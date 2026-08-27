from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import User
from app.security import create_access_token, get_current_user, verify_password
from fastapi.security import OAuth2PasswordRequestForm

app = FastAPI(
    title="User CRUD API (MySQL 8.0 + Docker Compose)",
    description="把内存数据对接到 MySQL 数据库",
    version="2.0.0"
)

class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    email: str
    password: str
    nickname: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[str] = None

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=1, max_length=64)
    email: Optional[str] = None
    password: Optional[str] = None
    nickname: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    nickname: Optional[str]
    age: Optional[int]
    gender: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

@app.get("/")
def root():
    return {"message": "Welcome to User CRUD API (MySQL Version)"}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    
    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@app.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    from app.security import get_password_hash
    user_data = user.model_dump()
    user_data["password"] = get_password_hash(user_data["password"])  # 加密密码
    db_user = User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users", response_model=List[UserResponse])
def get_users(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    email: Optional[str] = None,
    gender: Optional[str] = None,
    age: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(User)

    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.nickname.contains(search)) |
            (User.email.contains(search))
        )

    if email:
        query = query.filter(User.email == email)

    if gender:
        query = query.filter(User.gender == gender)

    if age is not None:
        query = query.filter(User.age == age)

    return query.offset(skip).limit(limit).all()

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in user_update.model_dump(exclude_unset=True).items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return {"message": "User deleted successfully"}
