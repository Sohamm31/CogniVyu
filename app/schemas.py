from pydantic import BaseModel
from typing import Optional

class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    domain: Optional[str] = None
class QueryResponse(BaseModel):
    domain: str
    answer: str
    conversation_id: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class MessageHistory(BaseModel):
    human_message: str
    bot_message: str
    domain: str

class Conversation(BaseModel):
    id: str
    title: str 

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
