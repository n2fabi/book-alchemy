from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from data_models import db, Author, Book
import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import or_

load_dotenv()  # .env-Datei laden


app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["DEBUG"] = True
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data', 'library.sqlite')}"


db.init_app(app)

@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    if request.method == 'POST':
        authors = []

        if request.is_json:
            data = request.get_json()

            # Falls mehrere Autoren gesendet werden
            if isinstance(data, list):
                authors = data
            else:
                authors = [data]
        else:
            # Daten aus HTML-Formular
            authors = [{
                "name": request.form.get('name'),
                "birth_date": request.form.get('birth_date'),
                "date_of_death": request.form.get('date_of_death')
            }]

        for author_data in authors:
            name = author_data.get('name')
            birth_date_str = author_data.get('birth_date')
            date_of_death_str = author_data.get('date_of_death')

            if not name or not birth_date_str:
                flash("Author name and birth date are required.", "error")
                continue  # zum nächsten Autor

            try:
                birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
            except ValueError:
                flash(f"Invalid birth date format for '{name}'. Use YYYY-MM-DD.", "error")
                continue

            try:
                date_of_death = datetime.strptime(date_of_death_str, "%Y-%m-%d").date() if date_of_death_str else None
            except ValueError:
                flash(f"Invalid date of death format for '{name}'. Use YYYY-MM-DD.", "error")
                continue

            new_author = Author(
                name=name,
                birth_date=birth_date,
                date_of_death=date_of_death
            )

            db.session.add(new_author)
            flash(f"Author '{name}' added successfully!", "success")

        db.session.commit()
        return redirect('/add_author')

    return render_template('add_author.html')


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()

            # Liste von Büchern
            if isinstance(data, list):
                success_count = 0
                print("Liste kommt an")
                for item in data:
                    isbn = item.get('isbn')
                    title = item.get('title')
                    publication_year = item.get('publication_year')
                    author_id = item.get('author_id')

                    if not all([isbn, title, publication_year, author_id]):
                        continue  # skip invalid entries

                    # Cover-URL automatisch aus Open Library Covers API holen
                    cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"

                    # Buch anlegen
                    try:
                        new_book = Book(
                            isbn=int(isbn),
                            title=title,
                            publication_year=int(publication_year),
                            author_id=int(author_id),
                            cover_url=cover_url
                        )
                        db.session.add(new_book)
                        success_count += 1
                    except Exception as e:
                        continue  # skip problematic entries

                db.session.commit()
                return {"message": f"{success_count} books added successfully."}, 201

            # Einzelnes Buch (kein Array, sondern ein Dict)
            else:
                isbn = data.get('isbn')
                title = data.get('title')
                publication_year = data.get('publication_year')
                author_id = data.get('author_id')

                if not all([isbn, title, publication_year, author_id]):
                    return {"error": "All fields are required."}, 400

                # Cover-URL automatisch aus Open Library Covers API holen
                cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"

                # Optional: Prüfen, ob das Bild existiert (Statuscode 200)
                try:
                    resp = request.head(cover_url)
                    if resp.status_code != 200:
                        cover_url = None  # Kein Bild gefunden
                except Exception as e:
                    cover_url = None

                # Buch anlegen
                try:
                    new_book = Book(
                        isbn=int(isbn),
                        title=title,
                        publication_year=int(publication_year),
                        author_id=int(author_id),
                        cover_url=cover_url
                    )
                    db.session.add(new_book)
                    db.session.commit()
                    return {"message": f"Book '{title}' added successfully!"}, 201
                except Exception as e:
                    return {"error": str(e)}, 500

        else:
            # Standard-Formular POST (HTML)
            isbn = request.form.get('isbn')
            title = request.form.get('title')
            publication_year = request.form.get('publication_year')
            author_id = request.form.get('author_id')

            if not all([isbn, title, publication_year, author_id]):
                flash("All fields are required.", "error")
                return redirect('/add_book')

            # Cover-URL automatisch aus Open Library Covers API holen
            cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"

            # Optional: Prüfen, ob das Bild existiert (Statuscode 200)
            try:
                resp = request.head(cover_url)
                if resp.status_code != 200:
                    cover_url = None  # Kein Bild gefunden
            except Exception as e:
                cover_url = None

            # Buch anlegen
            try:
                new_book = Book(
                    isbn=int(isbn),
                    title=title,
                    publication_year=int(publication_year),
                    author_id=int(author_id),
                    cover_url=cover_url
                )
                db.session.add(new_book)
                db.session.commit()
                flash(f"Book '{title}' added successfully!", "success")
            except Exception as e:
                flash(f"Error adding book: {e}", "error")

            return redirect('/add_book')

    # GET method: load list of authors
    authors = Author.query.all()
    return render_template('add_book.html', authors=authors)

@app.route('/')
def home():
    sort_by = request.args.get('sort', 'title')
    search_query = request.args.get('q', '').strip()

    query = Book.query.join(Author)

    if search_query:
        # Suche in Titel und Autorname
        query = query.filter(
            or_(
                Book.title.ilike(f"%{search_query}%"),
                Author.name.ilike(f"%{search_query}%")
            )
        )

    # Sortierung anwenden
    if sort_by == 'author':
        query = query.order_by(Author.name)
    else:
        query = query.order_by(Book.title)

    books = query.all()

    # Meldung, falls keine Treffer
    no_results = (len(books) == 0 and search_query != "")

    return render_template('home.html', books=books, sort_by=sort_by, no_results=no_results, search_query=search_query)

@app.route('/book/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    author = book.author

    # Buch löschen
    db.session.delete(book)
    db.session.commit()

    # Prüfen, ob der Autor noch andere Bücher hat
    other_books = Book.query.filter_by(author_id=author.id).count()
    if other_books == 0:
        db.session.delete(author)
        db.session.commit()
        flash(f"Book '{book.title}' and its author '{author.name}' were deleted.", "success")
    else:
        flash(f"Book '{book.title}' was deleted.", "success")

    return redirect(url_for('home'))


with app.app_context():
  db.create_all()


