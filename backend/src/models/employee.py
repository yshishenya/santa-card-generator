"""Employee-related Pydantic models."""

from typing import Optional
from pydantic import BaseModel, Field


class Employee(BaseModel):
    """Employee data model.

    Represents an employee in the system with basic information.
    """

    id: str = Field(..., description="Unique employee identifier")
    name: str = Field(..., description="Full name of the employee", min_length=1)
    department: Optional[str] = Field(None, description="Department name (optional)")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "id": "1",
                "name": "Иванов Иван Иванович",
                "department": "IT",
            }
        }
