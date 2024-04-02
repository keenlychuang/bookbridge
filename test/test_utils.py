import requests 
import pytest
from typing import Literal, Optional 
from utils import *

# Test the Book class initialization
def test_book_initialization():
    book = Book("Sample Title", "Author Name", "fiction", True, "Sample blurb", 4.5, "Sample notes")
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

@pytest.mark.skip(reason="Not implemented yet")
def test_parse_response():
    prompt = generate_processing_prompt("booklist")
    # assert len(parse_response("API response")) == expected_number_of_books
    pass

def test_csv_string_to_books(): 
    path = "data/test/synthetic_booklists/test_csv.txt" 
    with open(path, 'r') as file: 
        csv_string = file.read()
    print(csv_string)
    books = string_to_books(csv_string)

    for book in books:
        assert type(book) == Book 
        print(book)
    pass 

def test_generate_processing_prompt(): 
    string = extract_text_from_pdf("data/test/synthetic_booklists/test_booklist_5.txt")
    prompt = generate_processing_prompt(string)
    print("generated the following processing prompt: ")
    print(prompt)

def test_string_to_books():
    path = "data/test/synthetic_booklists/test_booklist_5.txt"
    string = extract_text_from_pdf(path)
    books = parse_response(string)
    assert len(books) == 5

def test_generate_sample_booklist():
    num_books = 10 
    path = "data/test/book_titles/reddit_titles.txt"
    booklist_string = generate_sample_booklist(num_books, path=path)
    
    # assert that the string is not empty
    assert booklist_string != ""

    num_books = 0 
    booklist_string = generate_sample_booklist(num_books, path=path)
    # assert that the string is empty
    assert booklist_string == ""

def test_autofill():
    book = Book("The Three Body Problem")
    book.autofill()

    # assert proper formatting on first three fields 
    assert book.title == "The Three Body Problem"
    assert book.author == "Cixin Liu"
    assert book.genre == "science fiction"
    assert book.completed is not None

    # doesn't matter which blurb, should not complete other fields
    assert book.blurb is not None
    assert book.rating is None              
    assert book.notes is None

def test_pretty_print():
    book = Book("Sample Title", "Author Name", "fiction", True, "Sample blurb", 4.5, "Sample notes")
    print(book)

if __name__ == "__main__":
    pytest.main()