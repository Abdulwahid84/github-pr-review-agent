import google.generativeai as genai
from typing import List, Dict, Any
from ..config import settings
from ..models import ReviewComment, FilePatch

class SummaryAgent:
    """
    Enhanced agent that generates comprehensive PR review summaries 
    with detailed file-level analysis.
    """
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def generate_summary(
        self, 
        comments: List[ReviewComment],
        files: List[FilePatch],
        pr_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive summary with file-level reviews.
        
        Args:
            comments: List of review comments from all agents
            files: List of file patches that were analyzed
            pr_metadata: Metadata about the PR (title, description, author, etc.)
        
        Returns:
            Dict with summary and detailed file reviews
        """
        
        # Organize comments by file and severity
        comments_by_file = self._organize_comments_by_file(comments)
        issues_by_severity = self._count_by_severity(comments)
        issues_by_type = self._count_by_type(comments)
        
        # Generate file-level reviews
        files_review = await self._generate_file_reviews(
            files, 
            comments_by_file,
            pr_metadata
        )
        
        # Generate overall summary
        overall_summary = await self._generate_overall_summary(
            comments,
            files,
            issues_by_severity,
            issues_by_type,
            pr_metadata
        )
        
        return {
            "summary": overall_summary,
            "files_review": files_review,
            "total_files_analyzed": len(files),
            "total_issues_found": len(comments),
            "issues_by_severity": issues_by_severity,
            "issues_by_type": issues_by_type,
            "metadata": {
                "pr_number": pr_metadata.get("number"),
                "pr_title": pr_metadata.get("title", ""),
                "pr_author": pr_metadata.get("author", ""),
                "files_changed": len(files),
                "additions": pr_metadata.get("additions", 0),
                "deletions": pr_metadata.get("deletions", 0)
            }
        }
    
    def _organize_comments_by_file(self, comments: List[ReviewComment]) -> Dict[str, List[ReviewComment]]:
        """Group comments by file path."""
        organized = {}
        for comment in comments:
            if comment.file_path not in organized:
                organized[comment.file_path] = []
            organized[comment.file_path].append(comment)
        return organized
    
    def _count_by_severity(self, comments: List[ReviewComment]) -> Dict[str, int]:
        """Count issues by severity level."""
        counts = {"high": 0, "medium": 0, "low": 0}
        for comment in comments:
            counts[comment.severity] = counts.get(comment.severity, 0) + 1
        return counts
    
    def _count_by_type(self, comments: List[ReviewComment]) -> Dict[str, int]:
        """Count issues by category type."""
        counts = {}
        for comment in comments:
            counts[comment.category] = counts.get(comment.category, 0) + 1
        return counts
    
    async def _generate_file_reviews(
        self,
        files: List[FilePatch],
        comments_by_file: Dict[str, List[ReviewComment]],
        pr_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate detailed review for each file."""
        file_reviews = []
        
        for file_patch in files:
            file_comments = comments_by_file.get(file_patch.filename, [])
            
            # Get file statistics
            additions = sum(1 for hunk in file_patch.hunks 
                          for line in hunk.lines if line.change_type == "add")
            deletions = sum(1 for hunk in file_patch.hunks 
                          for line in hunk.lines if line.change_type == "remove")
            
            # Extract code snippet for context
            code_snippet = self._extract_code_snippet(file_patch, max_lines=15)
            
            # Generate AI review for this file
            file_review = await self._generate_single_file_review(
                file_patch,
                file_comments,
                additions,
                deletions,
                code_snippet,
                pr_metadata
            )
            
            file_reviews.append({
                "filename": file_patch.filename,
                "status": file_patch.status,
                "language": file_patch.language or "unknown",
                "additions": additions,
                "deletions": deletions,
                "issues_count": len(file_comments),
                "review": file_review,
                "issues": [
                    {
                        "line": c.line_number,
                        "severity": c.severity,
                        "category": c.category,
                        "title": c.title,
                        "comment": c.comment,
                        "suggested_fix": c.suggested_fix
                    }
                    for c in file_comments
                ]
            })
        
        return file_reviews
    
    def _extract_code_snippet(self, file_patch: FilePatch, max_lines: int = 15) -> str:
        """Extract a representative code snippet from the file."""
        lines = []
        line_count = 0
        
        for hunk in file_patch.hunks[:3]:  # First 3 hunks only
            for line in hunk.lines:
                if line.change_type in ["add", "context"]:
                    prefix = "+" if line.change_type == "add" else " "
                    lines.append(f"{prefix} {line.content}")
                    line_count += 1
                    if line_count >= max_lines:
                        break
            if line_count >= max_lines:
                break
        
        return "\n".join(lines)
    
    async def _generate_single_file_review(
        self,
        file_patch: FilePatch,
        comments: List[ReviewComment],
        additions: int,
        deletions: int,
        code_snippet: str,
        pr_metadata: Dict[str, Any]
    ) -> str:
        """Generate AI-powered review for a single file."""
        
        # Build context about the file
        issues_summary = ", ".join([
            f"{c.severity} {c.category}" for c in comments[:5]
        ]) if comments else "No issues detected"
        
        prompt = f"""You are an expert code reviewer. Provide a concise, professional review of this file change.

**File:** {file_patch.filename}
**Language:** {file_patch.language or 'unknown'}
**Status:** {file_patch.status}
**Changes:** +{additions} -{deletions} lines

**PR Context:**
- Title: {pr_metadata.get('title', 'N/A')}
- Author: {pr_metadata.get('author', 'Unknown')}

**Detected Issues:** {issues_summary}

**Code Sample:**
```
{code_snippet[:500]}
```

Provide a 2-3 sentence review focusing on:
1. Overall quality of changes
2. Main concerns (if any)
3. Positive aspects or good practices

Keep it professional, specific, and actionable. Don't repeat the issues list."""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=300,
                    temperature=0.7
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"Error generating file review: {e}")
            # Fallback summary
            if comments:
                return f"Found {len(comments)} issues in this file. Review the specific comments for details."
            else:
                return "No significant issues detected. Changes look reasonable."
    
    async def _generate_overall_summary(
        self,
        comments: List[ReviewComment],
        files: List[FilePatch],
        issues_by_severity: Dict[str, int],
        issues_by_type: Dict[str, int],
        pr_metadata: Dict[str, Any]
    ) -> str:
        """Generate comprehensive overall PR summary."""
        
        total_additions = sum(
            sum(1 for hunk in f.hunks for line in hunk.lines if line.change_type == "add")
            for f in files
        )
        total_deletions = sum(
            sum(1 for hunk in f.hunks for line in hunk.lines if line.change_type == "remove")
            for f in files
        )
        
        # Build detailed context for AI
        prompt = f"""You are a senior software engineer conducting a comprehensive PR review. Generate a professional, detailed summary.

**PR Information:**
- Number: #{pr_metadata.get('number', 'N/A')}
- Title: {pr_metadata.get('title', 'Pull Request')}
- Author: @{pr_metadata.get('author', 'unknown')}
- Files Changed: {len(files)}
- Lines: +{total_additions} -{total_deletions}

**Files Modified:**
{chr(10).join([f"- {f.filename} ({f.status})" for f in files[:10]])}

**Issues Found:**
- Total: {len(comments)}
- High Severity: {issues_by_severity.get('high', 0)}
- Medium Severity: {issues_by_severity.get('medium', 0)}
- Low Severity: {issues_by_severity.get('low', 0)}

**Issue Categories:**
{chr(10).join([f"- {cat.title()}: {count}" for cat, count in issues_by_type.items()])}

**Sample Issues:**
{chr(10).join([f"- [{c.severity.upper()}] {c.title} in {c.file_path}:{c.line_number}" for c in comments[:5]])}

Generate a comprehensive review summary with:
1. **Overview**: Brief assessment of PR quality and scope
2. **Key Findings**: Most important issues discovered (2-4 points)
3. **Recommendations**: Actionable next steps (2-3 points)
4. **Positive Aspects**: What's done well (1-2 points if applicable)

Use a professional, constructive tone. Be specific and actionable. Use emojis sparingly (⚠️ for warnings, ✅ for good, 🔒 for security).

Format as markdown with clear sections."""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=1000,
                    temperature=0.7
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"Error generating summary: {e}")
            # Fallback summary
            return self._generate_fallback_summary(
                comments, files, issues_by_severity, pr_metadata
            )
    
    def _generate_fallback_summary(
        self,
        comments: List[ReviewComment],
        files: List[FilePatch],
        issues_by_severity: Dict[str, int],
        pr_metadata: Dict[str, Any]
    ) -> str:
        """Generate basic summary when AI fails."""
        status_emoji = "⚠️" if issues_by_severity.get('high', 0) > 0 else "✅"
        
        summary_parts = [
            f"{status_emoji} **Code Review Complete**",
            f"\n**PR #{pr_metadata.get('number')}**: {pr_metadata.get('title', 'N/A')}",
            f"\n**Analyzed**: {len(files)} files",
            f"\n**Issues Found**: {len(comments)} total"
        ]
        
        if issues_by_severity.get('high', 0) > 0:
            summary_parts.append(f"\n⚠️ **{issues_by_severity['high']} high-severity issues** require immediate attention")
        
        if len(comments) == 0:
            summary_parts.append("\n✅ No major issues detected. Code looks good!")
        else:
            summary_parts.append("\n\n**Top Issues:**")
            for i, comment in enumerate(comments[:3], 1):
                summary_parts.append(f"\n{i}. [{comment.severity.upper()}] {comment.title}")
        
        return "".join(summary_parts)

