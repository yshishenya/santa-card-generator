"""Employee repository for data access operations."""

import json
import logging
from typing import List, Optional

import aiofiles

from src.config import settings
from src.models.employee import Employee

logger = logging.getLogger(__name__)


class EmployeeRepository:
    """Repository for employee data operations.

    Handles reading employee data from JSON file with async operations.
    """

    def __init__(self, file_path: Optional[str] = None) -> None:
        """Initialize repository with file path.

        Args:
            file_path: Path to employees JSON file. Uses settings default if not provided.
        """
        self.file_path = file_path or settings.employees_file_path
        logger.info(f"Initialized EmployeeRepository with file: {self.file_path}")

    async def get_all(self) -> List[Employee]:
        """Get all employees from the data file.

        Returns:
            List of all employees.

        Raises:
            FileNotFoundError: If employee data file doesn't exist.
            json.JSONDecodeError: If file contains invalid JSON.
            Exception: For other unexpected errors during file reading.
        """
        try:
            logger.debug(f"Reading employees from: {self.file_path}")

            async with aiofiles.open(self.file_path, mode="r", encoding="utf-8") as file:
                content = await file.read()
                data = json.loads(content)

            # Validate and parse employee data
            employees = [Employee(**employee_data) for employee_data in data]

            logger.info(f"Successfully loaded {len(employees)} employees")
            return employees

        except FileNotFoundError:
            logger.error(f"Employee data file not found: {self.file_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in employee data file: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error reading employee data: {e}")
            raise

    async def get_by_name(self, name: str) -> Optional[Employee]:
        """Get employee by exact name match.

        Args:
            name: Full name of the employee to search for.

        Returns:
            Employee if found, None otherwise.

        Raises:
            FileNotFoundError: If employee data file doesn't exist.
            json.JSONDecodeError: If file contains invalid JSON.
        """
        try:
            logger.debug(f"Searching for employee: {name}")

            employees = await self.get_all()

            # Case-insensitive search
            name_lower = name.lower().strip()
            for employee in employees:
                if employee.name.lower().strip() == name_lower:
                    logger.info(f"Found employee: {employee.name} (id: {employee.id})")
                    return employee

            logger.info(f"Employee not found: {name}")
            return None

        except Exception as e:
            logger.error(f"Error searching for employee {name}: {e}")
            raise
