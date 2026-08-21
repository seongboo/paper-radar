import smtplib

import pytest

from paper_radar import mailer
from paper_radar.models import EmailConfig


class FakeSMTP:
    created: list["FakeSMTP"] = []

    def __init__(self, host, port):
        self.host, self.port = host, port
        self.tls_started = False
        self.login_args = None
        self.sent = []
        FakeSMTP.created.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        self.tls_started = True

    def login(self, user, password):
        self.login_args = (user, password)

    def send_message(self, msg):
        self.sent.append(msg)


@pytest.fixture(autouse=True)
def fake_smtp(monkeypatch):
    FakeSMTP.created = []
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)


def _cfg(**kw) -> EmailConfig:
    defaults = dict(to=["a@example.com"], smtp_host="smtp.example.com", smtp_user="u@example.com")
    defaults.update(kw)
    return EmailConfig(**defaults)


def test_send_digest_message_and_login(monkeypatch):
    monkeypatch.setenv(mailer.PASSWORD_ENV, "secret")
    mailer.send_digest(_cfg(to=["a@example.com", "b@example.com"]), "2026-08-21", "본문")

    [server] = FakeSMTP.created
    assert (server.host, server.port) == ("smtp.example.com", 587)
    assert server.tls_started is True
    assert server.login_args == ("u@example.com", "secret")
    [msg] = server.sent
    assert msg["Subject"] == "논문 레이더 2026-08-21"
    assert msg["To"] == "a@example.com, b@example.com"
    assert msg["From"] == "u@example.com"
    assert "본문" in msg.get_content()


def test_no_login_without_password(monkeypatch):
    monkeypatch.delenv(mailer.PASSWORD_ENV, raising=False)
    mailer.send_digest(_cfg(), "2026-08-21", "본문")
    [server] = FakeSMTP.created
    assert server.login_args is None
    assert len(server.sent) == 1


def test_ssl_skips_starttls(monkeypatch):
    monkeypatch.setenv(mailer.PASSWORD_ENV, "secret")
    mailer.send_digest(_cfg(ssl=True, starttls=True, smtp_port=465), "2026-08-21", "x")
    [server] = FakeSMTP.created
    assert server.port == 465
    assert server.tls_started is False  # SMTPS 에서는 starttls 안 함
