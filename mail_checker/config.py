"""메일 계정 설정을 환경 변수에서 읽어온다."""

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


@dataclass
class MailAccount:
    label: str
    host: str
    port: int
    username: str
    password: str


def load_accounts() -> list[MailAccount]:
    accounts: list[MailAccount] = []

    google_email = os.getenv("GOOGLE_EMAIL")
    google_password = os.getenv("GOOGLE_APP_PASSWORD")
    if google_email and google_password:
        accounts.append(
            MailAccount(
                label="Google",
                host="imap.gmail.com",
                port=993,
                username=google_email,
                password=google_password,
            )
        )

    naver_email = os.getenv("NAVER_EMAIL")
    naver_password = os.getenv("NAVER_APP_PASSWORD")
    if naver_email and naver_password:
        accounts.append(
            MailAccount(
                label="Naver",
                host="imap.naver.com",
                port=993,
                username=naver_email,
                password=naver_password,
            )
        )

    return accounts
