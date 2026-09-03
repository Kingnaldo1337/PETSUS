from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage

import streamlit as st

from .registration import OTP_TTL_MINUTES


def setting(name: str, default: str = "") -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        return str(st.secrets.get(name, default)).strip()
    except (FileNotFoundError, AttributeError, KeyError):
        return default


def send_verification_code(recipient: str, code: str) -> None:
    host = setting("PETSUS_SMTP_HOST")
    port_text = setting("PETSUS_SMTP_PORT", "587")
    username = setting("PETSUS_SMTP_USERNAME")
    password = setting("PETSUS_SMTP_PASSWORD")
    sender = setting("PETSUS_SMTP_FROM", username)
    security = setting("PETSUS_SMTP_SECURITY", "starttls").lower()
    if not host or not sender:
        raise RuntimeError("O envio de e-mail ainda não foi configurado pela administração.")
    try:
        port = int(port_text)
    except ValueError as exc:
        raise RuntimeError("A porta SMTP configurada é inválida.") from exc

    message = EmailMessage()
    message["Subject"] = "Código de verificação PETSUS"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        f"Seu código de verificação é: {code}\n\n"
        f"Ele expira em {OTP_TTL_MINUTES} minutos. "
        "Se você não solicitou este cadastro, ignore esta mensagem."
    )

    context = ssl.create_default_context()
    if security == "ssl":
        with smtplib.SMTP_SSL(host, port, timeout=15, context=context) as smtp:
            if username:
                smtp.login(username, password)
            smtp.send_message(message)
    else:
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            smtp.ehlo()
            if security == "starttls":
                smtp.starttls(context=context)
                smtp.ehlo()
            if username:
                smtp.login(username, password)
            smtp.send_message(message)
