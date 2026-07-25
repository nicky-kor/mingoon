import email
import email.message
import imaplib
import unittest
from unittest.mock import MagicMock, patch

from mail_checker.config import MailAccount
from mail_checker.imap_client import IMAPMailChecker, MailCheckError


def make_account() -> MailAccount:
    return MailAccount(
        label="Test",
        host="imap.example.com",
        port=993,
        username="user@example.com",
        password="secret",
    )


class IMAPMailCheckerTests(unittest.TestCase):
    def test_unread_count(self):
        fake_conn = MagicMock()
        fake_conn.select.return_value = ("OK", [b""])
        fake_conn.search.return_value = ("OK", [b"1 2 3"])

        with patch(
            "mail_checker.imap_client.imaplib.IMAP4_SSL", return_value=fake_conn
        ):
            with IMAPMailChecker(make_account()) as checker:
                self.assertEqual(checker.unread_count(), 3)

    def test_recent_unread(self):
        fake_conn = MagicMock()
        fake_conn.search.return_value = ("OK", [b"1 2"])

        def fetch(msg_id, spec):
            msg = email.message.EmailMessage()
            msg["Subject"] = f"Subject {msg_id.decode()}"
            msg["From"] = "sender@example.com"
            msg["Date"] = "Sat, 25 Jul 2026 00:00:00 +0900"
            return ("OK", [(b"1", msg.as_bytes())])

        fake_conn.fetch.side_effect = fetch

        with patch(
            "mail_checker.imap_client.imaplib.IMAP4_SSL", return_value=fake_conn
        ):
            with IMAPMailChecker(make_account()) as checker:
                summaries = checker.recent_unread(limit=2)

        self.assertEqual(len(summaries), 2)
        self.assertTrue(summaries[0].subject.startswith("Subject"))
        self.assertEqual(summaries[0].sender, "sender@example.com")

    def test_login_failure_raises_mail_check_error(self):
        fake_conn = MagicMock()
        fake_conn.login.side_effect = imaplib.IMAP4.error("bad credentials")

        with patch(
            "mail_checker.imap_client.imaplib.IMAP4_SSL", return_value=fake_conn
        ):
            with self.assertRaises(MailCheckError) as ctx:
                with IMAPMailChecker(make_account()):
                    pass
            self.assertIn("로그인 실패", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
