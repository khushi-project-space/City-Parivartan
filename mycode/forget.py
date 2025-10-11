from flask import Blueprint, render_template, request, jsonify, session
from werkzeug.security import generate_password_hash
from config import get_connection, SMTP_USER, SMTP_PASS, SMTP_SERVER, SMTP_PORT
import random, smtplib
from email.mime.text import MIMEText

bp = Blueprint("forget", __name__)

# Temporary OTP store
otp_store = {}  # {email: otp}

# ---------------- Utility Functions ----------------
def send_email(email, otp):
    subject = "OTP for Password Reset"
    body = f"Hello,\n\nYour OTP for password reset is: {otp}\n\nThanks."
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = email
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("SMTP Error:", e)

def get_user_or_admin(email):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id,email FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    if user:
        cur.close(); conn.close()
        return "user", user
    cur.execute("SELECT admin_id,email FROM admins WHERE email=%s", (email,))
    admin = cur.fetchone()
    cur.close(); conn.close()
    if admin:
        return "admin", admin
    return None, None

def update_password(email, type_, hashed):
    conn = get_connection()
    cur = conn.cursor()
    if type_=="user":
        cur.execute("UPDATE users SET password=%s WHERE email=%s", (hashed,email))
    else:
        cur.execute("UPDATE admins SET password=%s WHERE email=%s", (hashed,email))
    conn.commit()
    cur.close(); conn.close()

# ---------------- Routes ----------------
@bp.route("/forget")
def forget_page():
    return render_template("user/forget.html")

@bp.route("/forget_send_otp", methods=["POST"])
def send_otp():
    data = request.get_json()
    email = data.get("email","").strip()
    type_, user = get_user_or_admin(email)
    if not user:
        return jsonify({"status":"error","message":"Email not found!"})
    otp = str(random.randint(1000,9999))
    otp_store[email] = otp
    session["forget_email"] = email
    session["forget_type"] = type_
    send_email(email, otp)
    return jsonify({"status":"ok","otp":otp})  # return otp only for demo/testing

@bp.route("/forget_verify_otp", methods=["POST"])
def verify_otp():
    data = request.get_json()
    email = data.get("email","")
    otp_input = data.get("otp","")
    if otp_store.get(email)==otp_input:
        return jsonify({"status":"ok"})
    else:
        return jsonify({"status":"error","message":"Invalid OTP"})

@bp.route("/forget_reset_password", methods=["POST"])
def reset_password():
    data = request.get_json()
    email = data.get("email","")
    new_password = data.get("new_password","")
    type_ = session.get("forget_type")
    if not type_ or not email:
        return jsonify({"status":"error","message":"Session expired, try again!"})
    hashed = generate_password_hash(new_password)
    update_password(email, type_, hashed)
    otp_store.pop(email,None)
    session.pop("forget_email",None)
    session.pop("forget_type",None)
    return jsonify({"status":"ok"})