"""IMAP을 통해 읽지 않은 메일을 조회하는 클라이언트."""

import email
import imaplib
from dataclasses import dataclass
from email.header import decode_header, make_header

from mail_checker.config import MailAccount


class MailCheckError(Exception):
    pass


@dataclass
class MailSummary:
    subject: str
    sender: str
    date: str


def _decode(value: str | None) -> str:
    if not value:
        return ""
    return str(make_header(decode_header(value)))


class IMAPMailChecker:
    def __init__(self, account: MailAccount):
        self.account = account
        self._conn: imaplib.IMAP4_SSL | None = None

    def __enter__(self) -> "IMAPMailChecker":
        try:
            self._conn = imaplib.IMAP4_SSL(self.account.host, self.account.port)
            self._conn.login(self.account.username, self.account.password)
        except (imaplib.IMAP4.error, OSError) as exc:
            raise MailCheckError(f"{self.account.label} 로그인 실패: {exc}") from exc
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._conn is not None:
            try:
                self._conn.logout()
            except imaplib.IMAP4.error:
                pass

    def unread_count(self, mailbox: str = "INBOX") -> int:
        status, _ = self._conn.select(mailbox, readonly=True)
        if status != "OK":
            raise MailCheckError(f"{self.account.label} 편지함 선택 실패")
        status, data = self._conn.search(None, "UNSEEN")
        if status != "OK":
            raise MailCheckError(f"{self.account.label} 메일 검색 실패")
        return len(data[0].split())

    def recent_unread(self, limit: int = 5) -> list[MailSummary]:
        status, data = self._conn.search(None, "UNSEEN")
        if status != "OK":
            raise MailCheckError(f"{self.account.label} 메일 검색 실패")

        ids = data[0].split()[-limit:]
        summaries: list[MailSummary] = []
        for msg_id in reversed(ids):
            status, msg_data = self._conn.fetch(
                msg_id, "(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)])"
            )
            if status != "OK" or not msg_data or msg_data[0] is None:
                continue
            raw_header = msg_data[0][1]
            msg = email.message_from_bytes(raw_header)
            summaries.append(
                MailSummary(
                    subject=_decode(msg.get("Subject")) or "(제목 없음)",
                    sender=_decode(msg.get("From")),
                    date=msg.get("Date", ""),
                )
            )
        return summaries
