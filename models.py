from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

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

class PostWithComments(Post):
    comments: List[Comment] = []