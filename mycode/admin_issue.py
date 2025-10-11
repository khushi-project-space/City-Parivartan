from flask import Blueprint, render_template, jsonify, request, current_app
from config import get_connection
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from mycode.socket_utils import notify_user_status_change
from flask import send_file
from fpdf import FPDF
import io

bp = Blueprint("admin_issue", __name__)

# ----------------- Generate PDF for an issue -----------------
@bp.route("/generate-pdf/<int:report_id>")
def generate_pdf(report_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reports WHERE id=%s", (report_id,))
    report = cursor.fetchone()
    cursor.close()
    conn.close()

    if not report:
        return "Issue not found", 404

    # ---------- Create PDF ----------
    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Issue Report Details", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", size=12)
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)

    def safe_text(value, max_len=300):
        if value is None:
            return "-"
        value = str(value)
        return value if len(value) <= max_len else value[:max_len] + "..."

    # ---------- Add Report Details ----------
    fields_to_show = [
        "id", "title", "description", "category", "severity",
        "area", "email", "status", "created_at", "updated_at"
    ]

    for key in fields_to_show:
        value = report.get(key, "-")
        text = f"{key.capitalize()}: {safe_text(value)}"
        pdf.multi_cell(190, 10, text)
        pdf.ln(2)

    # ---------- Add Images in SAME PAGE ----------
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, "Attached Images:", ln=True)

    y_start = pdf.get_y()  # current Y position

    # Report Image
    if report.get("image_path"):
        img_path = os.path.join(current_app.root_path, "static", "uploads", report["image_path"])
        if os.path.exists(img_path):
            pdf.set_font("Arial", size=12)
            pdf.text(20, y_start + 5, "Reported:")
            pdf.image(img_path, x=40, y=y_start, w=60, h=0)

    # Resolved Image
    if report.get("resolved_photo_path"):
        resolved_path = os.path.join(current_app.root_path, "static", "resolved_images", report["resolved_photo_path"])
        if os.path.exists(resolved_path):
            pdf.text(110, y_start + 5, "Resolved:")
            pdf.image(resolved_path, x=140, y=y_start, w=60, h=0)

    # ---------- Output to memory ----------
    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)

    filename = f"Issue_{report_id}.pdf"
    return send_file(pdf_output, as_attachment=True, download_name=filename, mimetype="application/pdf")

# ----------------- Display all issues with filters -----------------
@bp.route("/admin/issue")    
def admin_issue():
    status = request.args.get("status")
    category = request.args.get("category")
    severity = request.args.get("severity")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM reports WHERE 1=1"
    params = []

    if status:
        query += " AND status=%s"
        params.append(status)

    if category:
        query += " AND category=%s"
        params.append(category)

    if severity:
        query += " AND severity=%s"
        params.append(severity)

    query += " ORDER BY created_at DESC"
    cursor.execute(query, tuple(params))
    reports = cursor.fetchall()

    cursor.execute("SELECT DISTINCT category FROM reports")
    categories = [row["category"] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    for report in reports:
        report['image_path'] = os.path.basename(report['image_path']) if report.get('image_path') else None
        report['resolved_photo_path'] = os.path.basename(report['resolved_photo_path']) if report.get('resolved_photo_path') else None
        if not report.get('status'):
            report['status'] = "Received"

    return render_template("admin/issue.html", reports=reports, categories=categories,
                           selected_status=status, selected_category=category, selected_severity=severity)

# ----------------- Update issue status -----------------
@bp.route("/update-status/<int:report_id>", methods=["POST"])
def update_status(report_id):
    if not request.is_json:
        return jsonify({"error": "Invalid request"}), 400

    new_status = request.json.get("status")
    if new_status not in ["Received", "In Progress", "Resolved"]:
        return jsonify({"error": "Invalid status"}), 400

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("UPDATE reports SET status=%s, updated_at=%s WHERE id=%s", (new_status, now, report_id))
    cursor.execute("SELECT email, title FROM reports WHERE id=%s", (report_id,))
    row = cursor.fetchone()
    user_email = row["email"]
    title = row["title"]
    conn.commit()
    cursor.close()
    conn.close()

    notify_user_status_change(user_email, report_id, title, new_status, now)
    return jsonify({"success": True, "updated_at": now})

# ----------------- Fetch user details -----------------
@bp.route("/user-details/<path:email>")
def user_details(email):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, first_name, last_name, email, phone_no FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user)

# ----------------- Upload resolved image with lat/lng & timestamp -----------------
@bp.route("/upload-resolved/<int:report_id>", methods=["POST"])
def upload_resolved(report_id):
    if "photo" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    photo = request.files["photo"]
    if photo.filename == "":
        return jsonify({"success": False, "error": "Empty filename"}), 400

    # Get latitude and longitude from form (sent from frontend)
    latitude = request.form.get("latitude", "")
    longitude = request.form.get("longitude", "")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    from PIL import Image, ImageDraw, ImageFont

    folder = os.path.join(current_app.root_path, "static", "resolved_images")
    os.makedirs(folder, exist_ok=True)

    # Open the uploaded image with Pillow
    img = Image.open(photo)

    # Convert RGBA to RGB if needed
    if img.mode in ("RGBA", "LA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
        img = background
    else:
        img = img.convert("RGB")

    draw = ImageDraw.Draw(img)

    # Font setup
    font_path = os.path.join(current_app.root_path, "arial.ttf")  # Make sure arial.ttf exists here
    try:
        font = ImageFont.truetype(font_path, 20)
    except:
        font = ImageFont.load_default()

    # Text to overlay
    text = f"{now} | Lat: {latitude} | Lon: {longitude}"

    # Position: bottom left
    x = 10
    y = img.height - 30
    draw.text((x, y), text, fill="red", font=font)

    # Save file
    ext = ".jpg"
    filename = f"resolved_{report_id}_{int(datetime.now().timestamp())}{ext}"
    filepath = os.path.join(folder, filename)
    img.save(filepath, "JPEG")

    # Update database
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE reports SET resolved_photo_path=%s, updated_at=%s WHERE id=%s",
        (filename, now, report_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"success": True, "filename": filename})
