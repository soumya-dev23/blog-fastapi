# FastAPI Backend Application

A robust, high-performance RESTful API built with **FastAPI** designed for seamless data processing and scalable backend services.

---

## 🚀 Technologies Used

* **Python 3.14** - Core programming language
* **FastAPI** - Modern, high-performance web framework for building APIs
* **Uvicorn** - Lightning-fast ASGI server implementation
* **SQLite / PostgreSQL** - Relational database backend (adjustable via ORM)
* **Pydantic** - Data validation and settings management using Python type annotations
* **Git & GitHub** - Version control and code repository management

---

## 🎯 Project Purpose

This project serves as a structured backend service designed to handle core API routing, data validation, serialization, and database interactions efficiently. It provides asynchronous request handling, auto-generated interactive API documentation (Swagger/ReDoc), and clean architectural layering for maintainability.

---

## 🗄️ Database & Table Creation SQL

Below is the foundational SQL schema used to set up the primary database tables for this project. 

### 1. Posts Table
Manages core entity records (e.g., blog posts, items, or primary entries).

```sql
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS comments (
    id SERIAL PRIMARY KEY,
    post_id INT REFERENCES posts(id) ON DELETE CASCADE,
    author_name VARCHAR(100) NOT NULL,
    comment_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

#Clone the Repository

git clone [https://github.com/soumya-dev23/](https://github.com/soumya-dev23/)<repository-name>.git
cd <repository-name>

#####  Create & Activate Virtual Environment
#### Windows (PowerShell):

python -m venv venv
venv\Scripts\Activate

########### macOS / Linux:
python3 -m venv venv
source venv/bin/activate

#########Run the Application
###########Start the development server using Uvicorn:

uvicorn main:app --reload

##################### API Documentation
Once the server is running, you can access the interactive documentation directly in your browser:

Swagger UI: http://127.0.0.1:8000/docs

ReDoc UI: http://127.0.0.1:8000/redoc

############Author
Soumyadip Bhattacharya
GitHub: @soumya-dev23