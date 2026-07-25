"""구글/네이버 메일 확인 CLI."""

import argparse
import sys

from mail_checker.config import MailAccount, load_accounts
from mail_checker.imap_client import IMAPMailChecker, MailCheckError


def check_account(account: MailAccount, limit: int) -> bool:
    print(f"\n=== {account.label} ({account.username}) ===")
    try:
        with IMAPMailChecker(account) as checker:
            count = checker.unread_count()
            print(f"읽지 않은 메일: {count}통")
            if count:
                for mail in checker.recent_unread(limit=limit):
                    print(f"  - [{mail.date}] {mail.sender}: {mail.subject}")
        return True
    except MailCheckError as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="구글/네이버 메일 확인 프로그램")
    parser.add_argument(
        "--limit", type=int, default=5, help="계정별로 표시할 최근 메일 수 (기본값 5)"
    )
    args = parser.parse_args(argv)

    accounts = load_accounts()
    if not accounts:
        print(
            "설정된 계정이 없습니다. .env 파일에 GOOGLE_EMAIL/GOOGLE_APP_PASSWORD "
            "또는 NAVER_EMAIL/NAVER_APP_PASSWORD를 설정하세요.",
            file=sys.stderr,
        )
        return 1

    ok = True
    for account in accounts:
        ok = check_account(account, args.limit) and ok

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
