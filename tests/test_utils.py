import requests 
import pytest
import asyncio
import os 
from typing import Literal, Optional 
from bookbridge.utils import *
from notion_client import Client

load_dotenv() 
test_parent_page_id = os.getenv('PARENT_TEST_PAGE')

@pytest.mark.doc
def test_book_initialization():
    book = Book("Sample Title", "Author Name", "fiction", True, "Sample blurb", 4.5)
    assert book.title == "Sample Title"
    assert book.author == "Author Name"
    assert book.genre in valid_genres
    assert book.completed is True
    assert book.blurb == "Sample blurb"
    assert book.rating == 4.5
    return book 
    # assert book.notes == "Sample notes"

@pytest.mark.doc
def test_book_autofill(): 
    book = Book("Crime and Punishment")
    expected_author = "Fyodor Dostoevsky"
    book.llm_autofill() 
    assert book.author == expected_author
    assert book.genre in valid_genres
    assert isinstance(book.blurb, str)
    print(book)

@pytest.mark.doc
def test_llm_api_call():
    prompt = "Your task to return a critique of surveillance captialism and its impact on society."
    response = llm_api_call(prompt)
    print(f"llm api call produced the following test response:\n{response}")
    assert isinstance(response, str)

@pytest.mark.doc
def test_parse_csv_response():
    with open('data/test/synthetic_booklists/sample.csv', 'r') as file:
        output = file.read()
    books = parse_csv_response(output)
    for book in books:
        assert isinstance(book, Book), "failed csv parse, not all books in the booklist are books"

@pytest.mark.doc
def test_bookstring_to_csv(): 
    with open("data/test/synthetic_booklists/sample_booklist.txt", 'r') as file: 
        string = file.read() 
    csv = bookstring_to_csv(string)
    print(csv)
    assert is_valid_csv(csv)

@pytest.mark.doc
def test_extract_text_from_pdf():
    path = "data/test/synthetic_booklists/test_booklist_5.pdf"
    string = extract_text_from_pdf(path)
    print("Does this look like a good booklist?\n----------")
    print(string)
    print("----------")

@pytest.mark.doc
def test_pdf_to_bookslist():
    path = "data/test/synthetic_booklists/test_booklist_5.pdf"
    books = pdf_to_booklist(path)
    assert len(books) == 5

@pytest.mark.doc
def test_autofill():
    book = Book("Animal Farm")
    book.llm_autofill()

    # assert proper formatting on first three fields 
    assert book.title == "Animal Farm"
    assert book.author == "George Orwell"
    assert book.genre in valid_genres
    assert book.completed is not None

    # doesn't matter which blurb, should not complete other fields
    assert book.blurb is not None
    assert book.rating is None              
    # assert book.notes is None

@pytest.mark.doc
def test_pretty_print():
    book = Book("Sample Title", "Author Name", "fiction", True, "Sample blurb", 4.5)
    print(book)

@pytest.mark.notion 
def test_python_to_notion_database(): 
    # load example python booklist 
    booklist = sample_booklist() 
    notion_key = os.getenv("TEST_NOTION_SECRET_KEY")
    parent_page = os.getenv("PARENT_TEST_PAGE")
    #load up notion client 
    notion = Client(auth=os.getenv('TEST_NOTION_SECRET_KEY'))
    # create database and return id 
    id = python_to_notion_database(notion_key, booklist, parent_page)
    # print out pages 
    query_response = notion.databases.query(
        database_id = id 
    )
    print(query_response['results'])
    

@pytest.mark.notion 
def test_infer_emoji(): 
    # load example book 
    book = sample_book() 
    # infer emoji 
    emoji = infer_emoji(book)
    # assert emoji is acceptable by notion, ie, unicode 
    assert is_emoji(emoji)

@pytest.mark.notion
def test_create_booklist_database():
    # create booklsit database 
    database_id = create_booklist_database(test_parent_page_id)
    # query database 
    query_response = notion.databases.query(
        database_id=database_id
    )
    # print out page 
    print(query_response)

@pytest.mark.notion 
def test_add_booklist_page(): 
    book = sample_book() 
    key = os.getenv('TEST_NOTION_SECRET_KEY')
    notion = Client(auth=key)
    # assume we have a valid booklist database ID already with properly formatted properties 
    test_db_id = os.getenv('TEST_DB_ID')
    # check number of pages before 
    query_response = notion.databases.query(
        database_id=os.getenv('TEST_DB_ID')
    )
    prev_len = len(query_response['results'])
    # add page 
    add_booklist_page(book, test_db_id, key)
    # check number of pages after, assert we added a page 
    query_response = notion.databases.query(
        database_id=os.getenv('TEST_DB_ID')
    )
    assert len(query_response['results']) - 1 == prev_len

@pytest.mark.doc
def test_sample_book(): 
    # call function
    book = sample_book() 
    # check if its a proper book object 
    assert isinstance(book, Book)

@pytest.mark.doc
def test_sample_booklist(): 
    # call function
    booklist = sample_booklist() 
    # check if each book was autofilled, and each book is indeed a Book 
    for book in booklist: 
        assert book.author is not None

@pytest.mark.doc
def test_is_emoji(): 
    test_strings = ['\ud83d\ude00', '\ud83d\ude80', 'Hello, world!', '\ud83d\udc4d\ud83d\udc4e']
    results = [is_emoji(candidate) for candidate in test_strings]
    assert results == [True, True, False, True]


if __name__ == "__main__":
    pytest.main()