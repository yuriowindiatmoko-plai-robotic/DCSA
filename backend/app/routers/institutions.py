from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_db
from app.models.institution import Institution
from app.schemas.institution import InstitutionRead

router = APIRouter()

@router.get("/", response_model=List[InstitutionRead])
def get_institutions(db: Session = Depends(get_db)):
    return db.query(Institution).filter(Institution.status == "ACTIVE").all()
