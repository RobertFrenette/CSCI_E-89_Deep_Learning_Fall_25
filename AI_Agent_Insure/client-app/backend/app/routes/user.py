"""
User and policy routes
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.models import User, Policy, PolicyWithCoverage, QueryRequest, QueryResponse
from app.auth import get_current_user
from app.database import get_postgres_cursor, get_mongo_db
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/api/user", tags=["User"])


@router.get("/me", response_model=User)
async def get_current_user_profile(current_user = Depends(get_current_user)):
    """Get current user's profile"""
    db = get_mongo_db()
    
    user = await db.user_profiles.find_one({"username": current_user.username})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user["_id"] = str(user["_id"])
    return User(**user)


@router.get("/policies", response_model=List[Policy])
async def get_user_policies(current_user = Depends(get_current_user)):
    """
    Get all policies for the current user
    
    Looks up user's email in MongoDB, then queries Postgres for their policies
    """
    # Get user's email from MongoDB
    db = get_mongo_db()
    user = await db.user_profiles.find_one({"username": current_user.username})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Query Postgres for policies using email
    with get_postgres_cursor() as cursor:
        cursor.execute("""
            SELECT 
                p.policy_number,
                p.insured_id,
                p.policy_type,
                p.effective_date,
                p.expiration_date,
                p.annual_premium as premium_amount,
                p.policy_status as status
            FROM policies p
            JOIN insureds i ON p.insured_id = i.insured_id
            WHERE i.email_address = %s
            ORDER BY p.effective_date DESC
        """, (user["email"],))
        
        policies = cursor.fetchall()
    
    return [Policy(**dict(policy)) for policy in policies]


@router.get("/policies/{policy_number}", response_model=PolicyWithCoverage)
async def get_policy_details(policy_number: str, current_user = Depends(get_current_user)):
    """
    Get detailed information for a specific policy
    
    Includes coverage details
    """
    # Get user's email from MongoDB
    db = get_mongo_db()
    user = await db.user_profiles.find_one({"username": current_user.username})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Query Postgres for policy and coverage
    with get_postgres_cursor() as cursor:
        # Get policy
        cursor.execute("""
            SELECT 
                p.policy_number,
                p.insured_id,
                p.policy_type,
                p.effective_date,
                p.expiration_date,
                p.annual_premium as premium_amount,
                p.policy_status as status
            FROM policies p
            JOIN insureds i ON p.insured_id = i.insured_id
            WHERE p.policy_number = %s AND i.email_address = %s
        """, (policy_number, user["email"]))
        
        policy = cursor.fetchone()
        
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy not found or does not belong to user"
            )
        
        # Get coverage details
        cursor.execute("""
            SELECT 
                coverage_tier as coverage_type,
                coverage_limit,
                deductible,
                optional_addons_selected,
                regulatory_addons_selected,
                business_interruption_coverage,
                cyber_extension,
                incident_response_addon
            FROM coverage_details
            WHERE policy_number = %s
        """, (policy_number,))
        
        coverage = cursor.fetchall()
    
    policy_dict = dict(policy)
    policy_dict["coverage_details"] = [dict(c) for c in coverage] if coverage else []
    
    return PolicyWithCoverage(**policy_dict)


@router.get("/queries", response_model=List[QueryResponse])
async def get_user_queries(current_user = Depends(get_current_user), limit: int = 20):
    """
    Get user's query history
    """
    db = get_mongo_db()
    
    # Get user
    user = await db.user_profiles.find_one({"username": current_user.username})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get query history
    queries = await db.query_history.find(
        {"user_id": user["_id"]}
    ).sort("query_timestamp", -1).limit(limit).to_list(limit)
    
    # Convert ObjectIds to strings
    for query in queries:
        query["query_id"] = str(query["_id"])
        del query["_id"]
        del query["user_id"]
    
    return [QueryResponse(**q) for q in queries]
