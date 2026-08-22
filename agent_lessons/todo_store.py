"""아주 단순한 할 일(TODO) 저장소.

JSON 파일 하나에 목록을 저장합니다. Claude가 호출할 "도구(tool)"의 실제
구현부입니다 — Claude는 이 함수들을 직접 실행하지 못하고, "이 함수를
이런 입력으로 불러줘"라고 요청만 합니다. 실행은 항상 우리 코드(harness)가 합니다.
"""

import json
from pathlib import Path

STORE_PATH = Path(__file__).parent / "todos.json"


def _load() -> list[dict]:
    if not STORE_PATH.exists():
        return []
    return json.loads(STORE_PATH.read_text(encoding="utf-8"))


def _save(todos: list[dict]) -> None:
    STORE_PATH.write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding="utf-8")


def add_todo(title: str) -> dict:
    """할 일을 하나 추가합니다."""
    todos = _load()
    new_id = (max((t["id"] for t in todos), default=0)) + 1
    todo = {"id": new_id, "title": title, "done": False}
    todos.append(todo)
    _save(todos)
    return todo


def list_todos(include_done: bool = True) -> list[dict]:
    """할 일 목록을 조회합니다."""
    todos = _load()
    if not include_done:
        todos = [t for t in todos if not t["done"]]
    return todos


def complete_todo(todo_id: int) -> dict | None:
    """할 일을 완료 처리합니다. 존재하지 않으면 None을 반환합니다."""
    todos = _load()
    for t in todos:
        if t["id"] == todo_id:
            t["done"] = True
            _save(todos)
            return t
    return None
