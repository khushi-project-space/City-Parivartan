from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from config import get_connection
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

bp = Blueprint("admin_complaints", __name__)  # must match sidebar link

UPLOAD_FOLDER = os.path.join("static", "resolved_images")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ===========================
# Complaints Overview Page
# ===========================
@bp.route("/admin/complaints")
def admin_complaints():   # must match sidebar link
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch complaint reports
    cursor.execute("""
    SELECT r.id AS report_id, r.category, r.area, r.description,
           r.image_path, r.resolved_photo_path, r.status
    FROM reports r
    ORDER BY r.created_at DESC
    """)
    reports = cursor.fetchall()

    for report in reports:
        report_id = report["report_id"]

        # Likes
        cursor.execute("""
            SELECT COUNT(*) AS likes FROM report_interactions
            WHERE report_id=%s AND interaction_type='like'
        """, (report_id,))
        report['likes'] = cursor.fetchone()['likes']

        # Dislikes
        cursor.execute("""
            SELECT COUNT(*) AS dislikes FROM report_interactions
            WHERE report_id=%s AND interaction_type='dislike'
        """, (report_id,))
        report['dislikes'] = cursor.fetchone()['dislikes']

        # Comments
        cursor.execute("""
            SELECT comment FROM report_interactions
            WHERE report_id=%s AND interaction_type='comment'
            ORDER BY created_at ASC
        """, (report_id,))
        report['comments'] = cursor.fetchall()

        # Ensure correct image for resolved complaints
        if report.get('status') and report['status'].lower() == 'resolved' and report.get('resolved_photo_path'):
            report['image_path'] = report['resolved_photo_path']
        elif report.get('image_path'):
            report['image_path'] = os.path.basename(report['image_path'])

    cursor.close()
    conn.close()

    return render_template("admin/admin_complaints.html", complaints=reports)

# ===========================
# Upload Resolved Photo
# ===========================
@bp.route("/upload-resolved/<int:report_id>", methods=["POST"])
def upload_resolved(report_id):
    if "photo" not in request.files:
        return jsonify({"success": False, "error": "No file part"})
    file = request.files["photo"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No selected file"})
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    # Open the image and add text
    try:
        image = Image.open(file)
        if image.mode in ("RGBA", "LA"):
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        draw = ImageDraw.Draw(image)

        # Use default font
        font_path = os.path.join("arial.ttf")
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, 20)
        else:
            font = ImageFont.load_default()

        # Get lat/long and datetime
        latitude = request.form.get("latitude", "")
        longitude = request.form.get("longitude", "")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = f"Lat: {latitude}  Lon: {longitude}  {now}"

        margin = 10
        text_width, text_height = draw.textsize(text, font=font)
        x = margin
        y = image.height - text_height - margin
        draw.text((x, y), text, fill="white", font=font)

        image.save(file_path, "JPEG")
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

    # Update database
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE reports SET resolved_photo_path=%s, status='Resolved' WHERE id=%s",
                       (filename, report_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
