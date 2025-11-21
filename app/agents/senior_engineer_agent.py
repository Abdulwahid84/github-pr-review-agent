from app.utils.logger import setup_logger
import json

logger = setup_logger()

class SeniorEngineerAgent:
    """
    Agent 4: Senior Engineer
    Refines all feedback into professional, actionable comments
    """
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service
        self.agent_name = "Senior Engineer"
    
    async def refine(self, agent_results: dict) -> list:
        """
        Refine all agent outputs into polished feedback
        """
        logger.info(f"{self.agent_name}: Refining feedback...")
        
        # Combine all issues from all agents
        all_issues = []
        
        for agent_type, issues in agent_results.items():
            if agent_type != "engineering_feedback":  # Skip self
                all_issues.extend(issues)
        
        if not all_issues:
            logger.info(f"{self.agent_name}: No issues to refine")
            return []
        
        # Group issues by file
        issues_by_file = {}
        for issue in all_issues:
            file_name = issue.get("file", "unknown")
            if file_name not in issues_by_file:
                issues_by_file[file_name] = []
            issues_by_file[file_name].append(issue)
        
        refined_results = []
        
        # Refine each file's issues
        for file_name, file_issues in issues_by_file.items():
            try:
                logger.debug(f"{self.agent_name}: Refining {len(file_issues)} issues for {file_name}")
                
                # Create prompt for refinement
                issues_json = json.dumps(file_issues, indent=2)
                
                prompt = f"""You are a senior software engineer reviewing code feedback from multiple automated agents.

Your task is to refine these findings into clear, professional, actionable comments that would be helpful to a developer.

File: {file_name}

Raw findings from agents:
{issues_json}

Instructions:
1. Combine duplicate or similar issues
2. Prioritize the most critical issues
3. Rewrite messages in a professional, helpful tone
4. Ensure suggestions are specific and actionable
5. Remove any false positives or low-value findings

Return JSON in this EXACT format:
{{
  "refined_issues": [
    {{
      "type": "security|performance|code_quality",
      "severity": "high|medium|low",
      "message": "Clear, professional description",
      "suggestion": "Specific, actionable suggestion"
    }}
  ]
}}"""

                refined = await self.gemini.generate_json_response(prompt)
                
                if "refined_issues" in refined:
                    for issue in refined["refined_issues"]:
                        refined_results.append({
                            "file": file_name,
                            "agent": self.agent_name,
                            **issue
                        })
            
            except Exception as e:
                logger.error(f"{self.agent_name}: Error refining {file_name}: {str(e)}")
                # Fall back to original issues if refinement fails
                refined_results.extend(file_issues)
        
        logger.info(f"{self.agent_name}: Refined to {len(refined_results)} actionable items")
        return refined_results