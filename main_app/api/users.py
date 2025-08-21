from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from database.config import get_db
from models import User

router = APIRouter()

class UserCreate(BaseModel):
    name: str
    display_name: str

class UserResponse(BaseModel):
    id: int
    name: str
    display_name: str
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[UserResponse])
async def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.name == user.name).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    db_user = User(name=user.name, display_name=user.display_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user