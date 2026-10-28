from contextlib import asynccontextmanager
from datetime import datetime
import json
import os

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn
import psycopg2
import psycopg2.extras

# PostgreSQL connection string (can be overridden via environment variable)
# Update with your new password and database name:
DATABASE_URL = "postgresql://postgres:my_new_password@localhost:5432/fast-api"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Blog Management API", version="1.0", lifespan=lifespan)


@app.get("/", include_in_schema=False)
def root():
    return {"message": "Blog Management API is running. Use /posts or /docs for the API."}


class PostBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    content: str = Field(..., min_length=1)
    author: str = Field(..., min_length=3, max_length=100)
    tags: Optional[List[str]] = []


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    author: Optional[str] = Field(None, min_length=3, max_length=100)
    tags: Optional[List[str]] = None


class Post(PostBase):
    id: int
    created_at: datetime
    updated_at: datetime


class CommentCreate(BaseModel):
    author: str = Field(..., min_length=3, max_length=100)
    content: str = Field(..., min_length=1)


class Comment(BaseModel):
    id: int
    post_id: int
    author: str
    content: str
    created_at: datetime


def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn


def init_db() -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT NOT NULL,
            tags TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS comments (
            id SERIAL PRIMARY KEY,
            post_id INTEGER NOT NULL,
            author TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()
    conn.close()


def serialize_post(row: dict) -> Post:
    tags_raw = row["tags"]
    tags = []
    
    if isinstance(tags_raw, list):
        tags = tags_raw
    elif isinstance(tags_raw, str) and tags_raw.strip():
        try:
            tags = json.loads(tags_raw)
        except json.JSONDecodeError:
            # Fallback for comma-separated text stored directly in DB
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


def fetch_posts(author: Optional[str] = None, tag: Optional[str] = None, search: Optional[str] = None):
    """Helper function to query posts with optional filters."""
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


@app.get("/posts", response_model=List[Post])
def list_posts(
    author: Optional[str] = Query(None, description="Filter posts by author."),
    tag: Optional[str] = Query(None, description="Filter posts by tag."),
    search: Optional[str] = Query(None, description="Search in title or content."),
):
    return fetch_posts(author=author, tag=tag, search=search)


@app.get("/posts/all", response_model=List[Post])
def get_all_posts():
    """Alias for GET /posts to explicitly return all blog posts."""
    return fetch_posts()


@app.post("/posts/sample", response_model=Post, status_code=201)
def create_sample_post():
    """Create and return a sample blog post for testing."""
    sample = PostCreate(
        title="Sample post",
        content="This is a sample blog post created by the API.",
        author="API Tester",
        tags=["sample", "test"],
    )
    return create_post(sample)


@app.post("/posts/create", response_model=Post, status_code=201)
def create_post_with_body(post: PostCreate):
    """Create a new blog post from request body."""
    return create_post(post)


@app.post("/posts", response_model=Post, status_code=201)
def create_post(post: PostCreate):
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


@app.get("/posts/{post_id}", response_model=Post)
def get_post(post_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")
    return serialize_post(row)


@app.put("/posts/{post_id}", response_model=Post)
def update_post(post_id: int, update: PostUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Post not found")

    current = serialize_post(row)
    updated_data = current.dict()
    for field, value in update.dict(exclude_unset=True).items():
        updated_data[field] = value
    updated_data["tags"] = json.dumps(updated_data["tags"] or [])
    updated_data["updated_at"] = datetime.utcnow().isoformat()

    cursor.execute(
        "UPDATE posts SET title = %s, content = %s, author = %s, tags = %s, updated_at = %s WHERE id = %s RETURNING *",
        (
            updated_data["title"],
            updated_data["content"],
            updated_data["author"],
            updated_data["tags"],
            updated_data["updated_at"],
            post_id,
        ),
    )
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return serialize_post(row)


@app.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM posts WHERE id = %s", (post_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Post not found")
    conn.commit()
    conn.close()


@app.get("/posts/{post_id}/comments", response_model=List[Comment])
def list_comments(post_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Post not found")

    cursor.execute("SELECT * FROM comments WHERE post_id = %s ORDER BY created_at DESC", (post_id,))
    rows = cursor.fetchall()
    conn.close()
    return [serialize_comment(row) for row in rows]


@app.post("/posts/{post_id}/comments", response_model=Comment, status_code=201)
def create_comment(post_id: int, comment: CommentCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
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


@app.delete("/posts/{post_id}/comments/{comment_id}", status_code=204)
def delete_comment(post_id: int, comment_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM comments WHERE id = %s AND post_id = %s", (comment_id, post_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Comment not found")
    conn.commit()
    conn.close()


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)