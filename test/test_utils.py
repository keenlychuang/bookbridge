import requests 
import pytest
from typing import Literal, Optional 
from utils import Book, parse_response, llm_api_call, parse_booklist, generate_processing_prompt, txt_to_books, generate_sample_booklist

# full coverage and partitioning is kinda rough

# Test the Book class initialization
def test_book_initialization():
    book = Book("Sample Title", "Author Name", "fiction", True, "Sample blurb", 4.5, "Sample notes")
    assert book.title == "Sample Title"
    assert book.author == "Author Name"
    assert book.genre == "fiction"
    assert book.completed is True
    assert book.blurb == "Sample blurb"
    assert book.rating == 4.5
    assert book.notes == "Sample notes"

@pytest.mark.skip(reason="Not implemented yet")
def test_llm_api_call():
    # Mock the API call or use a fixed response
    # assert llm_api_call("test prompt") == "expected result"
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_parse_response():
    # Use a fixed API response and test if parsing is correct
    # assert len(parse_response("API response")) == expected_number_of_books
    pass

# test parse booklist 
@pytest.mark.skip(reason="Not implemented yet")
def test_parse_booklist(): 
    raise NotImplementedError()

# test generate processing prompt 
@pytest.mark.skip(reason="Not implemented yet")
def test_generate_processing_prompt(): 
    raise NotImplementedError()

# test txt to books 
@pytest.mark.skip(reason="Not implemented yet")
def test_txt_to_books():
    raise NotImplementedError()

# test generate sample booklist 
@pytest.mark.skip(reason="Not implemented yet")
def test_generate_sample_booklist():
    raise NotImplementedError()

# book: test autofill 
@pytest.mark.skip(reason="Not implemented yet")
def test_autofill():
    raise NotImplementedError()

# book: test pretty printing 
@pytest.mark.skip(reason="Not implemented yet")
def test_pretty_print():
    raise NotImplementedError()

if __name__ == "__main__":
    pytest.main()