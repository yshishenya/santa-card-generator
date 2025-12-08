"""Employees API router.

Handles employee-related endpoints.
"""

import logging
from typing import List
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from src.models.employee import Employee
from src.repositories.employee_repo import EmployeeRepository

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize repository
employee_repo = EmployeeRepository()


@router.get("/employees", response_model=List[Employee], status_code=status.HTTP_200_OK)
async def get_employees() -> List[Employee]:
    """Get list of all employees."""
    correlation_id = str(uuid4())
    try:
        logger.info(f"[{correlation_id}] GET /employees - Fetching all employees")
        employees = await employee_repo.get_all()
        logger.info(f"[{correlation_id}] Successfully fetched {len(employees)} employees")
        return employees
    except FileNotFoundError as e:
        logger.error(f"[{correlation_id}] Employee file not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Employee data file not found",
        )
    except Exception as e:
        logger.exception(f"[{correlation_id}] Error fetching employees: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch employees",
        )
