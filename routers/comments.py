from fastapi import APIRouter, HTTPException, status
from models import Comment, CommentCreate
from crud import create_comment_db, delete_comment_db


# Prefixing with /posts so it handles /posts/{post_id}/comments nicely
router = APIRouter(prefix="/posts", tags=["Comments"])

@router.post("/{post_id}/comments", response_model=Comment, status_code=201)
def create_comment(post_id: int, comment: CommentCreate):
    return create_comment_db(post_id, comment)

@router.delete("/{post_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(post_id: int, comment_id: int):
    delete_comment_db(post_id, comment_id)
    return None