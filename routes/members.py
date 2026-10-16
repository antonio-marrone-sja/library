from flask import Blueprint, flash, redirect, render_template, request, url_for
from mysql.connector import Error as DatabaseError
from mysql.connector import errorcode

from db.database import execute, fetch_all

members_bp = Blueprint("members", __name__, url_prefix="/members")


def get_members(search):
    return fetch_all("""
        SELECT m.member_id, m.first_name, m.last_name, m.email, m.registration_date,
               COUNT(l.loan_id) AS active_loans
        FROM members m
        LEFT JOIN loans l ON l.member_id = m.member_id AND l.return_date IS NULL
        WHERE CONCAT(m.first_name, ' ', m.last_name) LIKE %s OR m.email LIKE %s
        GROUP BY m.member_id
        ORDER BY m.last_name, m.first_name
    """, (f"%{search}%", f"%{search}%"))


@members_bp.route("/", methods=["GET", "POST"])
def list_members():
    search = request.args.get("q", "").strip()

    if request.method == "GET":
        return render_template("members/list.html", members=get_members(search), search=search, form={})

    form = request.form
    first_name = form.get("first_name", "").strip()
    last_name = form.get("last_name", "").strip()
    email = form.get("email", "").strip().lower()

    if not first_name or not last_name or "@" not in email:
        flash("Compila nome, cognome e un'email valida.", "error")
        return render_template("members/list.html", members=get_members(search), search=search, form=form)

    try:
        execute("""
            INSERT INTO members (first_name, last_name, email, registration_date)
            VALUES (%s, %s, %s, CURDATE())
        """, (first_name, last_name, email))
    except DatabaseError as error:
        if error.errno == errorcode.ER_DUP_ENTRY:
            flash("Esiste già un socio con questa email.", "error")
            return render_template("members/list.html", members=get_members(search), search=search, form=form)
        raise

    flash(f"Socio {first_name} {last_name} registrato.", "success")
    return redirect(url_for("members.list_members"))