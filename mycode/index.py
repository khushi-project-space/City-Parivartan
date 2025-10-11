from flask import Blueprint, render_template, jsonify
from config import get_connection

bp = Blueprint("index", __name__)

# ----------------- Dashboard Page -----------------
@bp.route("/admin/index")
def index():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # ✅ Stats: Received, In Progress, Resolved, Total
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN status='Received' THEN 1 ELSE 0 END) AS received_count,
            SUM(CASE WHEN status='In Progress' THEN 1 ELSE 0 END) AS in_progress_count,
            SUM(CASE WHEN status='Resolved' THEN 1 ELSE 0 END) AS resolved_count,
            COUNT(*) AS total_count
        FROM reports
    """)
    stats = cursor.fetchone()

    # ✅ Category-wise issues
    cursor.execute("""
        SELECT category, COUNT(*) AS count
        FROM reports
        GROUP BY category
    """)
    categories = cursor.fetchall()

    # ✅ Recent Issues (last 5)
    cursor.execute("""
        SELECT r.id, u.first_name, u.last_name, r.title, r.status, r.created_at
        FROM reports r
        LEFT JOIN users u ON r.email = u.email
        WHERE r.status IN ('Received', 'In Progress', 'Resolved')
        ORDER BY r.created_at DESC
        LIMIT 3
    """)
    recent_issues = cursor.fetchall()

    cursor.close()
    conn.close()

    # Ensure no nulls and format citizen name and date
    for issue in recent_issues:
        issue["citizen"] = f"{issue.get('first_name','')} {issue.get('last_name','')}".strip() or "Unknown"
        issue["status"] = issue.get("status") or "Received"
        issue["date"] = issue["created_at"].strftime("%Y-%m-%d") if issue.get("created_at") else ""

    return render_template(
        "admin/index.html",
        stats=stats,
        categories=categories,
        recent_issues=recent_issues
    )


# ----------------- API for Charts (optional AJAX use) -----------------
@bp.route("/admin/index/data")
def admin_index_data():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Status Counts (including Total)
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN status='Received' THEN 1 ELSE 0 END) AS received_count,
            SUM(CASE WHEN status='In Progress' THEN 1 ELSE 0 END) AS in_progress_count,
            SUM(CASE WHEN status='Resolved' THEN 1 ELSE 0 END) AS resolved_count,
            COUNT(*) AS total_count
        FROM reports
    """)
    status_data = cursor.fetchone()

    # Category Counts
    cursor.execute("""
        SELECT category, COUNT(*) AS count 
        FROM reports 
        GROUP BY category
    """)
    category_data = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({
        "status_data": status_data,
        "category_data": category_data
    })