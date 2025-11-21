import asyncio
from app.services.github_service import GitHubService
from app.services.gemini_service import GeminiService
from app.agents.reviewer_agent import ReviewerAgent
from app.agents.security_agent import SecurityAgent
from app.agents.performance_agent import PerformanceAgent
from app.agents.senior_engineer_agent import SeniorEngineerAgent
from app.agents.summary_agent import SummaryAgent
from app.utils.logger import setup_logger
from app.utils.diff_parser import DiffParser

logger = setup_logger()

class ReviewController:
    def __init__(self):
        self.github_service = GitHubService()
        self.gemini_service = GeminiService()
        self.diff_parser = DiffParser()
        
        # Initialize all agents
        self.reviewer_agent = ReviewerAgent(self.gemini_service)
        self.security_agent = SecurityAgent(self.gemini_service)
        self.performance_agent = PerformanceAgent(self.gemini_service)
        self.senior_engineer_agent = SeniorEngineerAgent(self.gemini_service)
        self.summary_agent = SummaryAgent(self.gemini_service)
    
    async def review_pull_request(self, owner: str, repo: str, pr_number: int, post_comment: bool = True):
        """
        Main orchestrator for PR review process
        """
        logger.info(f"Starting review for {owner}/{repo} PR #{pr_number}")
        
        try:
            # Step 1: Fetch PR data from GitHub
            logger.info("Fetching PR data from GitHub...")
            pr_data = self.github_service.get_pull_request(owner, repo, pr_number)
            
            # Step 2: Get diff content
            logger.info("Fetching PR diff...")
            diff_content = self.github_service.get_pr_diff(owner, repo, pr_number)
            
            # Step 3: Parse diff to extract files and changes
            logger.info("Parsing diff content...")
            parsed_files = self.diff_parser.parse_unified_diff(diff_content)
            
            if not parsed_files:
                logger.warning("No files changed in PR")
                return {
                    "review": {"files": [], "summary": "No code changes detected"},
                    "comment_posted": False
                }
            
            # Step 4: Run all agents in parallel
            logger.info("Running multi-agent analysis...")
            agent_results = await self._run_all_agents(parsed_files, pr_data)
            
            # Step 5: Combine results using summary agent
            logger.info("Generating final review summary...")
            final_review = await self.summary_agent.generate_summary(
                agent_results.get("comments", []),
                parsed_files,
                pr_data
            )
            
            # Step 6: Post comment to GitHub if requested
            comment_posted = False
            if post_comment:
                logger.info("Posting review comment to GitHub...")
                try:
                    comment_body = self._format_review_comment(final_review)
                    self.github_service.post_review_comment(owner, repo, pr_number, comment_body)
                    comment_posted = True
                    logger.info("Review comment posted successfully")
                except Exception as e:
                    logger.error(f"Failed to post comment: {e}")
            
            return {
                "review": final_review,
                "comment_posted": comment_posted
            }
            
        except Exception as e:
            logger.error(f"Error in review process: {e}")
            raise
    
    async def _run_all_agents(self, parsed_files: list, pr_data: dict):
        """
        Run all analysis agents and collect results
        """
        results = {
            "code_review": [],
            "security": [],
            "performance": [],
            "engineering_feedback": [],
            "comments": []
        }
        
        try:
            # Run each agent (or mock if not fully implemented)
            logger.info("Agent 1: Code Review analysis...")
            results["code_review"] = await self._safe_agent_call(
                self.reviewer_agent, "analyze", parsed_files, pr_data
            )
            
            logger.info("Agent 2: Security audit...")
            results["security"] = await self._safe_agent_call(
                self.security_agent, "analyze", parsed_files, pr_data
            )
            
            logger.info("Agent 3: Performance analysis...")
            results["performance"] = await self._safe_agent_call(
                self.performance_agent, "analyze", parsed_files, pr_data
            )
            
            logger.info("Agent 4: Senior engineer review...")
            results["engineering_feedback"] = await self._safe_agent_call(
                self.senior_engineer_agent, "refine", results
            )
            
            # Combine all comments
            all_comments = []
            for key in ["code_review", "security", "performance"]:
                if isinstance(results[key], list):
                    all_comments.extend(results[key])
            
            results["comments"] = all_comments
            
        except Exception as e:
            logger.warning(f"Agent execution issue: {e}")
        
        return results
    
    async def _safe_agent_call(self, agent, method_name: str, *args, **kwargs):
        """Safely call agent methods with fallback."""
        try:
            method = getattr(agent, method_name, None)
            if method and callable(method):
                if asyncio.iscoroutinefunction(method):
                    return await method(*args, **kwargs)
                else:
                    return method(*args, **kwargs)
            return []
        except Exception as e:
            logger.warning(f"Agent method {method_name} failed: {e}")
            return []
    
    def _format_review_comment(self, review: dict) -> str:
        """
        Format the review JSON into a readable GitHub comment
        """
        comment = "## 🤖 Automated PR Review\n\n"
        
        if isinstance(review, dict):
            if "summary" in review:
                comment += f"### Summary\n{review['summary']}\n\n"
            
            if "files_review" in review and review["files_review"]:
                comment += "### Detailed Findings\n\n"
                
                for file_review in review["files_review"]:
                    comment += f"#### 📄 `{file_review.get('filename', 'Unknown')}`\n\n"
                    
                    if "issues" in file_review and file_review["issues"]:
                        for issue in file_review["issues"]:
                            severity_emoji = {
                                "high": "🔴",
                                "medium": "🟡",
                                "low": "🟢"
                            }.get(issue.get("severity", "low"), "⚪")
                            
                            comment += f"{severity_emoji} **{issue.get('category', 'ISSUE').upper()}** (Line {issue.get('line', 'N/A')})\n"
                            comment += f"- {issue.get('comment', 'No details')}\n"
                            if "suggested_fix" in issue and issue["suggested_fix"]:
                                comment += f"- 💡 *Suggestion:* {issue['suggested_fix']}\n"
                            comment += "\n"
            else:
                comment += "✅ No issues found!\n"
        else:
            comment += f"```\n{str(review)}\n```\n"
        
        comment += "\n---\n*Generated by AI-powered PR Review Agent*"
        
        return comment