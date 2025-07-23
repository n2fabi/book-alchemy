from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

class Author(db.Model):
    __tablename__ = 'authors'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    date_of_death = db.Column(db.Date, nullable=True)

    def __repr__(self):
        return f"<Author {self.name} (ID: {self.id})>"

    def __str__(self):
        death = self.date_of_death.strftime('%Y-%m-%d') if self.date_of_death else "Present"
        return f"{self.name} (Born: {self.birth_date.strftime('%Y-%m-%d')}, Died: {death})"

class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.BigInteger, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    publication_year = db.Column(db.Integer, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'), nullable=False)
    cover_url = db.Column(db.String(255), nullable=True)

    # Relationship to Author
    author = db.relationship("Author", backref="books")

    def __repr__(self):
        return f"<Title {self.title} by {self.author.name} (ID: {self.id})>"

    def __str__(self):
        return f"{self.id} written in {self.publication_year} by {self.author.name} (isbn: {self.isbn})"
