"""
Exercise 4: Mini-Project - Library Management System
=====================================================
Combine everything: functions, classes, files, and JSON

This exercise brings together all the concepts from the course.
Build a simple library system that tracks books and borrowers.

Instructions:
- Complete all TODOs
- The system should persist data to JSON files
- Run this file to test your implementation

Run with: python exercise_4_project.py
"""

import json
import os
from datetime import datetime


# =============================================================================
# PART 1: HELPER FUNCTIONS
# =============================================================================

def format_date(dt: datetime = None) -> str:
    """
    Format a datetime object as a string "YYYY-MM-DD".
    If no datetime is provided, use the current date.

    Example:
        format_date(datetime(2024, 1, 15)) -> "2024-01-15"
        format_date() -> "2024-02-04" (today's date)
    """
    return f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}" if dt else format_date(datetime.today())


def generate_id(prefix: str, existing_ids: list) -> str:
    """
    Generate a new unique ID with the given prefix.

    Parameters:
        prefix: String prefix (e.g., "BOOK", "USER")
        existing_ids: List of existing IDs to avoid duplicates

    Returns:
        New ID in format "{prefix}_{number:04d}"

    Example:
        generate_id("BOOK", ["BOOK_0001", "BOOK_0002"]) -> "BOOK_0003"
        generate_id("USER", []) -> "USER_0001"
    """
    existing_ids.sort()
    new_id = 1 if not existing_ids else int(existing_ids[-1][-4:]) + 1
    return f"{prefix}_{new_id:04d}"


def search_items(items: list, **criteria) -> list:
    """
    Search a list of dictionaries by matching criteria.
    Uses **kwargs to accept any search fields.

    Parameters:
        items: List of dictionaries to search
        **criteria: Field-value pairs to match (case-insensitive for strings)

    Returns:
        List of matching items

    Example:
        books = [
            {"title": "Python 101", "author": "Smith"},
            {"title": "Java Guide", "author": "Smith"},
            {"title": "Python Advanced", "author": "Jones"}
        ]
        search_items(books, author="Smith") -> [first two books]
        search_items(books, title="Python 101") -> [first book]
    """
    result_list = []
    for item in items:
        match = True
        for key, value in criteria.items():
            if key not in item or item[key].lower() != value.lower():
                match = False
        if match: result_list.append(item)
    return result_list


# =============================================================================
# PART 2: BOOK CLASS
# =============================================================================

class Book:
    """
    Represents a book in the library.

    Class Attributes:
        GENRES: List of valid genres ["Fiction", "Non-Fiction", "Science", "History", "Technology"]

    Instance Attributes:
        book_id (str): Unique identifier
        title (str): Book title
        author (str): Author name
        genre (str): Must be one of GENRES
        available (bool): Whether book is available for borrowing

    Methods:
        to_dict(): Convert to dictionary for JSON serialization
        from_dict(data): Class method to create Book from dictionary
        __str__(): Return readable string representation
    """

    GENRES = ["Fiction", "Non-Fiction", "Science", "History", "Technology"]

    def __init__(self, book_id: str, title: str, author: str, genre: str, available: bool = True):
        if genre in self.GENRES: self.genre = genre
        else: raise ValueError(f"Invalid genre '{genre}'. Accepted genres: {self.GENRES}")
        self.book_id = book_id
        self.title = title
        self.author = author
        self.available = available

    def to_dict(self) -> dict:
        return {"book_id": self.book_id, "title": self.title, "author": self.author, "genre": self.genre, "available": self.available}

    @classmethod
    def from_dict(cls, data: dict) -> "Book":
        return Book(data["book_id"], data["title"], data["author"], data["genre"], data["available"])

    def __str__(self) -> str:
        return f"[{self.book_id}] {self.title} by {self.author} ({self.genre}) - {self.available}"


# =============================================================================
# PART 3: BORROWER CLASS
# =============================================================================

class Borrower:
    """
    Represents a library member who can borrow books.

    Instance Attributes:
        borrower_id (str): Unique identifier
        name (str): Borrower's name
        email (str): Borrower's email
        borrowed_books (list): List of book_ids currently borrowed

    Methods:
        borrow_book(book_id): Add book to borrowed list
        return_book(book_id): Remove book from borrowed list
        to_dict(): Convert to dictionary
        from_dict(data): Class method to create Borrower from dictionary
    """

    MAX_BOOKS = 3  # Maximum books a borrower can have at once

    def __init__(self, borrower_id: str, name: str, email: str, borrowed_books: list = None):
        self.borrower_id = borrower_id
        self.name = name
        self.email = email
        self.borrowed_books = borrowed_books or []

    def can_borrow(self) -> bool:
        """Check if borrower can borrow more books."""
        return len(self.borrowed_books) < self.MAX_BOOKS

    def borrow_book(self, book_id: str) -> bool:
        """Add book to borrowed list. Return False if at max limit."""
        if self.can_borrow():
            self.borrowed_books.append(book_id)
            return True
        return False

    def return_book(self, book_id: str) -> bool:
        """Remove book from borrowed list. Return False if not found."""
        if book_id in self.borrowed_books:
            self.borrowed_books.remove(book_id)
            return True
        return False

    def to_dict(self) -> dict:
        return {"borrower_id": self.borrower_id, "name": self.name, "email": self.email, "borrowed_books": self.borrowed_books}

    @classmethod
    def from_dict(cls, data: dict) -> "Borrower":
        return Borrower(data["borrower_id"], data["name"], data["email"], data["borrowed_books"])


# =============================================================================
# PART 4: LIBRARY CLASS (Main System)
# =============================================================================

class Library:
    """
    Main library system that manages books and borrowers.
    Persists data to JSON files.

    Attributes:
        name (str): Library name
        books (dict): book_id -> Book
        borrowers (dict): borrower_id -> Borrower
        books_file (str): Path to books JSON file
        borrowers_file (str): Path to borrowers JSON file

    Methods:
        add_book(title, author, genre) -> Book: Add a new book
        add_borrower(name, email) -> Borrower: Add a new borrower
        checkout_book(book_id, borrower_id) -> bool: Borrower checks out a book
        return_book(book_id, borrower_id) -> bool: Borrower returns a book
        search_books(**criteria) -> list: Search books by criteria
        get_available_books() -> list: Get all available books
        get_borrower_books(borrower_id) -> list: Get books borrowed by a borrower
        save(): Save all data to JSON files
        load(): Load data from JSON files
    """

    def __init__(self, name: str, data_dir: str = "."):
        self.name = name
        self.books = {}
        self.borrowers = {}
        self.books_file = os.path.join(data_dir, "library_books.json")
        self.borrowers_file = os.path.join(data_dir, "library_borrowers.json")
        self.load()

    def load(self) -> None:
        """Load books and borrowers from JSON files."""
        try:
            with open(self.books_file, "r", encoding="utf-8") as f:
                self.books = json.load(f)
        except FileNotFoundError: pass

        try:
            with open(self.borrowers_file, "r", encoding="utf-8") as f:
                self.borrowers = json.load(f)
        except FileNotFoundError: pass

    def save(self) -> None:
        """Save books and borrowers to JSON files."""
        books = {book_id: book.to_dict() for book_id, book in self.books.items()}
        with open(self.books_file, "w", encoding="utf-8") as f:
            json.dump(books, f, indent=2)

        borrowers = {borrower_id: borrower.to_dict() for borrower_id, borrower in self.borrowers.items()}
        with open(self.borrowers_file, "w", encoding="utf-8") as f:
            json.dump(borrowers, f, indent=2)

    def add_book(self, title: str, author: str, genre: str) -> Book:
        """Add a new book to the library."""
        new_book = Book(generate_id("BOOK", list(self.books.keys())), title, author, genre)
        self.books[new_book.book_id] = new_book
        self.save()
        return new_book

    def add_borrower(self, name: str, email: str) -> Borrower:
        """Register a new borrower."""
        new_borrower = Borrower(generate_id("USER", list(self.borrowers.keys())), name, email)
        self.borrowers[new_borrower.borrower_id] = new_borrower
        self.save()
        return new_borrower

    def checkout_book(self, book_id: str, borrower_id: str) -> bool:
        """
        Borrower checks out a book.
        Returns False if book unavailable, borrower not found, or at max limit.
        """
        if book_id not in self.books or not self.books[book_id].available: return False
        if borrower_id not in self.borrowers or not self.borrowers[borrower_id].can_borrow(): return False
        self.borrowers[borrower_id].borrow_book(book_id)
        self.books[book_id].available = False
        self.save()
        return True

    def return_book(self, book_id: str, borrower_id: str) -> bool:
        """
        Borrower returns a book.
        Returns False if book/borrower not found or book wasn't borrowed by this person.
        """
        if book_id not in self.books or borrower_id not in self.borrowers: return False
        if book_id not in self.borrowers[borrower_id].borrowed_books: return False
        self.borrowers[borrower_id].return_book(book_id)
        self.books[book_id].available = True
        self.save()
        return True

    def search_books(self, **criteria) -> list:
        """Search books by any criteria (title, author, genre, available)."""
        booklist = [book.to_dict() for book in self.books.values()]
        return search_items(booklist, **criteria)

    def get_available_books(self) -> list:
        """Get list of all available books."""
        available_books = []
        for book in self.books.values():
            if book.available: available_books.append(book)
        return available_books

    def get_borrower_books(self, borrower_id: str) -> list:
        """Get list of books currently borrowed by a borrower."""
        return self.borrowers[borrower_id].borrowed_books

    def get_statistics(self) -> dict:
        """
        Return library statistics.
        Uses the concepts of dict comprehension and aggregation.
        """
        total = len(self.books)
        available = len(self.get_available_books())
        genre_counts = {}
        for book in self.books.values():
            genre_counts[book.genre] = genre_counts.get(book.genre, 0) + 1
        return {
            'total_books': total,
            'available_books': available,
            'checked_out': total - available,
            'total_borrowers': len(self.borrowers),
            'books_by_genre': genre_counts
        }