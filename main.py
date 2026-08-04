from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import uuid4

app = FastAPI(
    title="User CRUD API",
    description="内存中的 User 增删改查接口",
    version="1.0.0"
)

# ========== 数据模型 ==========
class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱")
    age: Optional[int] = Field(None, ge=0, le=150, description="年龄")

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=150)

class User(BaseModel):
    id: str
    name: str
    email: str
    age: Optional[int] = None

# ========== 内存存储 ==========
# 用字典模拟数据库，key 为 user_id
users_db: dict[str, User] = {}

# ========== 接口 ==========

@app.get("/")
def root():
    return {"message": "Welcome to User CRUD API"}

# 创建用户 (Create)
@app.post("/users", response_model=User, status_code=201)
def create_user(user: UserCreate):
    user_id = str(uuid4())
    new_user = User(id=user_id, **user.model_dump())
    users_db[user_id] = new_user
    return new_user

# 获取所有用户 (Read - list)
@app.get("/users", response_model=List[User])
def get_users():
    return list(users_db.values())

# 获取单个用户 (Read - one)
@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: str):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

# 更新用户 (Update)
@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: str, user_update: UserUpdate):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing_user = users_db[user_id]
    update_data = user_update.model_dump(exclude_unset=True)  # 只更新传入的字段
    
    updated_user = existing_user.model_copy(update=update_data)
    users_db[user_id] = updated_user
    return updated_user

# 删除用户 (Delete)
@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: str):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    del users_db[user_id]
    return None  # 204 No Content
