import requests 
import pytest
import asyncio
import os 
from enum import Enum
from typing import Literal, Optional 
from bookbridge.utils import *
from bookbridge.book import * 
from notion_client import Client


'''
Most tests require the same Notion API key, Parent Page, and OpenAI Key as the GUI, and instead use variables in the .env file. 
You can find an example formatted file in .example.env
'''

load_dotenv() 
test_parent_page_id = os.getenv('PARENT_TEST_PAGE')

@pytest.mark.book
def test_book_initialization():
    book = Book("Sample Title", "Author Name", "fiction", BookStatus.NOT_STARTED, "Sample blurb", 4.5, ['Simon', 'Steve'])
    assert book.title == "Sample Title"
    assert book.author == "Author Name"
    assert book.genre in valid_genres
    assert book.status == BookStatus.NOT_STARTED
    assert book.blurb == "Sample blurb"
    assert book.rating == 4
    assert book.recs == ['Simon', 'Steve']
    # assert book.notes == "Sample notes"

@pytest.mark.book
def test_update_rating_selection(): 
    book = Book("Sample Title", "Author Name", "fiction", True, "Sample blurb", None)
    assert book.rating_selection == "Not Rated" 
    book.rating = 1 
    book.update_rating_selection() 
    assert book.rating_selection == "⭐"
    book.rating = 2
    book.update_rating_selection() 
    assert book.rating_selection == "⭐⭐"
    book.rating = 3
    book.update_rating_selection() 
    assert book.rating_selection == "⭐⭐⭐"
    book.rating = 4
    book.update_rating_selection() 
    assert book.rating_selection == "⭐⭐⭐⭐"
    book.rating = 5
    book.update_rating_selection() 
    assert book.rating_selection == "⭐⭐⭐⭐⭐"

@pytest.mark.book
def test_book_autofill(): 
    book = Book("Crime and Punishment")
    expected_author = "Fyodor Dostoevsky"
    llm_key = os.getenv("OPENAI_API_KEY")
    book.llm_autofill(llm_key) 
    assert book.author == expected_author
    assert book.genre in valid_genres
    assert isinstance(book.blurb, str)
    print(book)

@pytest.mark.doc
def test_llm_api_call():
    prompt = "Your task to return a critique of surveillance captialism and its impact on society."
    openai_key = os.getenv("OPENAI_API_KEY")
    response = llm_api_call(prompt, openai_key)
    print(f"llm api call produced the following test response:\n{response}")
    assert isinstance(response, str)

@pytest.mark.anthropic
def test_anthropic_api_call(): 
    prompt = "Your task to return a critique of surveillance captialism and its impact on society."
    anthropic_key = os.getenv("ANTHROPIC_KEY")
    response = anthropic_api_call(prompt, anthropic_key, model=CLAUDE_SMALL_MODEL)
    print(f"llm api call produced the following test response:\n{response}")
    assert isinstance(response, str)

@pytest.mark.anthropic
def test_anthropic_api_call_chained(): 
    prompt = "Your task is to generate a booklist of 50 books, each with an author and short description." 
    anthropic_key = os.getenv("ANTHROPIC_KEY")
    response = anthropic_api_call(prompt, anthropic_key, max_tokens=512, model=CLAUDE_SMALL_MODEL)
    print(f"llm api call produced the following test response:\n{response}")
    assert isinstance(response, str)
    count_tokens = lambda s: len(s)//4 
    assert count_tokens(response) > 512

@pytest.mark.extended
def test_llm_api_call_chained(): 
    prompt = "Your task is to generate a booklist of 50 books, each with an author and short description."
    openai_key = os.getenv('OPENAI_API_KEY')
    response = llm_api_call_chained(prompt, openai_key, max_tokens=512, model=GPT_FAST_MODEL)
    # assume each token on average is about 4 characters 
    count_tokens = lambda s: len(s)//4 
    assert count_tokens(response) > 512

@pytest.mark.doc    
def test_parse_csv_response():
    with open('data/test/synthetic_booklists/sample.csv', 'r') as file:
        output = file.read()
    llm_key = os.getenv("OPENAI_API_KEY")
    books = parse_csv_response(output, llm_key)
    print(books)
    for book in books:
        assert isinstance(book, Book), "failed csv parse, not all books in the booklist are books"

@pytest.mark.recs
def test_parse_csv_recs_response():
    with open('data/test/synthetic_booklists/sample_with_recs.csv', 'r') as file:
        output = file.read()
    llm_key = os.getenv("OPENAI_API_KEY")
    books = parse_csv_response(output, llm_key)
    print(books)
    for book in books:
        assert isinstance(book, Book), "failed csv parse, not all books in the booklist are books"
        assert len(book.recs)!=0, "failed csv parse, book should have recommender"

@pytest.mark.doc
def test_bookstring_to_csv(): 
    with open("data/test/synthetic_booklists/sample_booklist_20.txt", 'r') as file: 
        string = file.read() 
    llm_key = os.getenv("OPENAI_API_KEY")
    csv = bookstring_to_csv(string, llm_key)
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
    llm_key = os.getenv("OPENAI_API_KEY")
    books = pdf_to_booklist(path, llm_key)
    assert len(books) == 5

@pytest.mark.integration
def test_pdf_to_notion_base():
    # sample path to pdf, notion key, and parent page 
    path = "data/test/synthetic_booklists/test_booklist_5.pdf"
    notion_key = os.getenv("TEST_NOTION_SECRET_KEY")
    test_parent_page_id = os.getenv('PARENT_TEST_PAGE')
    # function call 
    llm_key = os.getenv("OPENAI_API_KEY")
    url = pdf_to_notion(path, test_parent_page_id, notion_key, llm_key)
    # go check that the page actually contains a good booklist 
    print(f"Go Check Out Your New Page: {url}")

@pytest.mark.integration
def test_pdf_to_notion_organic():
    # sample path to pdf, notion key, and parent page 
    path = "data/user/booklists/booklist_original.pdf"
    notion_key = os.getenv("TEST_NOTION_SECRET_KEY")
    test_parent_page_id = os.getenv('PARENT_TEST_PAGE')
    # function call 
    llm_key = os.getenv("OPENAI_API_KEY")
    url = pdf_to_notion(path, test_parent_page_id, notion_key, llm_key)
    # go check that the page actually contains a good booklist 
    print(f"Go Check Out Your New Page: {url}")

@pytest.mark.integration
@pytest.mark.recs 
def test_pdf_to_notion_recs_5(): 
    # sample path to pdf, notion key, and parent page 
    path = "data/test/synthetic_booklists/recs_5.pdf"
    notion_key = os.getenv("TEST_NOTION_SECRET_KEY")
    test_parent_page_id = os.getenv('PARENT_TEST_PAGE')
    # function call 
    llm_key = os.getenv("OPENAI_API_KEY")
    url = pdf_to_notion(path, test_parent_page_id, notion_key, llm_key)
    # go check that the page actually contains a good booklist 
    print(f"Go Check Out Your New Page: {url}")

@pytest.mark.integration 
def test_pdf_to_notion_10(): 
    # sample path to pdf, notion key, and parent page 
    path = "data/test/synthetic_booklists/test_booklist_10.pdf"
    notion_key = os.getenv("TEST_NOTION_SECRET_KEY")
    test_parent_page_id = os.getenv('PARENT_TEST_PAGE')
    # function call 
    llm_key = os.getenv("OPENAI_API_KEY")
    url = pdf_to_notion(path, test_parent_page_id, notion_key, llm_key)
    # go check that the page actually contains a good booklist 
    print(f"Go Check Out Your New Page: {url}")

@pytest.mark.integration 
def test_pdf_to_notion_25(): 
    path = "data/test/synthetic_booklists/test_booklist_25.pdf"
    notion_key = os.getenv("TEST_NOTION_SECRET_KEY")
    test_parent_page_id = os.getenv('PARENT_TEST_PAGE')
    # function call 
    llm_key = os.getenv("OPENAI_API_KEY")
    url = pdf_to_notion(path, test_parent_page_id, notion_key, llm_key)
    # go check that the page actually contains a good booklist 
    print(f"Go Check Out Your New Page: {url}")

@pytest.mark.doc 
def test_force_csv_fix(): 
    path = "data/test/synthetic_booklists/sample_output.txt" 
    with open(path, 'r') as file: 
        s = file.read() 
    formatted = force_csv_fix(s)
    print(formatted)
    assert is_valid_csv(formatted)

@pytest.mark.extended
def test_pdf_to_notion_15rs():
    path = "data/test/synthetic_booklists/test_booklist_15rs.pdf"
    notion_key = os.getenv("TEST_NOTION_SECRET_KEY")
    test_parent_page_id = os.getenv('PARENT_TEST_PAGE')
    # function call 
    llm_key = os.getenv("OPENAI_API_KEY")
    url = pdf_to_notion(path, test_parent_page_id, notion_key, llm_key)
    # go check that the page actually contains a good booklist 
    print(f"Go Check Out Your New Page: {url}")

@pytest.mark.extended
def test_pdf_to_notion_50rs():
    path = "data/test/synthetic_booklists/test_booklist_50rs.pdf"
    notion_key = os.getenv("TEST_NOTION_SECRET_KEY")
    test_parent_page_id = os.getenv('PARENT_TEST_PAGE')
    # function call 
    llm_key = os.getenv("OPENAI_API_KEY")
    url = pdf_to_notion(path, test_parent_page_id, notion_key, llm_key)
    # go check that the page actually contains a good booklist 
    print(f"Go Check Out Your New Page: {url}")

@pytest.mark.extended
def test_pdf_to_notion_99rs():
    path = "data/test/synthetic_booklists/test_booklist_99rs.pdf"
    notion_key = os.getenv("TEST_NOTION_SECRET_KEY")
    test_parent_page_id = os.getenv('PARENT_TEST_PAGE')
    # function call 
    llm_key = os.getenv("OPENAI_API_KEY")
    url = pdf_to_notion(path, test_parent_page_id, notion_key, llm_key)
    # go check that the page actually contains a good booklist 
    print(f"Go Check Out Your New Page: {url}")

@pytest.mark.extended
def test_pdf_to_notion_150rs():
    path = "data/test/synthetic_booklists/test_booklist_150rs.pdf"
    notion_key = os.getenv("TEST_NOTION_SECRET_KEY")
    test_parent_page_id = os.getenv('PARENT_TEST_PAGE')
    # function call 
    llm_key = os.getenv("OPENAI_API_KEY")
    url = pdf_to_notion(path, test_parent_page_id, notion_key, llm_key)
    # go check that the page actually contains a good booklist 
    print(f"Go Check Out Your New Page: {url}")
    
    


@pytest.mark.extended 
def test_pdf_to_notion_40(): 
    path = "data/test/synthetic_booklists/test_booklist_40.pdf"
    notion_key = os.getenv("TEST_NOTION_SECRET_KEY")
    test_parent_page_id = os.getenv('PARENT_TEST_PAGE')
    # function call 
    llm_key = os.getenv("OPENAI_API_KEY")
    url = pdf_to_notion(path, test_parent_page_id, notion_key, llm_key)
    # go check that the page actually contains a good booklist 
    print(f"Go Check Out Your New Page: {url}")

@pytest.mark.extended 
def test_pdf_to_notion_59():
    path = "data/test/synthetic_booklists/test_booklist_59.pdf"
    notion_key = os.getenv("TEST_NOTION_SECRET_KEY")
    test_parent_page_id = os.getenv('PARENT_TEST_PAGE')
    # function call 
    llm_key = os.getenv("OPENAI_API_KEY")
    url = pdf_to_notion(path, test_parent_page_id, notion_key, llm_key)
    # go check that the page actually contains a good booklist 
    print(f"Go Check Out Your New Page: {url}")

@pytest.mark.extended
def test_pdf_to_notion_30d(): 
    path = "data/test/synthetic_booklists/test_booklist_30d.pdf"
    notion_key = os.getenv("TEST_NOTION_SECRET_KEY")
    test_parent_page_id = os.getenv('PARENT_TEST_PAGE')
    # function call 
    llm_key = os.getenv("OPENAI_API_KEY")
    url = pdf_to_notion(path, test_parent_page_id, notion_key, llm_key)
    # go check that the page actually contains a good booklist 
    print(f"Go Check Out Your New Page: {url}")

@pytest.mark.extended
def test_pdf_to_notion_72d():
    path = "data/test/synthetic_booklists/test_booklist_72d.pdf"
    notion_key = os.getenv("TEST_NOTION_SECRET_KEY")
    test_parent_page_id = os.getenv('PARENT_TEST_PAGE')
    # function call 
    llm_key = os.getenv("OPENAI_API_KEY")
    url = pdf_to_notion(path, test_parent_page_id, notion_key, llm_key)
    # go check that the page actually contains a good booklist 
    print(f"Go Check Out Your New Page: {url}")

@pytest.mark.doc
def test_autofill():
    book = Book("Animal Farm")
    llm_key = os.getenv("OPENAI_API_KEY")
    book.llm_autofill(llm_key)

    # assert proper formatting on first three fields 
    assert book.title == "Animal Farm"
    assert book.author == "George Orwell"
    assert book.status is not None

    # doesn't matter which blurb, should not complete other fields
    assert book.blurb is not None
    assert book.rating is None              
    # assert book.notes is None

@pytest.mark.doc
def test_pretty_print():
    book = Book("Sample Title", "Author Name", "fiction", True, "Sample blurb", 4.5, ['Joey', 'Tristan', 'Yugi', 'Tea'])
    print(book)

@pytest.mark.notion 
def test_python_to_notion_database(): 
    # load example python booklist 
    llm_key = os.getenv("OPENAI_API_KEY")
    booklist = sample_booklist(llm_key) 
    notion_key = os.getenv("TEST_NOTION_SECRET_KEY")
    parent_page = os.getenv("PARENT_TEST_PAGE")
    #load up notion client 
    notion = Client(auth=os.getenv('TEST_NOTION_SECRET_KEY'))
    # create database and return id 
    llm_key = os.getenv("OPENAI_API_KEY")
    url = python_to_notion_database(notion_key, booklist, parent_page, llm_key)
    id = search_notion_id(url)
    # print out pages 
    query_response = notion.databases.query(
        database_id = id 
    )
    print(query_response['results'])

@pytest.mark.notion 
def test_infer_emoji(): 
    # load example book 
    llm_key = os.getenv("OPENAI_API_KEY")
    book = sample_book(llm_key) 
    # infer emoji 
    llm_key = os.getenv("OPENAI_API_KEY")
    emoji = infer_emoji(book, llm_key)
    # assert emoji is acceptable by notion, ie, unicode 
    assert valid_emoji(emoji)

@pytest.mark.notion
def test_create_booklist_database():
    # create booklsit database 
    notion_key = os.getenv("TEST_NOTION_SECRET_KEY")
    url = create_booklist_database(test_parent_page_id, notion_key)
    database_id = search_notion_id(url)
    # query database 
    notion = Client(auth=notion_key) 
    query_response = notion.databases.query(
        database_id=database_id
    )
    # print out page 
    print(query_response)

@pytest.mark.notion 
def test_add_booklist_page(): 
    llm_key = os.getenv("OPENAI_API_KEY")
    book = sample_book(llm_key) 
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
    llm_key = os.getenv("OPENAI_API_KEY")
    add_booklist_page(book, test_db_id, key, llm_key)
    # check number of pages after, assert we added a page 
    query_response = notion.databases.query(
        database_id=os.getenv('TEST_DB_ID')
    )
    assert len(query_response['results']) - 1 == prev_len

@pytest.mark.notion 
def test_add_booklist_page_new_select(): 
    llm_key = os.getenv("OPENAI_API_KEY")
    book = sample_book(llm_key) 
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
    book.genre = "new-genre"
    llm_key = os.getenv("OPENAI_API_KEY")
    add_booklist_page(book, test_db_id, key,llm_key)
    # check number of pages after, assert we added a page 
    query_response = notion.databases.query(
        database_id=os.getenv('TEST_DB_ID')
    )
    assert len(query_response['results']) - 1 == prev_len

@pytest.mark.doc
def test_sample_book(): 
    # call function
    llm_key = os.getenv("OPENAI_API_KEY")
    book = sample_book(llm_key) 
    # check if its a proper book object 
    assert isinstance(book, Book)

@pytest.mark.doc
def test_sample_booklist(): 
    # call function
    llm_key = os.getenv("OPENAI_API_KEY")
    booklist = sample_booklist(llm_key) 
    # check if each book was autofilled, and each book is indeed a Book 
    for book in booklist: 
        assert book.author is not None

@pytest.mark.doc
def test_valid_emoji(): 
    test_strings = ['🧛🏿', '✊🏼', 'Hello, world!', '\ud83d\udc4d\ud83d\udc4e', '👁️‍🗨️👁️‍🗨️']
    results = [valid_emoji(candidate) for candidate in test_strings]
    assert results == [True, True, False, False, False]

@pytest.mark.doc 
def test_clean_up_emoji():
    input_emoji = '👍🏽'
    base_emoji = clean_up_emoji(input_emoji)
    print(base_emoji)

@pytest.mark.doc 
def test_extract_emojis():
    with open('data/valid_emojis_notion.txt', 'r') as file:
        output = file.read()
    set = extract_emojis(output) 
    print(set)
    for emoji in set: 
        assert valid_emoji(emoji)

@pytest.mark.doc
def test_search_notion_id_with_valid_url():
    """Test searching a Notion ID from a valid URL."""
    expected_id = "86b6f5858bcf4ec797177c5ac80fcd63"
    actual_id = search_notion_id("https://www.notion.so/86b6f5858bcf4ec797177c5ac80fcd63")
    assert actual_id == expected_id, f"Expected to extract '{expected_id}', but got '{actual_id}' instead."

@pytest.mark.doc
def test_search_notion_id_with_invalid_url():
    """Test searching a Notion ID from an invalid URL (missing ID)."""
    actual_id = search_notion_id("https://www.notion.so/WorkspaceName/Page-Name")
    assert actual_id is None, "Expected to get None for a URL without a page ID."

@pytest.mark.doc
def test_search_notion_id_with_incomplete_url():
    """Test searching a Notion ID from an incomplete URL."""
    actual_id = search_notion_id("https://www.notion.so")
    assert actual_id is None, "Expected to get None for an incomplete URL."

@pytest.mark.doc 
def test_find_description_short():
    path = "data/test/synthetic_booklists/test_booklist_15rs.pdf"
    bookstring = extract_text_from_pdf(path)
    llm_key = os.getenv("OPENAI_API_KEY")
    title = "Anna Karenina"
    desc = find_description("1", bookstring, title, llm_key)
    target = "\"Anna Karenina\" by Leo Tolstoy follows the tragic story of Anna, a married woman who embarks on a passionate affair with Count Vronsky, leading to societal judgment and personal turmoil. The novel explores themes of love, society, and morality in 19th-century Russia."
    print(desc)
    print(target)
    assert desc == target 

@pytest.mark.doc
def test_find_description_long():
    path =  "data/test/synthetic_booklists/test_booklist_99rs.pdf"
    bookstring=extract_text_from_pdf(path)
    llm_key = os.getenv("OPENAI_API_KEY")
    title = "Adventures of Huckleberry Finn"
    desc = find_description("1", bookstring, title, llm_key)
    target = "\"The Adventures of Huckleberry Finn\" follows the journey of a young boy named Huck Finn as he escapes his abusive father and embarks on a rafting adventure down the Mississippi River with a runaway slave named Jim. Along the way, they encounter various characters and face moral dilemmas, ultimately exploring themes of race, freedom, and the importance of individual conscience."
    print(desc)
    print(target)
    assert desc == target 

if __name__ == "__main__":
    pytest.main()