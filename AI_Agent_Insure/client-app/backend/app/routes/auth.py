"""
Authentication routes
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from app.models import UserRegister, UserLogin, Token, User
from app.auth import get_password_hash, verify_password, create_access_token
from app.database import get_postgres_cursor, get_mongo_db
from app.config import get_settings
from bson import ObjectId

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
settings = get_settings()


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    Register a new user
    
    Validates email and policy number against Postgres database,
    then creates user profile in MongoDB
    """
    # Step 1: Validate email and policy number in Postgres
    with get_postgres_cursor() as cursor:
        cursor.execute("""
            SELECT i.insured_id, i.email_address, p.policy_number
            FROM insureds i
            JOIN policies p ON i.insured_id = p.insured_id
            WHERE i.email_address = %s AND p.policy_number = %s
            LIMIT 1
        """, (user_data.email, user_data.policy_number))
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and policy number do not match our records"
            )
    
    # Step 2: Check if user already exists in MongoDB
    db = get_mongo_db()
    existing_user = await db.user_profiles.find_one({
        "$or": [
            {"username": user_data.username},
            {"email": user_data.email}
        ]
    })
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Step 3: Create user in MongoDB
    hashed_password = get_password_hash(user_data.password)
    now = datetime.utcnow()
    insured_id = result['insured_id']  # Get insured_id from Postgres validation
    policy_number = result['policy_number']  # Get policy_number from Postgres validation
    
    # MongoDB schema requires last_login to be a date, not null
    # We'll set it to a far past date to indicate "never logged in"
    user_doc = {
        "username": user_data.username,
        "email": user_data.email,
        "password": hashed_password,
        "insured_id": insured_id,  # Store insured_id for broader account queries
        "policy_number": policy_number,  # Store policy_number for direct policy queries
        "created_at": now,
        "updated_at": now,
        # Set to a far past date to indicate "never logged in" (schema requires date type)
        "last_login": datetime(1970, 1, 1)
    }
    
    result = await db.user_profiles.insert_one(user_doc)
    user_doc["_id"] = str(result.inserted_id)
    
    # Return user without password
    return User(**user_doc)


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login user and return JWT token
    """
    db = get_mongo_db()
    
    # Find user by username
    user = await db.user_profiles.find_one({"username": form_data.username})
    
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last_login
    await db.user_profiles.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.utcnow(), "updated_at": datetime.utcnow()}}
    )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
