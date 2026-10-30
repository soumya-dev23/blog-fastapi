import json
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException
from database import get_db_connection
from models import Post, Comment, PostCreate, PostUpdate, PostWithComments

def serialize_post(row: dict) -> Post:
    tags_raw = row["tags"]
    tags = []
    if isinstance(tags_raw, list):
        tags = tags_raw
    elif isinstance(tags_raw, str) and tags_raw.strip():
        try:
            tags = json.loads(tags_raw)
        except json.JSONDecodeError:
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

    return Post(
        id=row["id"],
        title=row["title"],
        content=row["content"],
        author=row["author"],
        tags=tags,
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )

def serialize_comment(row: dict) -> Comment:
    return Comment(
        id=row["id"],
        post_id=row["post_id"],
        author=row["author"],
        content=row["content"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )

def get_posts_db(author: Optional[str] = None, tag: Optional[str] = None, search: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM posts"
    filters = []
    params = []

    if author:
        filters.append("author = %s")
        params.append(author)
    if tag:
        filters.append("tags LIKE %s")
        params.append(f'%"{tag}"%')
    if search:
        filters.append("(title LIKE %s OR content LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])

    if filters:
        query += " WHERE " + " AND ".join(filters)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [serialize_post(row) for row in rows]

def create_post_db(post: PostCreate):
    now = datetime.utcnow().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO posts (title, content, author, tags, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s) RETURNING *",
        (post.title, post.content, post.author, json.dumps(post.tags or []), now, now),
    )
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return serialize_post(row)

def get_post_with_comments_db(post_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Post not found")
        
    cursor.execute("SELECT * FROM comments WHERE post_id = %s ORDER BY created_at DESC", (post_id,))
    comment_rows = cursor.fetchall()
    conn.close()
    
    base_post = serialize_post(row)
    comments = [serialize_comment(c) for c in comment_rows]
    
    return PostWithComments(**base_post.dict(), comments=comments)

def create_comment_db(post_id: int, comment: CommentCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if the post exists
    cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Post not found")

    now = datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO comments (post_id, author, content, created_at) VALUES (%s, %s, %s, %s) RETURNING *",
        (post_id, comment.author, comment.content, now),
    )
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return serialize_comment(row)

def delete_comment_db(post_id: int, comment_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM comments WHERE id = %s AND post_id = %s", (comment_id, post_id))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Comment not found")
        
    conn.commit()
    conn.close()