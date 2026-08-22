"""Step 2: 도구(tool) 하나 쥐어주기

Step 1은 Claude에게 그냥 텍스트로 물어보고 답만 받았습니다.
이번엔 Claude에게 "할 일 추가/조회/완료" 도구 3개를 알려주고,
Claude가 "이 도구를 이렇게 불러줘"라고 요청하면 우리가 실제로 실행한 뒤
결과를 다시 Claude에게 보여줍니다.

중요: 이 스크립트는 아직 "자동 반복 루프"가 없습니다. Claude가 도구를
한 번 요청하면 딱 한 번만 실행하고 끝냅니다. 만약 Claude가 여러 도구를
연달아 써야 하는 복잡한 요청을 하면 이 스크립트로는 처리 못 합니다.
(그걸 자동으로 반복하게 만드는 게 Step 3의 목표입니다.)

실행 전 준비는 step1_basic_call.py와 동일합니다 (.env에 ANTHROPIC_API_KEY).

실행:
    python agent_lessons/step2_todo_tool.py "내일까지 보고서 끝내기 추가해줘"
"""

import json
import os
import sys

import anthropic
from dotenv import load_dotenv

from todo_store import add_todo, complete_todo, list_todos

load_dotenv()

# 1. 도구 정의 — Claude에게 "이런 함수들을 쓸 수 있어"라고 알려주는 설명서입니다.
#    실제 함수를 실행하는 코드가 아니라, 이름/설명/입력 형식(JSON Schema)만 담습니다.
TOOLS = [
    {
        "name": "add_todo",
        "description": "할 일을 하나 추가한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "할 일 내용"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "list_todos",
        "description": "할 일 목록을 조회한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "include_done": {
                    "type": "boolean",
                    "description": "완료된 항목도 포함할지 여부 (기본 true)",
                },
            },
        },
    },
    {
        "name": "complete_todo",
        "description": "할 일을 완료 처리한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "todo_id": {"type": "integer", "description": "완료 처리할 할 일의 id"},
            },
            "required": ["todo_id"],
        },
    },
]


def execute_tool(name: str, tool_input: dict) -> str:
    """Claude가 요청한 도구를 실제로 실행하고, 결과를 문자열로 돌려줍니다."""
    if name == "add_todo":
        result = add_todo(tool_input["title"])
    elif name == "list_todos":
        result = list_todos(tool_input.get("include_done", True))
    elif name == "complete_todo":
        result = complete_todo(tool_input["todo_id"])
    else:
        return f"알 수 없는 도구: {name}"
    return json.dumps(result, ensure_ascii=False)


def main(user_message: str) -> None:
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": user_message}]

    # 2. 첫 요청 — Claude에게 질문 + 사용 가능한 도구 목록을 함께 보냅니다.
    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=1024,
        tools=TOOLS,
        messages=messages,
    )

    print(f"[1차 응답] stop_reason = {response.stop_reason}")

    tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

    if not tool_use_blocks:
        # 도구가 필요 없는 질문이었던 경우 — 그냥 텍스트로 끝남
        for block in response.content:
            if block.type == "text":
                print(block.text)
        return

    # 3. Claude가 요청한 도구를 실제로 실행합니다.
    for tool in tool_use_blocks:
        print(f"  -> Claude가 도구 호출을 요청함: {tool.name}({tool.input})")

    messages.append({"role": "assistant", "content": response.content})

    tool_results = []
    for tool in tool_use_blocks:
        result = execute_tool(tool.name, tool.input)
        print(f"  -> 실행 결과: {result}")
        tool_results.append(
            {"type": "tool_result", "tool_use_id": tool.id, "content": result}
        )
    messages.append({"role": "user", "content": tool_results})

    # 4. 도구 실행 결과를 Claude에게 다시 보여주고, 최종 답변을 받습니다.
    #    (여기서 Claude가 도구를 또 요청하면 이 스크립트는 처리하지 못합니다 — Step 3에서 다룸)
    followup = client.messages.create(
        model="claude-opus-5",
        max_tokens=1024,
        tools=TOOLS,
        messages=messages,
    )

    print(f"\n[2차 응답] stop_reason = {followup.stop_reason}")
    for block in followup.content:
        if block.type == "text":
            print(block.text)


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit(
            ".env 파일에 ANTHROPIC_API_KEY를 설정하세요. "
            "https://console.anthropic.com/settings/keys 에서 발급받을 수 있습니다."
        )
    user_input = " ".join(sys.argv[1:]) or "할 일 목록 보여줘"
    main(user_input)
