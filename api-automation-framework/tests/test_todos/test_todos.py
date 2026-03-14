"""
tests/test_todos/test_todos.py — Tests for /todos endpoint
============================================================
CONCEPTS DEMONSTRATED:
  ✔ Boolean field testing (completed: true/false)
  ✔ Filtering via query parameters
  ✔ Pydantic model for Todos
  ✔ Fixture from root conftest (todos_api — session scope)
  ✔ Allure steps, attachments
"""

import pytest
import allure

from src.api.todos_api import TodosAPI
from src.models.todo_model import Todo
from src.utils.helpers import assert_status_code, pretty_json
from src.utils.logger import get_logger

log = get_logger(__name__)


@allure.feature("Todos API")
@allure.story("List Todos")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.smoke
@pytest.mark.todos
def test_get_all_todos_returns_200(todos_api: TodosAPI):
    """Smoke: /todos returns 200 and 200 items."""
    response = todos_api.get_all_todos()
    assert_status_code(response.status_code, 200)
    todos = response.json()
    assert len(todos) == 200, f"Expected 200 todos, got {len(todos)}"


@allure.feature("Todos API")
@allure.story("Filter Todos")
@pytest.mark.regression
@pytest.mark.todos
def test_filter_completed_todos(todos_api: TodosAPI):
    """
    GET /todos?completed=true → only completed todos returned.
    Verifies query parameter filtering works and all returned items
    have completed=True.
    """
    with allure.step("GET /todos?completed=true"):
        response = todos_api.get_completed_todos()

    with allure.step("Assert 200 and all todos are completed"):
        assert_status_code(response.status_code, 200)
        todos = response.json()
        assert len(todos) > 0, "Expected at least one completed todo"
        allure.attach(
            f"Completed todos count: {len(todos)}",
            name="Completed Count",
            attachment_type=allure.attachment_type.TEXT,
        )
        for todo in todos:
            assert todo["completed"] is True, (
                f"Todo id={todo['id']} has completed={todo['completed']}, expected True"
            )


@allure.feature("Todos API")
@allure.story("Filter Todos")
@pytest.mark.regression
@pytest.mark.todos
def test_filter_pending_todos(todos_api: TodosAPI):
    """GET /todos?completed=false → only pending todos returned."""
    response = todos_api.get_pending_todos()
    assert_status_code(response.status_code, 200)
    todos = response.json()
    assert len(todos) > 0
    for todo in todos:
        assert todo["completed"] is False


@allure.feature("Todos API")
@allure.story("Todos Schema Validation")
@pytest.mark.regression
@pytest.mark.todos
@pytest.mark.parametrize("todo_id", [1, 50, 100, 150, 200])
def test_todo_pydantic_validation(todos_api: TodosAPI, todo_id: int):
    """
    Parametrized Pydantic validation across different IDs.
    Covers first, middle, and last items in the 200-item list.
    """
    response = todos_api.get_todo(todo_id)
    assert_status_code(response.status_code, 200)
    todo_data = response.json()

    # Pydantic model validates types and constraints
    todo = Todo(**todo_data)
    assert todo.id == todo_id
    assert isinstance(todo.completed, bool)
    assert len(todo.title) > 0


@allure.feature("Todos API")
@allure.story("Create Todo")
@pytest.mark.crud
@pytest.mark.todos
def test_create_todo(todos_api: TodosAPI, sample_todo_payload: dict):
    """POST /todos → 201 with echoed body."""
    with allure.step("POST /todos with payload"):
        response = todos_api.create_todo(
            title=sample_todo_payload["title"],
            user_id=sample_todo_payload["userId"],
            completed=sample_todo_payload["completed"],
        )

    with allure.step("Assert 201 and response fields"):
        assert_status_code(response.status_code, 201)
        todo = response.json()
        assert todo["title"] == sample_todo_payload["title"]
        assert todo["completed"] == sample_todo_payload["completed"]
        assert todo["userId"] == sample_todo_payload["userId"]


@allure.feature("Todos API")
@allure.story("Mark Todo Complete")
@pytest.mark.crud
@pytest.mark.todos
def test_mark_todo_as_completed(todos_api: TodosAPI):
    """
    PATCH /todos/{id} with completed=True → marks a todo done.
    Demonstrates partial update (PATCH) for a boolean status field.
    """
    with allure.step("PATCH /todos/1 to mark completed"):
        response = todos_api.patch_todo(1, completed=True)

    with allure.step("Assert 200 and completed=True"):
        assert_status_code(response.status_code, 200)
        result = response.json()
        assert result["completed"] is True


@allure.feature("Todos API")
@allure.story("Filter by User")
@pytest.mark.regression
@pytest.mark.todos
@pytest.mark.parametrize("user_id", [1, 2, 3, 4, 5])
def test_todos_by_user_belong_to_user(todos_api: TodosAPI, user_id: int):
    """All todos returned for a userId filter belong to that user."""
    response = todos_api.get_todos_by_user(user_id)
    assert_status_code(response.status_code, 200)
    todos = response.json()
    assert len(todos) > 0
    for todo in todos:
        assert todo["userId"] == user_id
