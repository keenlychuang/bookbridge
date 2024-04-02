import requests
import json 
import pickle
from openai import OpenAI
import csv 
import fitz
from io import StringIO 
from typing import Literal, Optional, List
from dotenv import load_dotenv

Genre = Literal['fiction', 'non-fiction', 'mystery', 'fantasy', 'science fiction', 'romance', 'thriller', 'historical', 'biography', 'poetry', 'self-help', 'young adult']
valid_genres = ['fiction', 'non-fiction', 'mystery', 'fantasy', 'science fiction', 'romance', 'thriller', 'historical', 'biography', 'poetry', 'self-help', 'young adult']
valid_genres_string = str(valid_genres)
with open('prompts/request_emoji.txt', 'r') as file:  # 'r' for read mode
    emoji_prompt = file.read()
with open('prompts/request_booklist.txt','r') as file: 
    booklist_prompt = file.read() 
with open('prompts/booklist_to_csv.txt', 'r') as file: 
    processing_prompt = file.read() 
with open('prompts/infer_genre.txt', 'r') as file:
    genre_prompt = file.read() 
with open('prompts/infer_author.txt', 'r') as file:
    author_prompt = file.read() 
with open('prompts/infer_blurb.txt', 'r') as file:
    genre_prompt = file.read() 
# booklist_prompt = "Create a booklist of 10 of the most popular books of all time. Include brief descriptions of the book and give each a rating on a scale of one to five. Only return the list itself, do not describe your process."
# processing_prompt = "You will be provided with a text that represents a booklist. Your task is to translate it into a csv format. Include fields for the title, author, whether or not it is completed, its rating, and a summary of the book. Do not add any information that is not in the booklist itself, and leave the fields blank if they do not exist."
# genre_prompt = "You will be provided with the title of a book. Your task is to respond with the genre that most closely matches it. Pick from the following list."
# author_prompt = "You will be provided with the title of a book. Your task is to respond with only the name of the author of the book. If you do not know the name of the author, or it is a book without a known author, or if the author is ambiguous, simply respond with \"Unknown\". "
# blurb_prompt = "You will be provided with the title of a book. Your task is to respond with a brief description of the book. Keep your description to a couple of sentences at most. Include only the description, and do not mention the title or the author. If you don't know the book, respond with \"A summary cannot be generated for this book title.\""

class Book:
    def __init__(self, title: str, author: str = None, genre: Optional[Genre] = None, completed: bool = False, blurb: str = None, rating: float = None):
        """
        Initializes a new Book instance.

        Parameters:
        - title (str): The title of the book.
        - author (str, optional): The author of the book. Default is None.
        - genre (Optional[Genre], optional): The genre of the book from a predefined set. Default is None.
        - completed (bool, optional): Flag indicating if the book has been read. Default is False.
        - blurb (str, optional): A short description or blurb of the book. Default is None.
        - rating (float, optional): The personal rating given to the book. Default is None.
        # - notes (str, optional): Additional notes or comments about the book. Default is None.
        """
        assert title is not None, "Title cannot be None"
        self.title = title
        self.author = author
        self.genre = genre
        self.blurb = blurb
        self.completed = completed
        self.rating = rating
        # self.notes = notes

    def llm_autofill(self) -> str:
        """
        Automatically fills missing fields of the book instance using a language model API.

        Returns:
        str: A status message indicating success or details of the missing fields filled.
        
        Raises:
        NotImplementedError: Indicates the method hasn't been implemented yet.
        """
        authored, genred, blurbed = False, False, False
        #fill author 
        if self.author is None: 
            prompt = author_prompt + f"\n\n{self.title}"
            author_string = llm_api_call(prompt=prompt)
            self.author = author_string 
            print("added author")
        #fill genre 
        if self.genre is None: 
            prompt = genre_prompt + f"\n{valid_genres_string}\n\n{self.title}"
            genre_string = llm_api_call(prompt=prompt)
            assert genre_string in valid_genres
            self.genre = genre_string
            print("added genre")
        #fill blurb 
        if self.blurb is None: 
            prompt = blurb_prompt + f"\n\n{self.title}"
            blurb_string =llm_api_call(prompt=prompt)
            self.blurb = blurb_string
            print('added blurb')


    def __str__(self) -> str:
        """
        Provides a formatted string representation of the book instance.

        Returns:
        str: A string detailing the book's title, author, and other attributes.

        """
        completed_str = "Yes" if self.completed else "No"
        return (
            f"Title: {self.title}\n"
            f"    Author: {self.author or 'N/A'}\n"
            f"    Genre: {self.genre or 'N/A'}\n"
            f"    Completed: {completed_str}\n"
            f"    Blurb: {self.blurb or 'N/A'}\n"
            f"    Rating: {self.rating or 'N/A'}\n"
        )

def llm_api_call(prompt: str, max_tokens: int = 150, temperature: float = 0.7, frequency_penalty:float = 0.0, model:str = "gpt-4-0125-preview") -> str:
    """
    Calls the GPT-4 API using a provided text prompt to generate text.

    Parameters:
    - prompt (str): The text prompt to send to the API.
    - max_tokens (int, optional): The maximum number of tokens to generate. Default is 150.
    - temperature (float, optional): The creativity temperature. Default is 0.7.

    Returns:
    str: The text generated by the API.

    Raises:
    NotImplementedError: Indicates the function hasn't been implemented yet.
    """
    load_dotenv() 
    client = OpenAI() 
    gpt_role_prompt = "You are an AI assistant that can help with a variety of tasks." 
    gpt_user_prompt = prompt
    combined_prompt=[{"role": "assistant", "content": gpt_role_prompt}, {"role": "user", "content": gpt_user_prompt}]
    response = client.chat.completions.create(
        model=model,
        messages = combined_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        frequency_penalty=frequency_penalty)
    string_response = response.choices[0].message.content
    return string_response

def parse_response(response_text: str) -> List[Book]:
    """
    Parses the response text from an API call into a list of Book instances.

    Parameters:
    - response_text (str): The raw response text from an API call, assunming it is in a csv format

    Returns:
    List[Book]: A list of Book instances parsed from the response.

    Raises:
    NotImplementedError: Indicates the function hasn't been implemented yet.
    """
    reader = csv.reader(response_text.splitlines())  # Split CSV into rows
    books = []
    for row in reader:
        title, author, genre, completed, blurb, rating = row  # Unpacking row values

        # Convert 'completed' to boolean, 'rating' to float if present
        completed = completed == "True"
        rating = float(rating) if rating else None  
        book = Book(title, author, genre, completed, blurb, rating) 
        books.append(book)
    return books

def generate_processing_prompt(raw_booklist: str) -> str:
    """
    Generates a processing prompt to be used with a language model based on a raw booklist.

    Parameters:
    - raw_booklist (str): The raw text of a booklist.

    Returns:
    str: A formatted prompt for language model processing.

    Raises:
    NotImplementedError: Indicates the function hasn't been implemented yet.
    """
    raise NotImplementedError()

def string_to_books(csv_string:str) -> List[Book]:
    """
    Processes a list of books in text format to create a list of Book instances.

    Returns:
    List[Book]: A list of Book instances created from the text input.

    Raises:
    NotImplementedError: Indicates the function hasn't been implemented yet.
    """
    raise NotImplementedError("NOT YET IMPLEMENTED")

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts and returns all text from a PDF file.

    Parameters:
    - pdf_path (str): The file path to the PDF from which text will be extracted.

    Returns:
    - str: All text extracted from the PDF.
    """
    text = ''
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def generate_sample_booklist(num_books:int, path = "data/test/book_titles/gpt4_titles.txt") -> str:
    """
    Placeholder function to generate return a sample booklist, pulled from a list of books.

    Parameters:
    - num_books (int): Number of books to include in the sample list.

    Raises:
    - NotImplementedError: Functionality not yet implemented.
    """
    raise NotImplementedError()
