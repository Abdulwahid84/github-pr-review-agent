# 🚀 Automated GitHub Pull Request Review Agent

A Python-based backend system that uses AI to automatically review GitHub Pull Requests using a multi-agent architecture powered by Google Gemini.

## 🎯 Features

- **Multi-Agent Analysis System**:
  - Agent 1: Code Reviewer (logic bugs, code smells, readability)
  - Agent 2: Security Auditor (vulnerabilities, unsafe patterns)
  - Agent 3: Performance Analyst (inefficient code, optimization opportunities)
  - Agent 4: Senior Engineer (refines all feedback professionally)
  - Agent 5: Summary Agent (combines all outputs into structured JSON)

- **GitHub Integration**: Fetches PR diffs, posts review comments
- **Google Gemini AI**: Free tier Flash model for code analysis
- **RESTful API**: FastAPI-based backend with async support
- **Structured Output**: JSON-formatted review results

---

## 📋 Prerequisites

- Python 3.9+
- GitHub account
- Google account (for Gemini API)

---

## 🔧 Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd pr-review-agent
```

### 2. Create virtual environment

```bash
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 API Keys Setup

### **Step 1: Generate GitHub Personal Access Token (PAT)**

1. Go to [GitHub Settings → Developer Settings → Personal Access Tokens → Tokens (classic)](https://github.com/settings/tokens)
2. Click **"Generate new token (classic)"**
3. Give it a descriptive name (e.g., "PR Review Agent")
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `read:org` (if reviewing org repos)
5. Click **"Generate token"**
6. **Copy the token immediately** (you won't see it again!)

### **Step 2: Generate Google Gemini API Key**

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click **"Create API Key"**
3. Select a Google Cloud project (or create new)
4. Copy the API key

### **Step 3: Create `.env` file**

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your keys:

```env
GITHUB_TOKEN=ghp_your_github_token_here
GEMINI_API_KEY=your_gemini_api_key_here
LOG_LEVEL=INFO
PORT=8000
```

---

## 🚀 Running the Server

### Start the FastAPI server:

```bash
uvicorn main:app --reload
```

Server will start at: **http://localhost:8000**

### Verify it's running:

```bash
curl http://localhost:8000/health
```

---

## 📡 API Usage

### **Endpoint**: `POST /api/review`

### Request Body:

```json
{
  "owner": "octocat",
  "repo": "Hello-World",
  "pr_number": 7,
  "post_comment": true
}
```

### Parameters:

- `owner` (string): Repository owner (username or org)
- `repo` (string): Repository name
- `pr_number` (integer): Pull request number
- `post_comment` (boolean): Whether to post results to GitHub (default: true)

### Example using cURL:

```bash
curl -X POST http://localhost:8000/api/review \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "octocat",
    "repo": "Hello-World",
    "pr_number": 7,
    "post_comment": true
  }'
```

### Example using Python:

```python
import requests

response = requests.post(
    "http://localhost:8000/api/review",
    json={
        "owner": "octocat",
        "repo": "Hello-World",
        "pr_number": 7,
        "post_comment": True
    }
)

print(response.json())
```

---

## 📊 Response Format

```json
{
  "status": "success",
  "message": "Successfully reviewed PR #7",
  "review": {
    "summary": "Code review complete. Found 3 issues requiring attention...",
    "files": [
      {
        "file": "src/app.py",
        "issues": [
          {
            "type": "security",
            "severity": "high",
            "message": "Potential SQL injection vulnerability detected",
            "suggestion": "Use parameterized queries instead of string concatenation"
          }
        ]
      }
    ],
    "total_files_analyzed": 5,
    "total_issues_found": 3,
    "issues_by_severity": {
      "high": 1,
      "medium": 2,
      "low": 0
    },
    "issues_by_type": {
      "security": 1,
      "performance": 1,
      "code_quality": 1
    }
  },
  "comment_posted": true
}
```

---

## 📁 Project Structure

```
/app
  /routes
    review_routes.py          # API routes
  /controllers
    review_controller.py      # Main orchestrator
  /services
    github_service.py         # GitHub API integration
    gemini_service.py         # Gemini AI integration
  /agents
    reviewer_agent.py         # Agent 1: Code Reviewer
    security_agent.py         # Agent 2: Security Auditor
    performance_agent.py      # Agent 3: Performance Analyst
    senior_engineer_agent.py  # Agent 4: Senior Engineer
    summary_agent.py          # Agent 5: Summary Agent
  /utils
    diff_parser.py           # Parse GitHub diffs
    logger.py                # Logging utilities
  /config
    github_client.py         # GitHub configuration
    gemini_client.py         # Gemini configuration
main.py                      # FastAPI entry point
requirements.txt             # Python dependencies
README.md                    # This file
.env.example                 # Environment variables template
```

---

## 🔍 How It Works

1. **Fetch PR Data**: Retrieves PR metadata and unified diff from GitHub
2. **Parse Diff**: Extracts changed files and line-by-line modifications
3. **Multi-Agent Analysis**:
   - Code Reviewer checks for bugs and code quality
   - Security Auditor looks for vulnerabilities
   - Performance Analyst finds optimization opportunities
   - Senior Engineer refines all feedback
   - Summary Agent combines everything into structured JSON
4. **Post Results**: Comments review findings on GitHub PR

---

## 🧪 Testing

### Test with a real PR:

1. Create a test PR in your repository
2. Note the owner, repo, and PR number
3. Send request:

```bash
curl -X POST http://localhost:8000/api/review \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "YOUR_USERNAME",
    "repo": "YOUR_REPO",
    "pr_number": 1,
    "post_comment": true
  }'
```

### Check the PR on GitHub to see the automated review comment!

---

## 🔧 Configuration

### Environment Variables:

- `GITHUB_TOKEN`: Your GitHub PAT (required)
- `GEMINI_API_KEY`: Your Gemini API key (required)
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)
- `PORT`: Server port (default: 8000)

### Customize Agent Behavior:

Edit prompts in `app/services/gemini_service.py`:
- `_get_review_prompt()`
- `_get_security_prompt()`
- `_get_performance_prompt()`

---

## 🐛 Troubleshooting

### **"GITHUB_TOKEN not found"**
- Ensure `.env` file exists in project root
- Check token is correctly formatted: `GITHUB_TOKEN=ghp_...`

### **"GEMINI_API_KEY not found"**
- Verify Gemini API key in `.env`
- Ensure you've enabled Gemini API in Google Cloud

### **"Failed to fetch PR"**
- Verify PR exists and number is correct
- Check GitHub token has `repo` scope
- For private repos, ensure token has access

### **Rate Limiting**
- GitHub: 5,000 requests/hour for authenticated users
- Gemini: Check your API quota at Google AI Studio

---

## 🚀 Advanced Usage

### Run without posting comments (dry-run):

```json
{
  "owner": "octocat",
  "repo": "Hello-World",
  "pr_number": 7,
  "post_comment": false
}
```

### Custom deployment:

```bash
# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# With Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## 📝 Example Workflow

### Sample PR Diff:

```diff
diff --git a/src/app.py b/src/app.py
index abc123..def456 100644
--- a/src/app.py
+++ b/src/app.py
@@ -10,7 +10,8 @@ def get_user(user_id):
-    query = "SELECT * FROM users WHERE id = " + user_id
+    # TODO: Fix SQL injection
+    query = f"SELECT * FROM users WHERE id = {user_id}"
     return db.execute(query)
```

### Agent Reasoning:

**Agent 1 (Code Reviewer):**
- Issue: String formatting still vulnerable

**Agent 2 (Security Auditor):**
- 🔴 HIGH: SQL injection vulnerability
- Using f-string doesn't prevent injection

**Agent 3 (Performance Analyst):**
- No immediate performance concerns

**Agent 4 (Senior Engineer):**
- Refined message: "This code is vulnerable to SQL injection attacks. Use parameterized queries."

**Agent 5 (Summary):**
- Combined into final JSON with severity levels and suggestions

### Final GitHub Comment:

```
🤖 Automated PR Review

Summary: Found 1 high-severity security issue requiring immediate attention.

Detailed Findings:

📄 src/app.py
🔴 SECURITY (Line 13)
- Potential SQL injection vulnerability detected
- 💡 Suggestion: Use parameterized queries: cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

---

## 🤝 Contributing

Pull requests welcome! Please ensure:
- Code follows PEP 8 style
- Add tests for new features
- Update README for new functionality

---

## 📄 License

MIT License - feel free to use in your projects!

---

## 🆘 Support

- Issues: [GitHub Issues](https://github.com/your-repo/issues)
- Docs: [API Documentation](http://localhost:8000/docs)

---

## 🎉 Ready to Go!

Your automated PR review agent is now ready to use. Start reviewing pull requests with AI-powered insights!

```bash
uvicorn main:app --reload
```

Visit: http://localhost:8000/docs for interactive API documentation.