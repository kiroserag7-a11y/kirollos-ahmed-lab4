import os
from decimal import Decimal, InvalidOperation
from functools import wraps

import bcrypt
import pymysql
import pymysql.cursors
from dotenv import load_dotenv
from flask import (Flask, redirect, render_template, request, session,
                   url_for)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")


# ---------------------------------------------------------------- database
def get_db(database="registration"):
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=database,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def run(sql, params=(), fetch=None, db="registration"):
    """Run ONE parameterised statement. fetch: None | 'one' | 'all'."""
    conn = get_db(db)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if fetch == "one":
                return cur.fetchone()
            if fetch == "all":
                return cur.fetchall()
            return cur.lastrowid
    finally:
        conn.close()


# ----------------------------------------------------------------- helpers
def pw_bytes(password):
    return password.encode("utf-8")[:72]  # bcrypt only uses 72 bytes


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


def validate_title(title):
    title = (title or "").strip()
    if not title:
        return title, ["Title is required"]
    if len(title) > 200:
        return title, ["Title is too long (200 characters at most)"]
    return title, []


# ------------------------------------------------------------------- auth
@app.route("/")
def index():
    return redirect(url_for("todos" if "user_id" in session else "login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("todos"))
    if request.method == "GET":
        return render_template("register.html", errors=[], form={})

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")

    errors = []
    if not name:
        errors.append("Name is required")
    if not email:
        errors.append("Email is required")
    if not password:
        errors.append("Password is required")
    if not confirm:
        errors.append("Confirm password is required")
    if password and confirm and password != confirm:
        errors.append("Passwords do not match")
    if errors:
        return render_template("register.html", errors=errors,
                               form={"name": name, "email": email})

    hashed = bcrypt.hashpw(pw_bytes(password), bcrypt.gensalt(12)).decode()
    try:
        user_id = run(
            "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)",
            (email[:255], name[:100], hashed),
        )
    except pymysql.err.IntegrityError as e:
        if e.args[0] == 1062:  # duplicate entry (UNIQUE email)
            return render_template("register.html",
                                   errors=["Email Already Exists"],
                                   form={"name": name, "email": email})
        raise

    session.clear()
    session["user_id"] = user_id
    session["name"] = name
    return redirect(url_for("todos"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("todos"))
    if request.method == "GET":
        return render_template("login.html", errors=[], form={})

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    errors = []
    if not email:
        errors.append("Email is required")
    if not password:
        errors.append("Password is required")
    if errors:
        return render_template("login.html", errors=errors,
                               form={"email": email})

    user = run(
        "SELECT user_id, name, password_hash FROM users WHERE email = %s",
        (email,), fetch="one",
    )
    if user and bcrypt.checkpw(pw_bytes(password),
                               user["password_hash"].encode()):
        session.clear()
        session["user_id"] = user["user_id"]
        session["name"] = user["name"]
        return redirect(url_for("todos"))

    return render_template("login.html", errors=["Invalid email or password"],
                           form={"email": email})


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


# ------------------------------------------------------------------ todos
def render_todos(add_errors=None, add_title="", todo_errors=None,
                 edit_values=None):
    rows = run(
        "SELECT todo_id, title, is_done, created_at FROM todos "
        "WHERE user_id = %s ORDER BY todo_id DESC",
        (session["user_id"],), fetch="all",
    )
    return render_template(
        "todos.html", todos=rows, add_errors=add_errors or [],
        add_title=add_title, todo_errors=todo_errors or {},
        edit_values=edit_values or {},
    )


@app.route("/todos")
@login_required
def todos():
    return render_todos()


@app.route("/todos/add", methods=["POST"])
@login_required
def add_todo():
    title, errors = validate_title(request.form.get("title"))
    if errors:
        return render_todos(add_errors=errors, add_title=request.form.get("title", ""))
    run("INSERT INTO todos (user_id, title) VALUES (%s, %s)",
        (session["user_id"], title))
    return redirect(url_for("todos"))


@app.route("/todos/<int:todo_id>/edit", methods=["POST"])
@login_required
def edit_todo(todo_id):
    title, errors = validate_title(request.form.get("title"))
    if errors:
        return render_todos(todo_errors={todo_id: errors},
                            edit_values={todo_id: request.form.get("title", "")})
    run("UPDATE todos SET title = %s WHERE todo_id = %s AND user_id = %s",
        (title, todo_id, session["user_id"]))
    return redirect(url_for("todos"))


@app.route("/todos/<int:todo_id>/toggle", methods=["POST"])
@login_required
def toggle_todo(todo_id):
    is_done = 1 if request.form.get("is_done") == "1" else 0
    run("UPDATE todos SET is_done = %s WHERE todo_id = %s AND user_id = %s",
        (is_done, todo_id, session["user_id"]))
    return redirect(url_for("todos"))


@app.route("/todos/<int:todo_id>/delete", methods=["POST"])
@login_required
def delete_todo(todo_id):
    run("DELETE FROM todos WHERE todo_id = %s AND user_id = %s",
        (todo_id, session["user_id"]))
    return redirect(url_for("todos"))


# ----------------------------------------------------------------- library
# Lab 4 / Problem 2: search queries on the database `library`.
# --- QUERIES START
SEARCH_BASE = (
    "SELECT b.book_id, b.title, b.price, b.publish_year, c.name AS category\n"
    "FROM book b JOIN category c ON b.category_id = c.category_id"
)

QUERIES = {
    # F2.1 is built from the form (placeholders); this is an example run
    "F2.1": SEARCH_BASE + "\nWHERE b.title LIKE '%murder%'\n"
            "  AND b.price BETWEEN 10 AND 20\n  AND b.category_id = 2\n"
            "ORDER BY b.price ASC, b.title",

    "F2.2": "SELECT b.book_id, b.title, b.price, b.publish_year,\n"
            "       a.name AS author, p.name AS publisher, c.name AS category\n"
            "FROM book b\n"
            "JOIN author a    ON b.author_id = a.author_id\n"
            "JOIN publisher p ON b.publisher_id = p.publisher_id\n"
            "JOIN category c  ON b.category_id = c.category_id\n"
            "ORDER BY b.book_id",

    "F2.3a": "SELECT c.category_id, c.name AS category, COUNT(*) AS books,\n"
             "       ROUND(AVG(b.price), 2) AS average_price\n"
             "FROM category c JOIN book b ON b.category_id = c.category_id\n"
             "GROUP BY c.category_id, c.name\n"
             "ORDER BY c.name",

    "F2.3b": "SELECT a.author_id, a.name AS author, COUNT(*) AS books\n"
             "FROM author a JOIN book b ON b.author_id = a.author_id\n"
             "GROUP BY a.author_id, a.name\n"
             "HAVING COUNT(*) >= 2\n"
             "ORDER BY books DESC, a.name",

    "F2.3c": "SELECT COUNT(*) AS books, SUM(price) AS total_price,\n"
             "       MIN(price) AS smallest_price, MAX(price) AS largest_price\n"
             "FROM book",

    "F2.4a": "SELECT l.loan_id, b.title AS book, m.name AS member, l.loan_date\n"
             "FROM loan l\n"
             "JOIN book b   ON l.book_id = b.book_id\n"
             "JOIN member m ON l.member_id = m.member_id\n"
             "WHERE l.return_date IS NULL\n"
             "ORDER BY l.loan_date",

    "F2.4b": "SELECT m.member_id, m.name, m.email\n"
             "FROM member m LEFT JOIN loan l ON l.member_id = m.member_id\n"
             "WHERE l.loan_id IS NULL\n"
             "ORDER BY m.name",

    "F2.4c": "SELECT b.book_id, b.title\n"
             "FROM book b LEFT JOIN loan l ON l.book_id = b.book_id\n"
             "WHERE l.loan_id IS NULL\n"
             "ORDER BY b.title",

    "F2.5a": "SELECT b.book_id, b.title, COUNT(*) AS loans\n"
             "FROM book b JOIN loan l ON l.book_id = b.book_id\n"
             "GROUP BY b.book_id, b.title\n"
             "ORDER BY loans DESC, b.title\n"
             "LIMIT 3",

    "F2.5b": "SELECT m.member_id, m.name, COUNT(*) AS loans\n"
             "FROM member m JOIN loan l ON l.member_id = m.member_id\n"
             "GROUP BY m.member_id, m.name\n"
             "ORDER BY loans DESC, m.name\n"
             "LIMIT 1",

    "F2.6a": "SELECT a.author_id, a.name AS author, a.country,\n"
             "       COUNT(b.book_id) AS books\n"
             "FROM author a LEFT JOIN book b ON b.author_id = a.author_id\n"
             "GROUP BY a.author_id, a.name, a.country\n"
             "ORDER BY books DESC, a.name",

    "F2.6b": "SELECT b.book_id, b.title, a.name AS author,\n"
             "       p.name AS publisher, a.country\n"
             "FROM book b\n"
             "JOIN author a    ON b.author_id = a.author_id\n"
             "JOIN publisher p ON b.publisher_id = p.publisher_id\n"
             "WHERE a.country = p.country\n"
             "ORDER BY b.title",
}
# --- QUERIES END


def lib(sql, params=(), fetch="all"):
    return run(sql, params, fetch, db="library")


def section(heading, key, columns, empty="Nothing to show."):
    return {"heading": heading, "columns": columns,
            "rows": lib(QUERIES[key]), "empty": empty}


def parse_price(raw, label, errors):
    if not raw:
        return None
    try:
        value = Decimal(raw)
        if (not value.is_finite() or value < 0
                or value > Decimal("99999999.99")):
            raise InvalidOperation
        return value
    except InvalidOperation:
        errors.append(label + " must be a valid number")
        return None


def escape_like(text):
    return (text.replace("\\", "\\\\").replace("%", "\\%")
            .replace("_", "\\_"))


# F2.1  search books: LIKE + BETWEEN + category, cheapest first
@app.route("/search")
@login_required
def search():
    keyword = (request.args.get("keyword") or "").strip()
    min_raw = (request.args.get("min_price") or "").strip()
    max_raw = (request.args.get("max_price") or "").strip()
    cat_raw = (request.args.get("category_id") or "").strip()
    errors = []

    min_price = parse_price(min_raw, "Minimum price", errors)
    max_price = parse_price(max_raw, "Maximum price", errors)
    if len(keyword) > 100:
        errors.append("Keyword is too long (100 characters at most)")
    category_id = None
    if cat_raw:
        try:
            category_id = int(cat_raw)
        except ValueError:
            errors.append("Choose a valid category")
    if (min_price is not None and max_price is not None
            and min_price > max_price):
        errors.append("Minimum price is greater than maximum price")

    rows = []
    if not errors:
        where, params = [], []          # placeholders, never the typed text
        if keyword:
            where.append("b.title LIKE %s")
            params.append("%" + escape_like(keyword) + "%")
        if min_price is not None and max_price is not None:
            where.append("b.price BETWEEN %s AND %s")
            params += [min_price, max_price]
        elif min_price is not None:
            where.append("b.price >= %s")
            params.append(min_price)
        elif max_price is not None:
            where.append("b.price <= %s")
            params.append(max_price)
        if category_id is not None:
            where.append("b.category_id = %s")
            params.append(category_id)
        sql = SEARCH_BASE
        if where:
            sql += "\nWHERE " + " AND ".join(where)
        sql += "\nORDER BY b.price ASC, b.title"
        rows = lib(sql, tuple(params))

    categories = lib("SELECT category_id, name FROM category "
                     "ORDER BY name")
    results = {
        "heading": "Matching books (cheapest first)",
        "columns": [("book_id", "ID"), ("title", "Title"),
                    ("price", "Price"), ("publish_year", "Year"),
                    ("category", "Category")],
        "rows": rows, "empty": "No book matches your search.",
    }
    return render_template(
        "search.html", errors=errors, categories=categories,
        results=results,
        form={"keyword": keyword, "min_price": min_raw,
              "max_price": max_raw, "category_id": cat_raw})


# F2.2  catalogue: JOIN of four tables
@app.route("/catalogue")
@login_required
def catalogue():
    cols = [("book_id", "ID"), ("title", "Title"), ("price", "Price"),
            ("publish_year", "Year"), ("author", "Author"),
            ("publisher", "Publisher"), ("category", "Category")]
    return render_template("report.html", title="Catalogue", sections=[
        section("Catalogue", "F2.2", cols, "The library has no books.")])


# F2.3  reports: GROUP BY, HAVING, aggregates
@app.route("/reports")
@login_required
def reports():
    return render_template("report.html", title="Reports", sections=[
        section("Books and average price of each category", "F2.3a",
                [("category", "Category"), ("books", "Books"),
                 ("average_price", "Average price")]),
        section("Authors who wrote at least 2 books", "F2.3b",
                [("author_id", "ID"), ("author", "Author"),
                 ("books", "Books")], "No author wrote 2 books yet."),
        section("The whole library", "F2.3c",
                [("books", "Books"), ("total_price", "Total price"),
                 ("smallest_price", "Smallest price"),
                 ("largest_price", "Largest price")]),
    ])


# F2.4  loans: JOIN and LEFT JOIN
@app.route("/loans")
@login_required
def loans():
    return render_template("report.html", title="Loans", sections=[
        section("Loans not returned yet", "F2.4a",
                [("loan_id", "Loan"), ("book", "Book"),
                 ("member", "Member"), ("loan_date", "Loan date")],
                "Every book has been returned."),
        section("Members who never borrowed a book", "F2.4b",
                [("member_id", "ID"), ("name", "Name"),
                 ("email", "Email")], "Every member has borrowed a book."),
        section("Books that were never borrowed", "F2.4c",
                [("book_id", "ID"), ("title", "Title")],
                "Every book was borrowed at least once."),
    ])


# F2.5  most borrowed: GROUP BY, ORDER BY, LIMIT
@app.route("/top")
@login_required
def top():
    return render_template("report.html", title="Most borrowed", sections=[
        section("The 3 most borrowed books", "F2.5a",
                [("book_id", "ID"), ("title", "Title"),
                 ("loans", "Loans")], "There are no loans yet."),
        section("The member with the most loans", "F2.5b",
                [("member_id", "ID"), ("name", "Name"),
                 ("loans", "Loans")], "There are no loans yet."),
    ])


# F2.6  authors and books: LEFT JOIN, JOIN
@app.route("/authors-books")
@login_required
def authors_books():
    return render_template("report.html", title="Authors and books", sections=[
        section("Every author with the number of books", "F2.6a",
                [("author_id", "ID"), ("author", "Author"),
                 ("country", "Country"), ("books", "Books")]),
        section("Books whose author and publisher share a country", "F2.6b",
                [("book_id", "ID"), ("title", "Title"),
                 ("author", "Author"), ("publisher", "Publisher"),
                 ("country", "Country")], "No such book."),
    ])


# ---------------------------------------------------------- friendly errors
@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404,
                           message="Page not found."), 404


@app.errorhandler(405)
def not_allowed(_):
    return render_template("error.html", code=405,
                           message="This action is not allowed."), 405


@app.errorhandler(500)
def server_error(_):
    return render_template("error.html", code=500,
                           message="Something went wrong. Please try again."), 500


if __name__ == "__main__":
    app.run(debug=False, port=5000)
