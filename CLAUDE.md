# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 작업 원칙
- 내 요청이나 가정이 틀렸거나 더 나은 방법이 있으면, 실행하기 전에 먼저 말할 것. 무조건 동의하지 말 것.
- 사실(직접 확인함)과 추측(확인 안 함)을 구분해서 말할 것.
- "됐다"고 하기 전에 실제로 실행하거나 테스트해서 확인할 것. 못 했으면 못 했다고 말할 것.
- 방안을 제안할 때는 단점과 실패할 수 있는 경우를 같이 적을 것.
- 모르면 지어내지 말고 모른다고 할 것.

## 프로젝트 개요
- 아직 본 프로젝트 주제는 정해지지 않았다. 현재 실제 코드는 `agent_lessons/`의 학습용 실습뿐이다.
- 아이패드 등에서 Claude Code on the web으로 이어서 개발하는 것을 전제로 한다. 사용자와의 대화, 문서, 코드 주석은 한국어로 쓴다.

## 개발 환경
- Python 프로젝트다. 의존성은 `requirements.txt`(`anthropic`, `python-dotenv`)에 있다.
- `.claude/hooks/session-start.sh`는 원격 세션(`CLAUDE_CODE_REMOTE=true`)에서만 실행된다. `requirements.txt`가 있으면 `pip install --user`를, `package.json`이 있으면 `npm install`을 실행한다. 새 언어나 도구를 추가하면 이 훅도 함께 갱신해야 한다.
- API 키는 `.env`의 `ANTHROPIC_API_KEY`에서 읽는다. 형식은 `.env.example`을 따른다. `.env`는 gitignore 대상이다.
- 테스트, 린트, 빌드 설정은 아직 없다.

## 실행
```bash
python3 agent_lessons/step1_basic_call.py   # ANTHROPIC_API_KEY 필요, 실제 API 호출(과금)
```

## agent_lessons 구조
- 에이전트와 harness를 직접 만들어보며 배우는 단계별 실습이다. 계획된 순서는 1 기본 호출 → 2 도구 하나 → 3 수동 에이전트 루프 → 4 Tool Runner로 재구현이다. 진행 상황은 `agent_lessons/README.md`의 표에 있다.
- 각 단계는 독립 실행 가능한 `stepN_<주제>.py` 파일 하나로 만들고, 이전 단계 위에 개념을 하나씩만 더한다.
- 기존 파일의 형식을 따른다. 모듈 docstring에는 배우는 것, 준비, 실행 방법을 한국어로 쓴다. `load_dotenv()`를 호출하고, `__main__`에서 키가 없으면 안내 메시지와 함께 종료하며, 학습 포인트에는 한국어 주석을 단다.
- 새 단계를 추가하면 `agent_lessons/README.md`의 학습 순서 표도 갱신한다.
- 모델 ID와 SDK 사용법은 기억에 의존하지 말고 `/claude-api` 스킬로 확인한다.
