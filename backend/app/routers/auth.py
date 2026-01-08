# app/routers/auth.py
from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, DataError
from datetime import datetime

from app.auth.hash import hash_password, verify_password
from app.auth.jwt_handler import create_access_token, create_refresh_token, decode_access_token
from app.models.user import User
from app.models.institution import Institution
from app.schemas.user import UserCreate, UserRead
from app.dependencies import get_db

router = APIRouter()


@router.post("/register", response_model=UserRead)
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        # 1. Lookup institution by name
        institution = db.query(Institution).filter(
            Institution.name == user.institution_name
        ).first()
        if not institution:
            raise HTTPException(
                status_code=404,
                detail=f"Institution '{user.institution_name}' not found"
            )

        # 2. Check if username already exists
        existing_user = db.query(User).filter(User.username == user.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")

        # 3. Check if email already exists
        existing_email = db.query(User).filter(User.email == user.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")

        # 4. Create user object with all new fields
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hash_password(user.password),
            institution_id=institution.institution_id,
            role=user.role.value,
            status="ACTIVE",
        )
        db.add(db_user)

        # 5. Commit to database
        db.commit()
        db.refresh(db_user)
        return db_user

    except HTTPException:
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Username or email already exists (db constraint)"
        )
    except DataError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid data format (possibly too long fields)"
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error. Please try again later."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected server error: {str(e)}")


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Update last_login timestamp
    user.last_login = datetime.now()
    db.commit()

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "uuid": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "institution_id": str(user.institution_id),
    }


@router.post("/refresh")
def refresh_token(refresh_token: str = Body(...), db: Session = Depends(get_db)):
    payload = decode_access_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Validate user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_access_token = create_access_token({"sub": user_id})
    return {"access_token": new_access_token}
