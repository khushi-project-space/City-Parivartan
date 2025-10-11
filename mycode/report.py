from flask import Blueprint, jsonify, render_template, request, current_app, flash, redirect, url_for, session, send_file
import os
import base64
import re
import random
from config import get_connection, SMTP_USER, SMTP_PASS, SMTP_SERVER, SMTP_PORT
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from fpdf import FPDF
from io import BytesIO

bp = Blueprint("report", __name__)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


# ==================== PDF GENERATION ====================
def generate_report_pdf(report_data):
    """
    Generate a PDF from report_data dict and return a BytesIO object.
    """
    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Civic Issue Report", ln=True, align="C")
    pdf.ln(10)

    # Report details
    pdf.set_font("Arial", "", 12)
    for key, value in report_data.items():
        if key != "image_path":
            pdf.multi_cell(0, 8, f"{key.capitalize()}: {value}")
            pdf.ln(1)

    # Add image if exists
    if report_data.get("image_path") and os.path.exists(report_data["image_path"]):
        pdf.ln(5)
        try:
            pdf.image(report_data["image_path"], w=100)
        except:
            pass  # ignore if image can't be added

    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer


# ==================== OTP HANDLING ====================
@bp.route("/send_otp", methods=["POST"])
def send_otp():
    """
    Sends OTP to user's email.
    """
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"success": False, "message": "Missing email"})

    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))
    session["otp"] = otp
    session["otp_email"] = email

    try:
        subject = "Your OTP for Report Submission"
        body = f"Your OTP is: {otp}"

        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()

        print(f"📧 OTP sent successfully to {email}")
        return jsonify({"success": True})

    except Exception as e:
        print(f"❌ OTP sending failed: {str(e)}")
        return jsonify({"success": False, "message": str(e)})


@bp.route("/verify_otp", methods=["POST"])
def verify_otp():
    """
    Verifies the OTP entered by user.
    """
    data = request.get_json()
    email = data.get("email")
    otp_input = data.get("otp")

    if not email or not otp_input:
        return jsonify({"success": False, "message": "Missing data"})

    if session.get("otp") == otp_input and session.get("otp_email") == email:
        session.pop("otp")
        session.pop("otp_email")
        session["otp_verified"] = True
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "Invalid OTP"})


# ==================== REPORT ISSUE ====================
@bp.route("/report_issue", methods=["GET", "POST"])
def report_issue():
    if "user_email" not in session:
        flash("⚠️ Please login first!", "warning")
        return redirect(url_for("login1.login"))

    user_email = session["user_email"]

    if request.method == "POST":

        # ===== OTP CHECK =====
        if not session.get("otp_verified"):
            flash("⚠️ Please verify OTP before submitting report!", "danger")
            return redirect(url_for("report.report_issue"))

        # ===== Form Data =====
        email = request.form.get("email", user_email)
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        severity = request.form.get("severity", "").strip()
        area = request.form.get("area", "").strip()
        latitude = request.form.get("latitude", "").strip()
        longitude = request.form.get("longitude", "").strip()
        image_data = request.form.get("photo_data", "")

        # ===== Validate coordinates =====
        if not latitude or not longitude or latitude.lower() == "n/a" or longitude.lower() == "n/a":
            flash("⚠️ Please select a valid location on the map!", "danger")
            return redirect(url_for("report.report_issue"))

        filepath = ""

        # ===== Image Handling =====
        if image_data:
            try:
                img_str = re.sub(r"^data:image/.+;base64,", "", image_data)
                img_bytes = base64.b64decode(img_str.encode("utf-8"))

                if len(img_bytes) > MAX_FILE_SIZE:
                    flash("⚠️ Photo size must be < 5MB.", "danger")
                    return redirect(url_for("report.report_issue"))

                os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
                filename = f"{title.replace(' ', '_')}.jpg"
                filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

                with open(filepath, "wb") as f:
                    f.write(img_bytes)

            except Exception as e:
                flash(f"⚠️ Image upload failed: {str(e)}", "danger")
                return redirect(url_for("report.report_issue"))

        # ===== Save to DB =====
        try:
            db = get_connection()
            cursor = db.cursor()

            cursor.execute(
                """
                INSERT INTO reports
                (email, title, description, category, severity, area, latitude, longitude, image_path, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                """,
                (email, title, description, category, severity, area, latitude, longitude, filepath)
            )
            db.commit()
            report_id = cursor.lastrowid

            # Fetch user info
            cursor.execute("SELECT id, first_name, last_name FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()
            user_id = user[0] if user else None
            user_name = f"{user[1]} {user[2]}" if user else "Unknown"

            cursor.close()
            db.close()

            # ===== Send email to Admin =====
            subject = f"📢 New Report Submitted (ID: {report_id})"
            body = f"""
Hello Admin,

A new issue has been reported.

🆔 Report ID: {report_id}
📌 Title: {title}
📝 Description: {description}
🏠 Area: {area}
📂 Category: {category}
⚠️ Severity: {severity}

👤 Reported By:
User ID: {user_id}
Name: {user_name}
Email: {email}

Regards,
Civic System
"""
            msg = MIMEMultipart()
            msg["From"] = SMTP_USER
            msg["To"] = "cityparivartan@gmail.com"
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            if filepath and os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(filepath)}"
                )
                msg.attach(part)

            try:
                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15)
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
                server.quit()
                print("📧 Report email sent to Admin!")
            except Exception as e:
                print(f"❌ Failed to send report email: {e}")

            # ===== Clear OTP =====
            session.pop("otp_verified", None)

            # ===== Generate PDF =====
            pdf_file = generate_report_pdf({
                "title": title,
                "description": description,
                "category": category,
                "severity": severity,
                "area": area,
                "latitude": latitude,
                "longitude": longitude,
                "image_path": filepath
            })

            return send_file(
                pdf_file,
                as_attachment=True,
                download_name=f"Report_{report_id}.pdf",
                mimetype="application/pdf"
            )

        except Exception as e:
            flash(f"⚠️ Database error: {str(e)}", "danger")
            return redirect(url_for("report.report_issue"))

    # ===== GET Request =====
    return render_template("user/report_issue.html", user_email=user_email)