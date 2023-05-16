from typing import Optional

from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    email: str
    full_name: str = None
    photo: Optional[bytes] = None

    class Config:
        orm_mode = True

class User(UserBase):
    id: int

    class Config:
        orm_mode = True

class BookBase(BaseModel):
    title: str
    description: str
    content: str
    photo: Optional[bytes] = None

    class Config:
        orm_mode = True

class Book(BookBase):
    id: int

    class Config:
        orm_mode = True

