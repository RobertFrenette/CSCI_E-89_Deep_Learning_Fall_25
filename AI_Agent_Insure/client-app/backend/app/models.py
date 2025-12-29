"""
Pydantic models for API requests and responses
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# Authentication Models
class UserRegister(BaseModel):
    """User registration request"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    policy_number: str = Field(..., description="Policy number for validation")


class UserLogin(BaseModel):
    """User login request"""
    username: str
    password: str


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """JWT token payload"""
    username: Optional[str] = None


# User Models
class User(BaseModel):
    """User profile"""
    id: str = Field(..., alias="_id")
    username: str
    email: EmailStr
    insured_id: Optional[str] = None  # Insured ID for broader account queries
    policy_number: Optional[str] = None  # Policy number for direct policy queries
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class UserInDB(User):
    """User with hashed password (internal use)"""
    password: str


# Policy Models
class Policy(BaseModel):
    """Insurance policy"""
    policy_number: str
    insured_id: str
    policy_type: str
    effective_date: datetime
    expiration_date: datetime
    premium_amount: float
    status: str


class PolicyWithCoverage(Policy):
    """Policy with coverage details"""
    coverage_details: Optional[List[dict]] = None


# Query Models
class QueryRequest(BaseModel):
    """AI query request"""
    query_text: str = Field(..., min_length=1, max_length=1000)
    query_type: Optional[str] = Field(None, pattern="^(policy_info|claims|coverage|general)$")


class QueryResponse(BaseModel):
    """AI query response"""
    query_id: str
    query_text: str
    rag_response: str
    sources_used: List[str]
    query_timestamp: datetime
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
