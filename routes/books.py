from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from mysql.connector import Error as DatabaseError
from mysql.connector import errorcode

from db.database import execute, fetch_all, fetch_one, get_connection

books_bp = Blueprint("books", __name__, url_prefix="/books")


@books_bp.route("/")
def list_books():
    search = request.args.get("q", "").strip()

    books = fetch_all("""
        SELECT b.book_id, b.title, b.author, b.publication_year, b.cover_image,
               COUNT(c.copy_id) AS total_copies,
               COALESCE(SUM(c.status = 'available'), 0) AS available_copies
        FROM books b
        LEFT JOIN book_copies c ON c.book_id = b.book_id
        WHERE b.title LIKE %s OR b.author LIKE %s OR b.isbn LIKE %s
        GROUP BY b.book_id
        ORDER BY b.title
    """, (f"%{search}%", f"%{search}%", f"%{search}%"))

    return render_template("books/list.html", books=books, search=search)


@books_bp.route("/<int:book_id>")
def book_detail(book_id):
    book = fetch_one("SELECT * FROM books WHERE book_id = %s", (book_id,))
    if book is None:
        abort(404)

    # Per ogni copia mostriamo anche chi la ha in prestito (se è in prestito)
    copies = fetch_all("""
        SELECT c.copy_id, c.acquisition_date, c.status,
               l.loan_id, l.due_date, m.first_name, m.last_name
        FROM book_copies c
        LEFT JOIN loans l ON l.copy_id = c.copy_id AND l.return_date IS NULL
        LEFT JOIN members m ON m.member_id = l.member_id
        WHERE c.book_id = %s
        ORDER BY c.copy_id
    """, (book_id,))

    return render_template("books/detail.html", book=book, copies=copies, today=date.today())


@books_bp.route("/new", methods=["GET", "POST"])
def new_book():
    if request.method == "GET":
        return render_template("books/new.html", form={})

    form = request.form
    title = form.get("title", "").strip()
    author = form.get("author", "").strip()
    isbn = form.get("isbn", "").strip() or None
    year = form.get("publication_year", "").strip()
    cover_image = form.get("cover_image", "").strip() or None
    copies = form.get("copies", "1").strip()

    errors = []
    if not title:
        errors.append("Il titolo è obbligatorio.")
    if not author:
        errors.append("L'autore è obbligatorio.")
    if year and not (year.isdigit() and int(year) <= date.today().year):
        errors.append("L'anno di pubblicazione non è valido.")
    if not (copies.isdigit() and 0 <= int(copies) <= 50):
        errors.append("Il numero di copie deve essere tra 0 e 50.")

    if errors:
        for message in errors:
            flash(message, "error")
        return render_template("books/new.html", form=form)

    # Libro e copie vengono inseriti in un'unica transazione
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO books (isbn, title, author, publication_year, cover_image)
            VALUES (%s, %s, %s, %s, %s)
        """, (isbn, title, author, int(year) if year else None, cover_image))
        book_id = cursor.lastrowid

        for _ in range(int(copies)):
            cursor.execute("""
                INSERT INTO book_copies (book_id, acquisition_date, status)
                VALUES (%s, CURDATE(), 'available')
            """, (book_id,))

        connection.commit()
    except DatabaseError as error:
        connection.rollback()
        if error.errno == errorcode.ER_DUP_ENTRY:
            flash("Esiste già un libro con questo ISBN.", "error")
            return render_template("books/new.html", form=form)
        raise
    finally:
        connection.close()

    flash(f"Libro \"{title}\" aggiunto al catalogo.", "success")
    return redirect(url_for("books.book_detail", book_id=book_id))


@books_bp.route("/<int:book_id>/copies", methods=["POST"])
def add_copy(book_id):
    execute("""
        INSERT INTO book_copies (book_id, acquisition_date, status)
        VALUES (%s, CURDATE(), 'available')
    """, (book_id,))
    flash("Nuova copia aggiunta.", "success")
    return redirect(url_for("books.book_detail", book_id=book_id))


@books_bp.route("/copies/<int:copy_id>/withdraw", methods=["POST"])
def withdraw_copy(copy_id):
    copy = fetch_one("SELECT book_id, status FROM book_copies WHERE copy_id = %s", (copy_id,))
    if copy is None:
        abort(404)

    if copy["status"] == "available":
        execute("UPDATE book_copies SET status = 'withdrawn' WHERE copy_id = %s", (copy_id,))
        flash(f"Copia #{copy_id} ritirata dal prestito.", "success")
    else:
        flash("Si possono ritirare solo le copie disponibili.", "error")

    return redirect(url_for("books.book_detail", book_id=copy["book_id"]))
