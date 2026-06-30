import os

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from objects import glob
import utils
from argon2 import PasswordHasher
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.api_route("/", methods=["GET", "POST"])
async def password_recovery(request: Request):
    return templates.TemplateResponse(
        "error.html", {"request": request, "error_message": "Currently disabled"}
    )

    data = request.query_params

    if data.get("type") is None and request.method == "GET":
        return templates.TemplateResponse("request_change.html", {"request": request})

    if data.get("type") == "submit" and request.method == "POST":
        form = await request.form()
        if form.get("email") is None:
            return templates.TemplateResponse(
                "error.html", {"request": request, "error_message": "Email not specified"}
            )
        if form.get("username") is None:
            return templates.TemplateResponse(
                "error.html", {"request": request, "error_message": "Username not specified"}
            )

        lost_user = glob.players.get(username=form.get("username"))
        if lost_user is None:
            return templates.TemplateResponse(
                "error.html", {"request": request, "error_message": "User not found"}
            )

        receiver_email = form.get("email")
        if utils.make_md5(receiver_email) != lost_user.email_hash:
            return templates.TemplateResponse(
                "error.html", {"request": request, "error_message": "Invalid email"}
            )

        recovery_token = utils.make_md5(f"{secrets.token_urlsafe(16)}{lost_user.id}")
        glob.rec_tokens[recovery_token] = lost_user.id

        email = os.getenv("EMAIL")
        password = os.getenv("EMAIL_PASSWORD")
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        message = MIMEMultipart()
        message["From"] = email
        message["To"] = receiver_email
        message["Subject"] = "Password recovery"
        message.attach(
            MIMEText(
                f"Hi, you requested a password recovery, recovery link: {glob.config.host}/user/password_recovery?type=change&token={recovery_token}",
                "plain",
            )
        )

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email, password)
            server.sendmail(email, receiver_email, message.as_string())
            server.quit()
        return templates.TemplateResponse(
            "success.html", {"request": request, "success_message": "Recovery email sent"}
        )

    if data.get("type") == "change" and request.method == "GET":
        return templates.TemplateResponse(
            "change_recover.html", {"request": request, "token": data.get("token")}
        )

    if data.get("type") == "change" and request.method == "POST":
        form = await request.form()
        if form.get("token") is None:
            return templates.TemplateResponse(
                "error.html", {"request": request, "error_message": "Token not specified"}
            )
        if form.get("password") is None:
            return templates.TemplateResponse(
                "error.html", {"request": request, "error_message": "Password not specified"}
            )
        if form.get("confirm_password") is None:
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "error_message": "Confirm password not specified"},
            )
        if form.get("password") != form.get("confirm_password"):
            return templates.TemplateResponse(
                "error.html", {"request": request, "error_message": "Passwords do not match"}
            )
        if form.get("token") not in glob.rec_tokens:
            return templates.TemplateResponse(
                "error.html", {"request": request, "error_message": "Invalid token"}
            )

        new_password = form.get("password")
        new_password_hash = utils.make_md5(f"{new_password}taikotaiko")
        ph = PasswordHasher()
        new_password_hash = ph.hash(new_password_hash)
        await glob.db.execute(
            "UPDATE users SET password_hash = $1 WHERE id = $2",
            [new_password_hash, glob.rec_tokens[form.get("token")]],
        )
        del glob.rec_tokens[form.get("token")]
        return templates.TemplateResponse(
            "success.html",
            {
                "request": request,
                "success_message": "Password changed successfully, you can login now",
            },
        )
