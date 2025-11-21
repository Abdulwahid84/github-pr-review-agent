from app.utils.logger import setup_logger

logger = setup_logger()

class PerformanceAgent:
    """
    Agent 3: Performance Analyst
    Finds inefficient code and optimization opportunities
    """
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service
        self.agent_name = "Performance Analyst"
    
    async def analyze(self, parsed_files: list, pr_data: dict) -> list:
        """
        Analyze code for performance issues
        """
        logger.info(f"{self.agent_name}: Starting performance analysis...")
        
        results = []
        
        for file_data in parsed_files:
            file_name = file_data.get("file_name", "unknown")
            added_lines = file_data.get("added_lines", [])
            
            if not added_lines:
                continue
            
            # Combine added lines into code snippet
            code_snippet = "\n".join([line["content"] for line in added_lines])
            
            if not code_snippet.strip():
                continue
            
            logger.debug(f"{self.agent_name}: Analyzing {file_name}")
            
            try:
                # Analyze with Gemini
                analysis = await self.gemini.analyze_code(
                    code_snippet=code_snippet,
                    analysis_type="performance",
                    context={
                        "file_name": file_name,
                        "pr_title": pr_data.get("title", ""),
                        "pr_body": pr_data.get("body", "")
                    }
                )
                
                # Add file context to issues
                if "issues" in analysis and analysis["issues"]:
                    for issue in analysis["issues"]:
                        results.append({
                            "file": file_name,
                            "line": added_lines[0].get("line_number") if added_lines else None,
                            "agent": self.agent_name,
                            **issue
                        })
                        logger.debug(f"Performance issue: {issue.get('message', 'N/A')}")
            
            except Exception as e:
                logger.error(f"{self.agent_name}: Error analyzing {file_name}: {str(e)}")
                continue
        
        logger.info(f"{self.agent_name}: Found {len(results)} performance issues")
        return results