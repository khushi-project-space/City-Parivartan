from flask import Blueprint, render_template, request, redirect, url_for
from config import get_connection
import os

bp = Blueprint("roads", __name__, url_prefix="/roads")

@bp.route("/")
def roads_page():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM reports WHERE category='Roads' ORDER BY created_at DESC")
    reports = cursor.fetchall()

    cursor.execute("SELECT * FROM report_interactions ORDER BY created_at ASC")
    interactions = cursor.fetchall()
    conn.close()

    for report in reports:
        if report.get("image_path"):
            report["image_path"] = os.path.basename(report["image_path"])
        if report.get("resolved_photo_path"):
            report["resolved_photo_path"] = os.path.basename(report["resolved_photo_path"])

    comments_dict = {}
    for report in reports:
        report_id = report['id']
        likes = sum(1 for i in interactions if i['report_id'] == report_id and i['interaction_type'] == 'like')
        dislikes = sum(1 for i in interactions if i['report_id'] == report_id and i['interaction_type'] == 'dislike')
        report['likes'] = likes
        report['dislikes'] = dislikes
        comments_dict[report_id] = [
            i for i in interactions
            if i['report_id'] == report_id and i['interaction_type'] == 'comment'
        ]

    return render_template("user/roads.html", reports=reports, comments=comments_dict)


@bp.route("/interact", methods=["POST"])
def roads_interact():
    report_id = request.form.get("report_id")
    interaction_type = request.form.get("interaction_type")
    comment_text = request.form.get("comment", None)

    conn = get_connection()
    cursor = conn.cursor()

    if interaction_type == "comment" and comment_text:
        cursor.execute(
            "INSERT INTO report_interactions (report_id, interaction_type, comment) VALUES (%s, %s, %s)",
            (report_id, interaction_type, comment_text)
        )
    elif interaction_type in ["like", "dislike"]:
        cursor.execute(
            "INSERT INTO report_interactions (report_id, interaction_type) VALUES (%s, %s)",
            (report_id, interaction_type)
        )

    conn.commit()
    conn.close()
    return redirect(url_for("roads.roads_page"))
