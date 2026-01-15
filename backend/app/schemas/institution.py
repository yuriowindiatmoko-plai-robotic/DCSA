from pydantic import BaseModel
from uuid import UUID

class InstitutionRead(BaseModel):
    institution_id: UUID
    name: str

    class Config:
        orm_mode = True
