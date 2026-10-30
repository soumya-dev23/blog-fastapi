from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

from database import init_db
from routers import posts, comments

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Blog Management API", version="1.0", lifespan=lifespan)

# Include the router from the routers folder
app.include_router(posts.router)
app.include_router(comments.router)

@app.get("/", include_in_schema=False)
def root():
    return {"message": "Blog Management API is running. Use /posts or /docs for the API."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)