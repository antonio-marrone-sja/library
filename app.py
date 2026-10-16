import os

from dotenv import load_dotenv
from flask import Flask, render_template
from mysql.connector import Error as DatabaseError

from db.database import fetch_one
from routes.books import books_bp
from routes.loans import loans_bp
from routes.members import members_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev")

app.register_blueprint(books_bp)
app.register_blueprint(members_bp)
app.register_blueprint(loans_bp)


STATUS_LABELS = {
    "available": "Disponibile",
    "on_loan": "In prestito",
    "withdrawn": "Ritirata",
}


@app.template_filter("date_it")
def date_it(value):
    """Formatta una data come gg/mm/aaaa."""
    return value.strftime("%d/%m/%Y") if value else "—"


@app.template_filter("status_label")
def status_label(value):
    return STATUS_LABELS.get(value, value)


@app.errorhandler(DatabaseError)
def database_error(error):
    return render_template("error.html", error=error), 500


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", error="Pagina non trovata."), 404


@app.route("/")
def index():
    stats = fetch_one("""
        SELECT
            (SELECT COUNT(*) FROM books) AS books,
            (SELECT COUNT(*) FROM book_copies WHERE status = 'available') AS available_copies,
            (SELECT COUNT(*) FROM members) AS members,
            (SELECT COUNT(*) FROM loans WHERE return_date IS NULL) AS active_loans,
            (SELECT COUNT(*) FROM loans
              WHERE return_date IS NULL AND due_date < CURDATE()) AS overdue_loans
    """)

    return render_template("index.html", stats=stats)


if __name__ == "__main__":
    app.run(debug=True)
