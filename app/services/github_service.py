import httpx
from typing import Optional, Dict, Any, Tuple
from app.config import settings
from app.models import PRDiff, FileChange
from app.utils.diff_parser import DiffParser

class GitHubService:
    """Enhanced service for interacting with GitHub API."""
    
    def __init__(self):
        self.token = settings.github_token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    def get_pull_request(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """Fetch PR details."""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        
        response = httpx.get(url, headers=self.headers, timeout=settings.api_timeout)
        response.raise_for_status()
        
        pr_data = response.json()
        
        return {
            "number": pr_number,
            "title": pr_data.get("title", ""),
            "body": pr_data.get("body", ""),
            "author": pr_data.get("user", {}).get("login", "unknown"),
            "state": pr_data.get("state", ""),
            "created_at": pr_data.get("created_at", ""),
            "updated_at": pr_data.get("updated_at", ""),
            "additions": pr_data.get("additions", 0),
            "deletions": pr_data.get("deletions", 0),
            "changed_files": pr_data.get("changed_files", 0),
            "commits": pr_data.get("commits", 0),
            "base_ref": pr_data.get("base", {}).get("ref", ""),
            "head_ref": pr_data.get("head", {}).get("ref", ""),
            "base_sha": pr_data.get("base", {}).get("sha", ""),
            "head_sha": pr_data.get("head", {}).get("sha", ""),
        }
    
    def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """Fetch the unified diff for a PR."""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        
        headers = {**self.headers, "Accept": "application/vnd.github.v3.diff"}
        response = httpx.get(url, headers=headers, timeout=settings.api_timeout)
        response.raise_for_status()
        
        return response.text
    
    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> list:
        """Fetch list of files changed in a PR."""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        
        response = httpx.get(url, headers=self.headers, timeout=settings.api_timeout)
        response.raise_for_status()
        
        return response.json()
    
    async def fetch_pr_with_metadata(
        self, 
        owner: str, 
        repo: str, 
        pr_number: int
    ) -> Tuple[PRDiff, Dict[str, Any]]:
        """
        Fetch PR diff AND metadata for enhanced summary generation.
        
        Returns:
            Tuple of (PRDiff, metadata_dict)
        """
        async with httpx.AsyncClient(timeout=settings.api_timeout) as client:
            # Get PR details
            pr_url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
            pr_response = await client.get(pr_url, headers=self.headers)
            pr_response.raise_for_status()
            pr_data = pr_response.json()
            
            # Extract metadata
            metadata = {
                "number": pr_number,
                "title": pr_data.get("title", ""),
                "body": pr_data.get("body", ""),
                "author": pr_data.get("user", {}).get("login", "unknown"),
                "state": pr_data.get("state", ""),
                "created_at": pr_data.get("created_at", ""),
                "updated_at": pr_data.get("updated_at", ""),
                "additions": pr_data.get("additions", 0),
                "deletions": pr_data.get("deletions", 0),
                "changed_files": pr_data.get("changed_files", 0),
                "commits": pr_data.get("commits", 0),
                "base_ref": pr_data.get("base", {}).get("ref", ""),
                "head_ref": pr_data.get("head", {}).get("ref", ""),
            }
            
            # Get diff
            diff_headers = {**self.headers, "Accept": "application/vnd.github.v3.diff"}
            diff_response = await client.get(pr_url, headers=diff_headers)
            diff_response.raise_for_status()
            diff_text = diff_response.text
            
            # Parse diff
            files = DiffParser.parse_unified_diff(diff_text)
            
            pr_diff = PRDiff(
                pr_number=pr_number,
                base_sha=pr_data['base']['sha'],
                head_sha=pr_data['head']['sha'],
                files=files,
                total_additions=pr_data.get('additions', 0),
                total_deletions=pr_data.get('deletions', 0)
            )
            
            return pr_diff, metadata
    
    async def fetch_pr_files_content(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        sha: str
    ) -> Dict[str, str]:
        """
        Fetch full file contents for each changed file.
        Works with both classic and fine-grained tokens.
        
        Required Token Permissions:
        - Classic: 'repo' scope
        - Fine-grained: 'Contents' repository permission (read)
        
        Returns:
            Dict mapping filename to file content
        """
        async with httpx.AsyncClient(timeout=settings.api_timeout) as client:
            # Get list of files in PR
            pr_url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
            response = await client.get(pr_url, headers=self.headers)
            response.raise_for_status()
            files_data = response.json()
            
            file_contents = {}
            
            for file_info in files_data:
                filename = file_info.get("filename")
                
                # Skip deleted files
                if file_info.get("status") == "removed":
                    continue
                
                # Try to fetch file content
                try:
                    content_url = f"{self.base_url}/repos/{owner}/{repo}/contents/{filename}?ref={sha}"
                    content_response = await client.get(content_url, headers=self.headers)
                    
                    if content_response.status_code == 200:
                        content_data = content_response.json()
                        
                        # Decode base64 content
                        import base64
                        if content_data.get("encoding") == "base64":
                            content = base64.b64decode(content_data["content"]).decode('utf-8', errors='ignore')
                            file_contents[filename] = content
                        
                except Exception as e:
                    print(f"Could not fetch content for {filename}: {e}")
                    continue
            
            return file_contents
    
    async def post_review_comments(
        self, 
        owner: str, 
        repo: str, 
        pr_number: int,
        comments: list,
        summary: str
    ) -> Dict[str, Any]:
        """Post review comments back to GitHub PR."""
        async with httpx.AsyncClient(timeout=settings.api_timeout) as client:
            review_url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
            
            # Format comments for GitHub API
            github_comments = []
            for comment in comments:
                github_comments.append({
                    "path": comment.file_path,
                    "line": comment.line_number,
                    "body": f"**[{comment.severity.upper()} - {comment.category.upper()}]** {comment.title}\n\n{comment.comment}"
                })
            
            review_data = {
                "body": summary,
                "event": "COMMENT",
                "comments": github_comments[:50]  # GitHub limit
            }
            
            response = await client.post(
                review_url,
                headers=self.headers,
                json=review_data
            )
            response.raise_for_status()
            return response.json()
    
    def post_review_comment(self, owner: str, repo: str, pr_number: int, comment_body: str) -> Dict[str, Any]:
        """Post a comment on the PR."""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        
        data = {"body": comment_body}
        
        response = httpx.post(url, headers=self.headers, json=data, timeout=settings.api_timeout)
        response.raise_for_status()
        
        return response.json()
    
    @staticmethod
    def parse_pr_url(pr_url: str) -> Tuple[str, str, int]:
        """Parse GitHub PR URL into owner, repo, pr_number."""
        import re
        match = re.match(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
        if not match:
            raise ValueError("Invalid GitHub PR URL")
        return match.group(1), match.group(2), int(match.group(3))
    
    def validate_token_permissions(self) -> Dict[str, Any]:
        """
        Check if the token has required permissions.
        Works with both classic and fine-grained tokens.
        """
        # Test token by fetching user info
        response = httpx.get(
            f"{self.base_url}/user",
            headers=self.headers,
            timeout=10
        )
        
        if response.status_code != 200:
            return {
                "valid": False,
                "error": "Token is invalid or expired"
            }
        
        # Check scopes from response headers
        scopes = response.headers.get("X-OAuth-Scopes", "")
        
        return {
            "valid": True,
            "token_type": "fine-grained" if not scopes else "classic",
            "scopes": scopes.split(", ") if scopes else [],
            "user": response.json().get("login")
        }
