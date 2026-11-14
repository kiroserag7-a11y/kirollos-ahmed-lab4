# Lab 4 - Search Queries in SQL (Problem 2: Library)

## Team
| Name | ID | Did what |
|------|----|----------|
| Kirollose Serag Mouner | 2304102 | `problem2_DDL.sql`, `problem2_DML.sql`, SQL queries (`problem2_Queries.sql`) |
| Ahmed Ramdan Mohamed | 2304109 | website pages F2.1-F2.6, README |

## Contents
| File | What it is |
|------|------------|
| `problem2_DDL.sql` | Database `library`: 6 tables (author, publisher, category, book, member, loan), primary keys, foreign keys, `ON DELETE CASCADE` (author -> book, book -> loan) |
| `problem2_DML.sql` | Seed data: 5 authors, 3 publishers, 3 categories, 10 books, 5 members, 12 loans |
| `problem2_Queries.sql` | The SQL of the pages F2.1-F2.6, each query has a `-- F2.x` comment |
| `website/` | The website (login + to-do from Lab 2) with the new search pages |

## Technology
Python 3 + Flask, PyMySQL (plain SQL, no ORM), bcrypt, HTML/Jinja2, CSS, JavaScript, MySQL 8.

## How to run (from an empty machine)
1. Install Python 3.10+ and MySQL 8.
2. Build the databases (run from this folder):
   ```bash
   mysql -u root -p < website/database/schema.sql   # login database: registration
   mysql -u root -p < problem2_DDL.sql              # library database + 6 tables
   mysql -u root -p < problem2_DML.sql              # seed data
   mysql -u root -p < problem2_Queries.sql          # (optional) run all page queries by hand
   ```
3. Set up the website:
   ```bash
   cd website
   pip install -r requirements.txt
   cp .env.example .env      # on Windows: copy .env.example .env
   ```
   Open `.env` and write your MySQL password and any long random `SECRET_KEY`.
4. Start the server and open <http://localhost:5000>:
   ```bash
   python app.py
   ```
5. Register or log in. The top bar links to the new pages.

## Pages
| Page | Address | SQL features |
|------|---------|--------------|
| F2.1 Search books | `/search` | `WHERE`, `LIKE`, `BETWEEN`, category, `ORDER BY price` |
| F2.2 Catalogue | `/catalogue` | `JOIN` of book, author, publisher, category |
| F2.3 Reports | `/reports` | `GROUP BY`, `HAVING`, `COUNT`, `AVG`, `SUM`, `MIN`, `MAX` |
| F2.4 Loans | `/loans` | `JOIN`, `LEFT JOIN ... IS NULL` |
| F2.5 Most borrowed | `/top` | `GROUP BY`, `ORDER BY`, `LIMIT` |
| F2.6 Authors and books | `/authors-books` | `LEFT JOIN`, `JOIN` |

## Bonus
**Prepared statements in F2.1 (search books).** The search form uses placeholders (`%s`) for the keyword, the minimum and
maximum price and the category: the values typed by the user are sent to MySQL separately and are never glued into the
SQL text. The `%` and `_` typed in the keyword are escaped, so they are treated as normal characters.
See the `search()` function in `website/app.py`.

All pages need a logged-in user.
