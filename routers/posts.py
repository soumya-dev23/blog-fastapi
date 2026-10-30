from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from models import Post, PostCreate, PostUpdate, PostWithComments, Comment, CommentCreate
from crud import get_posts_db, create_post_db, get_post_with_comments_db
from database import get_db_connection
from crud import serialize_comment


router = APIRouter(prefix="/posts", tags=["Posts"])

@router.get("", response_model=List[Post])
def list_posts(
    author: Optional[str] = Query(None, description="Filter posts by author."),
    tag: Optional[str] = Query(None, description="Filter posts by tag."),
    search: Optional[str] = Query(None, description="Search in title or content."),
):
    return get_posts_db(author=author, tag=tag, search=search)

@router.post("", response_model=Post, status_code=201)
def create_post(post: PostCreate):
    return create_post_db(post)

@router.get("/{post_id}", response_model=PostWithComments)
def get_post(post_id: int):
    return get_post_with_comments_db(post_id)

@router.post("/{post_id}/comments", response_model=Comment, status_code=201)
def create_comment(post_id: int, comment: CommentCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Post not found")

    now = datetime.utcnow().isoformat() if 'datetime' in globals() else __import__('datetime').datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO comments (post_id, author, content, created_at) VALUES (%s, %s, %s, %s) RETURNING *",
        (post_id, comment.author, comment.content, now),
    )
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return serialize_comment(row)