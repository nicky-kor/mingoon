"""Step 1: Claude API 기본 호출

에이전트/harness를 배우기 전에, 가장 밑바닥인 "질문 한 번 -> 답변 한 번"
왕복부터 확인합니다. 아직 도구(tool)도, 반복 루프도 없습니다.

실행 전 준비:
1. .env.example을 .env로 복사
2. https://console.anthropic.com/settings/keys 에서 발급받은 키를
   ANTHROPIC_API_KEY에 입력

실행:
    python agent_lessons/step1_basic_call.py
"""

import os

import anthropic
from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    # 클라이언트는 ANTHROPIC_API_KEY 환경변수를 자동으로 읽습니다.
    client = anthropic.Anthropic()

    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": "한 문장으로, Claude API의 Messages 엔드포인트가 뭔지 설명해줘."}
        ],
    )

    # response.content는 블록(block) 리스트입니다. 텍스트 블록만 골라 출력합니다.
    for block in response.content:
        if block.type == "text":
            print(block.text)

    print(f"\n(참고) stop_reason: {response.stop_reason}")
    print(f"(참고) 사용 토큰: input={response.usage.input_tokens}, output={response.usage.output_tokens}")


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit(
            ".env 파일에 ANTHROPIC_API_KEY를 설정하세요. "
            "https://console.anthropic.com/settings/keys 에서 발급받을 수 있습니다."
        )
    main()
