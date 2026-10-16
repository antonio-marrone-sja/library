from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from mysql.connector import Error as DatabaseError

from db.database import execute, fetch_all

loans_bp = Blueprint("loans", __name__, url_prefix="/loans")

LOAN_DAYS = 30

# Codice di errore restituito da MySQL quando un trigger esegue SIGNAL SQLSTATE '45000'
TRIGGER_ERROR = 1644

FILTERS = {
    "active": "l.return_date IS NULL",
    "overdue": "l.return_date IS NULL AND l.due_date < CURDATE()",
    "returned": "l.return_date IS NOT NULL",
    "all": "TRUE",
}


@loans_bp.route("/")
def list_loans():
    current_filter = request.args.get("filter", "active")
    if current_filter not in FILTERS:
        current_filter = "active"

    # La condizione viene scelta da un dizionario fisso, mai dall'input dell'utente
    loans = fetch_all(f"""
        SELECT l.loan_id, l.copy_id, l.loan_date, l.due_date, l.return_date,
               b.book_id, b.title, m.first_name, m.last_name
        FROM loans l
        JOIN book_copies c ON c.copy_id = l.copy_id
        JOIN books b ON b.book_id = c.book_id
        JOIN members m ON m.member_id = l.member_id
        WHERE {FILTERS[current_filter]}
        ORDER BY l.return_date IS NOT NULL, l.due_date
    """)

    return render_template("loans/list.html", loans=loans, current_filter=current_filter, today=date.today())


def render_new_loan_form(form):
    members = fetch_all("""
        SELECT member_id, first_name, last_name, email
        FROM members
        ORDER BY last_name, first_name
    """)
    copies = fetch_all("""
        SELECT c.copy_id, b.title, b.author
        FROM book_copies c
        JOIN books b ON b.book_id = c.book_id
        WHERE c.status = 'available'
        ORDER BY b.title, c.copy_id
    """)
    today = date.today()
    return render_template(
        "loans/new.html",
        members=members,
        copies=copies,
        form=form,
        today=today.isoformat(),
        default_due=(today + timedelta(days=LOAN_DAYS)).isoformat(),
    )


@loans_bp.route("/new", methods=["GET", "POST"])
def new_loan():
    if request.method == "GET":
        # Dalla pagina del libro si può arrivare qui con la copia già selezionata
        return render_new_loan_form({"copy_id": request.args.get("copy_id", "")})

    form = request.form
    member_id = form.get("member_id", "")
    copy_id = form.get("copy_id", "")
    due_date = form.get("due_date", "")

    try:
        due = date.fromisoformat(due_date)
    except ValueError:
        due = None

    if not member_id.isdigit() or not copy_id.isdigit() or due is None:
        flash("Seleziona socio, copia e data di scadenza.", "error")
        return render_new_loan_form(form)

    if due < date.today():
        flash("La data di scadenza non può essere nel passato.", "error")
        return render_new_loan_form(form)

    try:
        execute("""
            INSERT INTO loans (copy_id, member_id, loan_date, due_date)
            VALUES (%s, %s, CURDATE(), %s)
        """, (int(copy_id), int(member_id), due))
    except DatabaseError as error:
        # Il trigger check_copy_availability blocca le copie non disponibili
        if error.errno == TRIGGER_ERROR:
            flash(error.msg, "error")
            return render_new_loan_form(form)
        raise

    flash("Prestito registrato.", "success")
    return redirect(url_for("loans.list_loans"))


@loans_bp.route("/<int:loan_id>/return", methods=["POST"])
def return_loan(loan_id):
    # Il trigger update_copy_status_after_return rende di nuovo disponibile la copia
    execute("""
        UPDATE loans
        SET return_date = CURDATE()
        WHERE loan_id = %s AND return_date IS NULL
    """, (loan_id,))
    flash("Restituzione registrata: la copia è di nuovo disponibile.", "success")
    return redirect(request.referrer or url_for("loans.list_loans"))