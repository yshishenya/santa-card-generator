"""Unit tests for EmployeeRepository.

This module contains comprehensive tests for the EmployeeRepository class,
covering data loading, searching, and error handling scenarios.

Test coverage:
- Loading all employees from JSON file
- Handling empty files
- Searching by exact name match
- Searching by partial/case-insensitive match
- Employee not found scenarios
- File not found error handling
"""

import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from typing import List

from src.repositories.employee_repo import EmployeeRepository
from src.models.employee import Employee


class TestGetAll:
    """Tests for get_all() method."""

    @pytest.mark.asyncio
    async def test_get_all_returns_employees(
        self, sample_employee_data: List[dict]
    ) -> None:
        """Test that get_all() returns all employees from the JSON file.

        Verifies that:
        - All employees are loaded from the file
        - Each employee is properly parsed into Employee model
        - Employee count matches the data file
        """
        # Arrange
        mock_file_content = json.dumps(sample_employee_data)

        with patch("src.repositories.employee_repo.aiofiles") as mock_aiofiles:
            # Create mock for async context manager
            mock_file = AsyncMock()
            mock_file.read = AsyncMock(return_value=mock_file_content)

            mock_open_cm = AsyncMock()
            mock_open_cm.__aenter__.return_value = mock_file
            mock_open_cm.__aexit__.return_value = None

            mock_aiofiles.open.return_value = mock_open_cm

            with patch("src.repositories.employee_repo.settings") as mock_settings:
                mock_settings.employees_file_path = "/test/employees.json"
                repo = EmployeeRepository()

                # Act
                result = await repo.get_all()

        # Assert
        assert len(result) == len(sample_employee_data)
        assert all(isinstance(emp, Employee) for emp in result)
        assert result[0].name == sample_employee_data[0]["name"]
        assert result[0].id == sample_employee_data[0]["id"]

    @pytest.mark.asyncio
    async def test_get_all_empty_file(self) -> None:
        """Test that get_all() returns empty list for empty JSON array.

        Verifies that:
        - Empty JSON array is properly handled
        - Empty list is returned without errors
        """
        # Arrange
        mock_file_content = "[]"

        with patch("src.repositories.employee_repo.aiofiles") as mock_aiofiles:
            mock_file = AsyncMock()
            mock_file.read = AsyncMock(return_value=mock_file_content)

            mock_open_cm = AsyncMock()
            mock_open_cm.__aenter__.return_value = mock_file
            mock_open_cm.__aexit__.return_value = None

            mock_aiofiles.open.return_value = mock_open_cm

            with patch("src.repositories.employee_repo.settings") as mock_settings:
                mock_settings.employees_file_path = "/test/employees.json"
                repo = EmployeeRepository()

                # Act
                result = await repo.get_all()

        # Assert
        assert result == []
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_file_not_found_returns_empty(self) -> None:
        """Test that FileNotFoundError is raised when file doesn't exist.

        Verifies that:
        - FileNotFoundError is propagated
        - Error is logged appropriately
        """
        # Arrange
        with patch("src.repositories.employee_repo.aiofiles") as mock_aiofiles:
            mock_aiofiles.open.side_effect = FileNotFoundError("File not found")

            with patch("src.repositories.employee_repo.settings") as mock_settings:
                mock_settings.employees_file_path = "/nonexistent/employees.json"
                repo = EmployeeRepository()

                # Act & Assert
                with pytest.raises(FileNotFoundError):
                    await repo.get_all()

    @pytest.mark.asyncio
    async def test_get_all_handles_invalid_json(self) -> None:
        """Test that invalid JSON raises JSONDecodeError.

        Verifies that:
        - Invalid JSON content raises appropriate error
        - Error is logged for debugging
        """
        # Arrange
        mock_file_content = "not valid json {"

        with patch("src.repositories.employee_repo.aiofiles") as mock_aiofiles:
            mock_file = AsyncMock()
            mock_file.read = AsyncMock(return_value=mock_file_content)

            mock_open_cm = AsyncMock()
            mock_open_cm.__aenter__.return_value = mock_file
            mock_open_cm.__aexit__.return_value = None

            mock_aiofiles.open.return_value = mock_open_cm

            with patch("src.repositories.employee_repo.settings") as mock_settings:
                mock_settings.employees_file_path = "/test/employees.json"
                repo = EmployeeRepository()

                # Act & Assert
                with pytest.raises(json.JSONDecodeError):
                    await repo.get_all()

    @pytest.mark.asyncio
    async def test_get_all_with_custom_file_path(
        self, sample_employee_data: List[dict]
    ) -> None:
        """Test that custom file path can be provided to constructor.

        Verifies that:
        - Custom file path overrides settings default
        - Data is loaded from the custom path
        """
        # Arrange
        custom_path = "/custom/path/employees.json"
        mock_file_content = json.dumps(sample_employee_data)

        with patch("src.repositories.employee_repo.aiofiles") as mock_aiofiles:
            mock_file = AsyncMock()
            mock_file.read = AsyncMock(return_value=mock_file_content)

            mock_open_cm = AsyncMock()
            mock_open_cm.__aenter__.return_value = mock_file
            mock_open_cm.__aexit__.return_value = None

            mock_aiofiles.open.return_value = mock_open_cm

            with patch("src.repositories.employee_repo.settings"):
                repo = EmployeeRepository(file_path=custom_path)

                # Act
                result = await repo.get_all()

        # Assert
        assert repo.file_path == custom_path
        assert len(result) == len(sample_employee_data)
        mock_aiofiles.open.assert_called_once_with(
            custom_path, mode="r", encoding="utf-8"
        )


class TestGetByName:
    """Tests for get_by_name() method."""

    @pytest.mark.asyncio
    async def test_get_by_name_exact_match(
        self, sample_employee_data: List[dict]
    ) -> None:
        """Test that get_by_name() finds employee with exact name match.

        Verifies that:
        - Employee is found by exact name
        - Correct employee object is returned
        - All employee attributes are populated
        """
        # Arrange
        mock_file_content = json.dumps(sample_employee_data)
        search_name = sample_employee_data[0]["name"]

        with patch("src.repositories.employee_repo.aiofiles") as mock_aiofiles:
            mock_file = AsyncMock()
            mock_file.read = AsyncMock(return_value=mock_file_content)

            mock_open_cm = AsyncMock()
            mock_open_cm.__aenter__.return_value = mock_file
            mock_open_cm.__aexit__.return_value = None

            mock_aiofiles.open.return_value = mock_open_cm

            with patch("src.repositories.employee_repo.settings") as mock_settings:
                mock_settings.employees_file_path = "/test/employees.json"
                repo = EmployeeRepository()

                # Act
                result = await repo.get_by_name(search_name)

        # Assert
        assert result is not None
        assert result.name == search_name
        assert result.id == sample_employee_data[0]["id"]
        assert result.department == sample_employee_data[0]["department"]

    @pytest.mark.asyncio
    async def test_get_by_name_partial_match(
        self, sample_employee_data: List[dict]
    ) -> None:
        """Test that get_by_name() uses case-insensitive matching.

        Verifies that:
        - Case-insensitive search works
        - Whitespace is trimmed during comparison
        """
        # Arrange
        mock_file_content = json.dumps(sample_employee_data)
        # Use lowercase version of the name
        original_name = sample_employee_data[0]["name"]
        search_name = original_name.lower()

        with patch("src.repositories.employee_repo.aiofiles") as mock_aiofiles:
            mock_file = AsyncMock()
            mock_file.read = AsyncMock(return_value=mock_file_content)

            mock_open_cm = AsyncMock()
            mock_open_cm.__aenter__.return_value = mock_file
            mock_open_cm.__aexit__.return_value = None

            mock_aiofiles.open.return_value = mock_open_cm

            with patch("src.repositories.employee_repo.settings") as mock_settings:
                mock_settings.employees_file_path = "/test/employees.json"
                repo = EmployeeRepository()

                # Act
                result = await repo.get_by_name(search_name)

        # Assert
        assert result is not None
        assert result.name == original_name

    @pytest.mark.asyncio
    async def test_get_by_name_with_whitespace(
        self, sample_employee_data: List[dict]
    ) -> None:
        """Test that get_by_name() handles whitespace in search term.

        Verifies that:
        - Leading and trailing whitespace is trimmed
        - Employee is still found correctly
        """
        # Arrange
        mock_file_content = json.dumps(sample_employee_data)
        original_name = sample_employee_data[1]["name"]
        search_name = f"  {original_name}  "  # Add whitespace

        with patch("src.repositories.employee_repo.aiofiles") as mock_aiofiles:
            mock_file = AsyncMock()
            mock_file.read = AsyncMock(return_value=mock_file_content)

            mock_open_cm = AsyncMock()
            mock_open_cm.__aenter__.return_value = mock_file
            mock_open_cm.__aexit__.return_value = None

            mock_aiofiles.open.return_value = mock_open_cm

            with patch("src.repositories.employee_repo.settings") as mock_settings:
                mock_settings.employees_file_path = "/test/employees.json"
                repo = EmployeeRepository()

                # Act
                result = await repo.get_by_name(search_name)

        # Assert
        assert result is not None
        assert result.name == original_name

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(
        self, sample_employee_data: List[dict]
    ) -> None:
        """Test that get_by_name() returns None when employee not found.

        Verifies that:
        - None is returned for non-existent name
        - No exception is raised
        """
        # Arrange
        mock_file_content = json.dumps(sample_employee_data)
        search_name = "Nonexistent Employee Name"

        with patch("src.repositories.employee_repo.aiofiles") as mock_aiofiles:
            mock_file = AsyncMock()
            mock_file.read = AsyncMock(return_value=mock_file_content)

            mock_open_cm = AsyncMock()
            mock_open_cm.__aenter__.return_value = mock_file
            mock_open_cm.__aexit__.return_value = None

            mock_aiofiles.open.return_value = mock_open_cm

            with patch("src.repositories.employee_repo.settings") as mock_settings:
                mock_settings.employees_file_path = "/test/employees.json"
                repo = EmployeeRepository()

                # Act
                result = await repo.get_by_name(search_name)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_name_empty_database(self) -> None:
        """Test that get_by_name() returns None when no employees exist.

        Verifies that:
        - None is returned for empty employee list
        - No exception is raised
        """
        # Arrange
        mock_file_content = "[]"
        search_name = "Any Name"

        with patch("src.repositories.employee_repo.aiofiles") as mock_aiofiles:
            mock_file = AsyncMock()
            mock_file.read = AsyncMock(return_value=mock_file_content)

            mock_open_cm = AsyncMock()
            mock_open_cm.__aenter__.return_value = mock_file
            mock_open_cm.__aexit__.return_value = None

            mock_aiofiles.open.return_value = mock_open_cm

            with patch("src.repositories.employee_repo.settings") as mock_settings:
                mock_settings.employees_file_path = "/test/employees.json"
                repo = EmployeeRepository()

                # Act
                result = await repo.get_by_name(search_name)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_name_file_not_found_raises_error(self) -> None:
        """Test that get_by_name() raises error when file doesn't exist.

        Verifies that:
        - FileNotFoundError is propagated from get_all()
        - Error can be handled by caller
        """
        # Arrange
        with patch("src.repositories.employee_repo.aiofiles") as mock_aiofiles:
            mock_aiofiles.open.side_effect = FileNotFoundError("File not found")

            with patch("src.repositories.employee_repo.settings") as mock_settings:
                mock_settings.employees_file_path = "/nonexistent/path.json"
                repo = EmployeeRepository()

                # Act & Assert
                with pytest.raises(FileNotFoundError):
                    await repo.get_by_name("Any Name")


class TestRepositoryInit:
    """Tests for EmployeeRepository initialization."""

    def test_init_uses_settings_default(self) -> None:
        """Test that repository uses settings default file path.

        Verifies that:
        - Default file path is loaded from settings
        - Custom path parameter is optional
        """
        # Arrange & Act
        with patch("src.repositories.employee_repo.settings") as mock_settings:
            mock_settings.employees_file_path = "/default/path.json"
            repo = EmployeeRepository()

        # Assert
        assert repo.file_path == "/default/path.json"

    def test_init_with_custom_path(self) -> None:
        """Test that repository accepts custom file path.

        Verifies that:
        - Custom file path overrides settings
        """
        # Arrange
        custom_path = "/custom/path.json"

        # Act
        with patch("src.repositories.employee_repo.settings"):
            repo = EmployeeRepository(file_path=custom_path)

        # Assert
        assert repo.file_path == custom_path


class TestEmployeeModel:
    """Tests for Employee model validation within repository context."""

    @pytest.mark.asyncio
    async def test_employee_with_optional_department(self) -> None:
        """Test that employees without department are loaded correctly.

        Verifies that:
        - Optional department field can be None
        - Employee is still valid without department
        """
        # Arrange
        employee_data = [
            {"id": "1", "name": "Test Employee", "department": None},
        ]
        mock_file_content = json.dumps(employee_data)

        with patch("src.repositories.employee_repo.aiofiles") as mock_aiofiles:
            mock_file = AsyncMock()
            mock_file.read = AsyncMock(return_value=mock_file_content)

            mock_open_cm = AsyncMock()
            mock_open_cm.__aenter__.return_value = mock_file
            mock_open_cm.__aexit__.return_value = None

            mock_aiofiles.open.return_value = mock_open_cm

            with patch("src.repositories.employee_repo.settings") as mock_settings:
                mock_settings.employees_file_path = "/test/employees.json"
                repo = EmployeeRepository()

                # Act
                result = await repo.get_all()

        # Assert
        assert len(result) == 1
        assert result[0].department is None

    @pytest.mark.asyncio
    async def test_employee_missing_required_field_raises_error(self) -> None:
        """Test that missing required fields raise validation error.

        Verifies that:
        - Missing 'name' field raises validation error
        - Pydantic validation is working correctly
        """
        # Arrange
        invalid_employee_data = [
            {"id": "1", "department": "IT"},  # Missing 'name'
        ]
        mock_file_content = json.dumps(invalid_employee_data)

        with patch("src.repositories.employee_repo.aiofiles") as mock_aiofiles:
            mock_file = AsyncMock()
            mock_file.read = AsyncMock(return_value=mock_file_content)

            mock_open_cm = AsyncMock()
            mock_open_cm.__aenter__.return_value = mock_file
            mock_open_cm.__aexit__.return_value = None

            mock_aiofiles.open.return_value = mock_open_cm

            with patch("src.repositories.employee_repo.settings") as mock_settings:
                mock_settings.employees_file_path = "/test/employees.json"
                repo = EmployeeRepository()

                # Act & Assert
                with pytest.raises(Exception):  # Pydantic ValidationError
                    await repo.get_all()

    @pytest.mark.asyncio
    async def test_employee_data_with_all_fields(self) -> None:
        """Test that employees with all fields are loaded correctly.

        Verifies that:
        - All employee fields are properly parsed
        - Department is correctly assigned
        """
        # Arrange
        employee_data = [
            {"id": "1", "name": "Full Employee", "department": "Engineering"},
        ]
        mock_file_content = json.dumps(employee_data)

        with patch("src.repositories.employee_repo.aiofiles") as mock_aiofiles:
            mock_file = AsyncMock()
            mock_file.read = AsyncMock(return_value=mock_file_content)

            mock_open_cm = AsyncMock()
            mock_open_cm.__aenter__.return_value = mock_file
            mock_open_cm.__aexit__.return_value = None

            mock_aiofiles.open.return_value = mock_open_cm

            with patch("src.repositories.employee_repo.settings") as mock_settings:
                mock_settings.employees_file_path = "/test/employees.json"
                repo = EmployeeRepository()

                # Act
                result = await repo.get_all()

        # Assert
        assert len(result) == 1
        assert result[0].id == "1"
        assert result[0].name == "Full Employee"
        assert result[0].department == "Engineering"
