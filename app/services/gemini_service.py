import google.generativeai as genai
import json
from app.config.gemini_client import GeminiConfig
from app.utils.logger import setup_logger

logger = setup_logger()

class GeminiService:
    def __init__(self):
        self.config = GeminiConfig()
        genai.configure(api_key=self.config.api_key)
        
        # Use Gemini Flash (free tier)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        logger.info("Gemini service initialized with Flash model")
    
    async def generate_response(self, prompt: str, system_instruction: str = None) -> str:
        """
        Generate a response from Gemini
        """
        try:
            # Configure generation
            generation_config = {
                "temperature": 0.3,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
            
            # Add system instruction if provided
            full_prompt = prompt
            if system_instruction:
                full_prompt = f"{system_instruction}\n\n{prompt}"
            
            logger.debug(f"Sending prompt to Gemini (length: {len(full_prompt)} chars)")
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            result = response.text
            logger.debug(f"Received response from Gemini (length: {len(result)} chars)")
            
            return result
        
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise ValueError(f"Failed to generate response: {str(e)}")
    
    async def generate_json_response(self, prompt: str, system_instruction: str = None) -> dict:
        """
        Generate a JSON response from Gemini
        """
        try:
            # Enforce JSON output in prompt
            json_prompt = f"{prompt}\n\nIMPORTANT: Return ONLY valid JSON, no markdown, no backticks, no preamble."
            
            response_text = await self.generate_response(json_prompt, system_instruction)
            
            # Clean response (remove markdown code blocks if present)
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            # Parse JSON
            try:
                result = json.loads(cleaned)
                logger.debug("Successfully parsed JSON response")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {e}")
                logger.error(f"Raw response: {cleaned[:500]}...")
                # Return empty structure on parse failure
                return {"files": [], "error": "Failed to parse AI response"}
        
        except Exception as e:
            logger.error(f"Error generating JSON response: {str(e)}")
            raise
    
    async def analyze_code(self, code_snippet: str, analysis_type: str, context: dict = None) -> dict:
        """
        Analyze code snippet for specific issues
        
        Args:
            code_snippet: Code to analyze
            analysis_type: Type of analysis (review, security, performance)
            context: Additional context (file name, PR info, etc.)
        """
        prompts = {
            "review": self._get_review_prompt(code_snippet, context),
            "security": self._get_security_prompt(code_snippet, context),
            "performance": self._get_performance_prompt(code_snippet, context)
        }
        
        prompt = prompts.get(analysis_type, prompts["review"])
        
        return await self.generate_json_response(prompt)
    
    def _get_review_prompt(self, code: str, context: dict) -> str:
        file_name = context.get("file_name", "unknown") if context else "unknown"
        
        return f"""You are an expert code reviewer. Analyze this code for:
- Logic bugs and errors
- Code smells and bad practices
- Readability issues
- Potential runtime errors
- Best practice violations

File: {file_name}

Code:
{code}

Return JSON in this EXACT format:
{{
  "issues": [
    {{
      "type": "code_quality",
      "severity": "high|medium|low",
      "message": "Clear description of the issue",
      "suggestion": "How to fix it"
    }}
  ]
}}"""
    
    def _get_security_prompt(self, code: str, context: dict) -> str:
        file_name = context.get("file_name", "unknown") if context else "unknown"
        
        return f"""You are a security auditor. Analyze this code for:
- SQL injection vulnerabilities
- XSS vulnerabilities
- Authentication/authorization issues
- Insecure data handling
- Exposed secrets or credentials
- Unsafe API calls
- Path traversal vulnerabilities

File: {file_name}

Code:
{code}

Return JSON in this EXACT format:
{{
  "issues": [
    {{
      "type": "security",
      "severity": "high|medium|low",
      "message": "Clear description of security issue",
      "suggestion": "How to fix it securely"
    }}
  ]
}}"""
    
    def _get_performance_prompt(self, code: str, context: dict) -> str:
        file_name = context.get("file_name", "unknown") if context else "unknown"
        
        return f"""You are a performance analyst. Analyze this code for:
- Inefficient algorithms (O(n²) or worse)
- Unnecessary loops or iterations
- Memory leaks or excessive memory usage
- Blocking operations that should be async
- Database N+1 queries
- Missing caching opportunities
- Resource-intensive operations

File: {file_name}

Code:
{code}

Return JSON in this EXACT format:
{{
  "issues": [
    {{
      "type": "performance",
      "severity": "high|medium|low",
      "message": "Clear description of performance issue",
      "suggestion": "How to optimize it"
    }}
  ]
}}"""