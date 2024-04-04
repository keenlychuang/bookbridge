import requests 
import pytest
from typing import Literal, Optional 
from bookbridge.utils import *

# Test the Book class initialization
def test_book_initialization():
    book = Book("Sample Title", "Author Name", "fiction", True, "Sample blurb", 4.5)
    assert book.title == "Sample Title"
    assert book.author == "Author Name"
    assert book.genre == "fiction"
    assert book.completed is True
    assert book.blurb == "Sample blurb"
    assert book.rating == 4.5
    # assert book.notes == "Sample notes"

def test_book_autofill(): 
    book = Book("Crime and Punishment")
    expected_author = "Fyodor Dostoevsky"
    expected_genre = "fiction"
    book.llm_autofill() 
    assert book.author == expected_author
    assert book.genre == expected_genre
    assert isinstance(book.blurb, str)
    print(book)

def test_llm_api_call():
    prompt = "Your task to return a critique of surveillance captialism and its impact on society."
    response = llm_api_call(prompt)
    print(f"llm api call produced the following test response:\n{response}")
    assert isinstance(response, str)

def test_parse_csv_response():
    with open('data/test/synthetic_booklists/sample.csv', 'r') as file:
        output = file.read()
    books = parse_csv_response(output)
    for book in books:
        assert isinstance(book, Book)

# def test_generate_processing_prompt(): 
#     string = extract_text_from_pdf("data/test/synthetic_booklists/test_booklist_5.pdf")
#     prompt = generate_processing_prompt(string)
#     print("generated the following processing prompt: ")
#     print(prompt)

def test_bookstring_to_csv(): 
    with open("data/test/synthetic_booklists/sample_booklist.txt", 'r') as file: 
        string = file.read() 
    csv = bookstring_to_csv(string)
    print(csv)
    assert is_valid_csv(csv)

def test_extract_text_from_pdf():
    path = "data/test/synthetic_booklists/test_booklist_5.pdf"
    string = extract_text_from_pdf(path)
    print("Does this look like a good booklist?\n----------")
    print(string)
    print("----------")

#stil failing
def test_pdf_to_bookslist():
    path = "data/test/synthetic_booklists/test_booklist_5.pdf"
    books = pdf_to_booklist(path)
    assert len(books) == 5


# def test_generate_sample_booklist():
#     num_books = 10 
#     path = "data/test/book_titles/reddit_titles.txt"
#     booklist_string = generate_sample_booklist(num_books, path=path)
    
#     # assert that the string is not empty
#     assert booklist_string != ""

#     num_books = 0 
#     booklist_string = generate_sample_booklist(num_books, path=path)
#     # assert that the string is empty
#     assert booklist_string == ""

def test_autofill():
    book = Book("Animal Farm")
    book.llm_autofill()

    # assert proper formatting on first three fields 
    assert book.title == "Animal Farm"
    assert book.author == "George Orwell"
    assert book.genre == "fiction"
    assert book.completed is not None

    # doesn't matter which blurb, should not complete other fields
    assert book.blurb is not None
    assert book.rating is None              
    # assert book.notes is None

def test_pretty_print():
    book = Book("Sample Title", "Author Name", "fiction", True, "Sample blurb", 4.5)
    print(book)

if __name__ == "__main__":
    pytest.main()