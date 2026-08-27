from sqlalchemy import Column, Integer, String, DateTime, func
from .database import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    username = Column(String(64), unique=True, nullable=False, index=True, comment="用户名")
    email = Column(String(128), unique=True, nullable=False, index=True, comment="邮箱")
    password = Column(String(255), nullable=False, comment="密码")
    nickname = Column(String(50), nullable=True, comment="昵称")
    age = Column(Integer, nullable=True, comment="年龄")
    gender = Column(String(10), nullable=True, comment="性别")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
