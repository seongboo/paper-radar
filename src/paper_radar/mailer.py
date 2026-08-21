"""메일 발송: 다이제스트 Markdown 을 그대로 본문으로 보낸다.

비밀번호는 SMTP_PASSWORD 환경변수로만 받는다 — profile.yaml 에 두지 않는다.
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

from .models import EmailConfig

PASSWORD_ENV = "SMTP_PASSWORD"


def send_digest(cfg: EmailConfig, date: str, body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = f"논문 레이더 {date}"
    msg["From"] = cfg.sender or cfg.smtp_user or cfg.to[0]
    msg["To"] = ", ".join(cfg.to)
    msg.set_content(body)

    password = os.environ.get(PASSWORD_ENV)
    smtp_cls = smtplib.SMTP_SSL if cfg.ssl else smtplib.SMTP
    with smtp_cls(cfg.smtp_host, cfg.smtp_port) as server:
        if cfg.starttls and not cfg.ssl:
            server.starttls()
        if cfg.smtp_user and password:
            server.login(cfg.smtp_user, password)
        server.send_message(msg)
