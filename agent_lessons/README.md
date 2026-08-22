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
| 2 | (예정) | 도구(tool) 하나 쥐어주기 — Claude가 도구 호출을 "요청"하는 흐름 |
| 3 | (예정) | 수동 에이전트 루프 직접 짜기 — harness의 정체 |
| 4 | (예정) | Tool Runner로 같은 걸 다시 만들기 — SDK가 대신 해주는 부분 비교 |

각 단계는 이전 단계 위에 쌓입니다. 순서대로 진행하세요.
