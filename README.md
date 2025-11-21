# Automated GitHub Pull Request Review Agent

## Problem Statement
Build an automated Pull Request (PR) Review Agent that analyzes code changes in a GitHub PR and generates clear, structured, and actionable review comments.

---

## Features

- Reads PR diffs via GitHub API or manual input.
- Multi-agent analysis for:
  - Logic
  - Readability
  - Performance
  - Security
- Generates structured review comments like a human reviewer.
- Backend-focused; API-level testing supported (Postman, Insomnia, curl).

---

## Getting Started

### Prerequisites

- Python 3.9+
- GitHub account & Personal Access Token
- Google account (for Gemini API, if applicable)

### Installation

```bash
git clone https://github.com/Abdulwahid84/github-pr-review-agent.git
cd github-pr-review-agent
python -m venv venv
# Activate virtual environment
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt

