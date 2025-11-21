from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class SeverityLevel(str, Enum):
    """Severity levels for issues."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class CategoryType(str, Enum):
    """Category types for review comments."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    CODE_QUALITY = "code_quality"
    BEST_PRACTICES = "best_practices"
    STYLE = "style"

class ReviewComment(BaseModel):
    """Model for a single review comment."""
    file_path: str
    line_number: int
    severity: SeverityLevel
    category: CategoryType
    title: str
    comment: str
    suggested_fix: Optional[str] = None
    agent_name: str

class LineChange(BaseModel):
    """Model for a single line change."""
    content: str
    change_type: str  # 'add', 'remove', 'context'
    line_number: Optional[int] = None

class Hunk(BaseModel):
    """Model for a hunk in a diff."""
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[LineChange]

class FilePatch(BaseModel):
    """Model for a file patch."""
    filename: str
    status: str  # 'added', 'removed', 'modified', 'renamed'
    additions: int = 0
    deletions: int = 0
    hunks: List[Hunk]
    language: Optional[str] = None

class FileChange(BaseModel):
    """Model for file changes."""
    filename: str
    status: str
    additions: int
    deletions: int
    patch: str

class PRDiff(BaseModel):
    """Model for a PR diff."""
    pr_number: int
    base_sha: str
    head_sha: str
    files: List[FilePatch]
    total_additions: int
    total_deletions: int

class ReviewRequest(BaseModel):
    """Request model for PR review."""
    pr_url: str
    agents: Optional[List[str]] = None  # Which agents to use

class ReviewResponse(BaseModel):
    """Response model for PR review."""
    pr_number: int
    summary: str
    files_review: List[Dict[str, Any]]
    total_files_analyzed: int
    total_issues_found: int
    issues_by_severity: Dict[str, int]
    issues_by_type: Dict[str, int]
    metadata: Dict[str, Any]