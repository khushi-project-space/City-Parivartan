from config import SMTP_USER, SMTP_PASS, SMTP_SERVER, SMTP_PORT
import smtplib
from email.mime.text import MIMEText
import traceback

socketio = None  # Will be injected from app.py

def notify_user_status_change(email, issue_id, title, status, updated_at):
    """Send real-time socket update and email to user."""

    # --- SocketIO real-time notification ---
    if socketio:
        socketio.emit("status_update", {
            "issue_id": issue_id,
            "title": title,
            "status": status,
            "updated_at": updated_at,
            "email": email
        }, room=email)

    # --- Email Notification ---
    subject = f"Issue #{issue_id} Status Updated"
    body = f"""
Hello,

Your issue (ID #{issue_id}) titled "{title}" has been updated to '{status}' on {updated_at}.

Thank you,
Support Team
"""

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = email

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.set_debuglevel(1)  # ✅ Enable SMTP debug logs
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        print(f"📧 Email sent to {email}")
    except Exception as e:
        print(f"❌ Failed to send email to {email}: {e}")
        traceback.print_exc()
