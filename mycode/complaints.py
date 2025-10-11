from flask import Blueprint, redirect, render_template, request, url_for
from config import get_connection
import os

bp = Blueprint("complaints", __name__)

@bp.route("/complaints")
def complaints():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch all reports
    cursor.execute("SELECT * FROM reports ORDER BY created_at DESC")
    reports = cursor.fetchall()

    # Fetch all interactions
    cursor.execute("SELECT * FROM report_interactions ORDER BY created_at ASC")
    interactions = cursor.fetchall()
    conn.close()

    # Fix image paths
    for report in reports:
        if report.get("image_path"):
            report["image_path"] = os.path.basename(report["image_path"])
        if report.get("resolved_photo_path"):
            report["resolved_photo_path"] = os.path.basename(report["resolved_photo_path"])

    # Likes, dislikes, comments
    comments_dict = {}
    for report in reports:
        report_id = report['id']
        likes = sum(1 for i in interactions if i['report_id']==report_id and i['interaction_type']=='like')
        dislikes = sum(1 for i in interactions if i['report_id']==report_id and i['interaction_type']=='dislike')
        report['likes'] = likes
        report['dislikes'] = dislikes
        comments_dict[report_id] = [i for i in interactions if i['report_id']==report_id and i['interaction_type']=='comment']

    return render_template("user/complaints.html", reports=reports, comments=comments_dict)


@bp.route("/complaints/interact", methods=["POST"])
def interact():
    report_id = request.form.get("report_id")
    interaction_type = request.form.get("interaction_type")
    comment_text = request.form.get("comment", "").strip()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Get report data for duplication
    cursor.execute("SELECT category, area, description, image_path FROM reports WHERE id=%s", (report_id,))
    report = cursor.fetchone()

    if not report:
        conn.close()
        return redirect(url_for("complaints.complaints"))

    # Add comment
    if comment_text and interaction_type == "comment":
        cursor.execute(
            """
            INSERT INTO report_interactions 
            (report_id, category, area, description, interaction_type, comment, image_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (report_id, report['category'], report['area'], report['description'],
             "comment", comment_text, report['image_path'])
        )

    # Add like/dislike
    elif interaction_type in ["like", "dislike"]:
        cursor.execute(
            """
            INSERT INTO report_interactions 
            (report_id, category, area, description, interaction_type, comment, image_path)
            VALUES (%s, %s, %s, %s, %s, '', %s)
            """,
            (report_id, report['category'], report['area'], report['description'],
             interaction_type, report['image_path'])
        )

    conn.commit()
    conn.close()
    return redirect(url_for("complaints.complaints"))
