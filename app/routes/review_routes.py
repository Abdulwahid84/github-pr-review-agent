from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.controllers.review_controller import ReviewController
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger()
controller = ReviewController()

class ReviewRequest(BaseModel):
    owner: str
    repo: str
    pr_number: int
    post_comment: bool = True

class ReviewResponse(BaseModel):
    status: str
    message: str
    review: dict
    comment_posted: bool

@router.post("/review", response_model=ReviewResponse)
async def review_pull_request(request: ReviewRequest):
    """
    Analyze a GitHub Pull Request and post review comments
    
    Args:
        owner: GitHub repository owner
        repo: Repository name
        pr_number: Pull request number
        post_comment: Whether to post the review to GitHub (default: True)
    
    Returns:
        ReviewResponse with analysis results
    """
    try:
        logger.info(f"Received review request for {request.owner}/{request.repo} PR #{request.pr_number}")
        
        result = await controller.review_pull_request(
            owner=request.owner,
            repo=request.repo,
            pr_number=request.pr_number,
            post_comment=request.post_comment
        )
        
        return ReviewResponse(
            status="success",
            message=f"Successfully reviewed PR #{request.pr_number}",
            review=result["review"],
            comment_posted=result["comment_posted"]
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error processing review: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")