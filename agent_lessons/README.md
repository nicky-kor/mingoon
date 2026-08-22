# 에이전트 / Harness 개발 학습

Claude API를 이용해 "에이전트"와 "harness"(에이전트를 실행시키는 코드)를 손으로 만들어보며 배우는 실습 코드입니다.

## 실행 준비

1. `.env.example`을 `.env`로 복사
2. https://console.anthropic.com/settings/keys 에서 API 키 발급 후 `ANTHROPIC_API_KEY`에 입력
3. `pip install -r requirements.txt` (세션 시작 시 자동 설치됨)

## 학습 순서

| 단계 | 파일 | 배우는 것 |
|---|---|---|
| 1 | `step1_basic_call.py` | Claude API 기본 호출 — 질문 한 번, 답변 한 번 |
| 2 | `step2_todo_tool.py` | 도구(tool) 3개(`add_todo`/`list_todos`/`complete_todo`) 쥐어주기 — Claude가 도구 호출을 "요청"하면 우리가 실행해서 결과를 돌려주는 흐름. 아직 자동 반복은 없음 |
| 3 | (예정) | 수동 에이전트 루프 직접 짜기 — harness의 정체. Step 2를 여러 도구가 필요한 요청도 처리하도록 확장 |
| 4 | (예정) | Tool Runner로 같은 걸 다시 만들기 — SDK가 대신 해주는 부분 비교 |

각 단계는 이전 단계 위에 쌓입니다. 순서대로 진행하세요.

## Step 2 예제 — 실제 할 일 관리 에이전트

```bash
python agent_lessons/step2_todo_tool.py "내일까지 보고서 끝내기 추가해줘"
python agent_lessons/step2_todo_tool.py "할 일 목록 보여줘"
python agent_lessons/step2_todo_tool.py "1번 완료 처리해줘"
```

할 일은 `agent_lessons/todos.json`에 저장됩니다 (커밋되지 않음, `.gitignore`에 등록).

**한계**: "1번 완료하고 목록도 보여줘"처럼 도구를 두 번 써야 하는 요청은 이 스크립트로 한 번에 처리되지 않습니다 — 왜 그런지, 어떻게 고치는지가 Step 3의 주제입니다.
