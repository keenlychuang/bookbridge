import requests
import json 
import pickle
from openai import OpenAI
import csv 
import fitz
import io 
import os 
from tqdm import tqdm
from typing import Literal, Optional, List
from dotenv import load_dotenv
from notion_client import Client
import unicodedata

load_dotenv() 
notion_key = os.getenv('NOTION_SECRET_KEY')
# Genre = Literal['fiction', 'non-fiction', 'mystery', 'fantasy', 'science fiction', 'romance', 'thriller', 'historical', 'biography', 'poetry', 'self-help', 'young adult']
# valid_genres = ['fiction', 'non-fiction', 'mystery', 'fantasy', 'science fiction', 'romance', 'thriller', 'historical', 'biography', 'poetry', 'self-help', 'young adult']
valid_genres = [
                'fiction', 'non-fiction', 'biography', 'mystery', 'fantasy', 'science-fiction',
                'historical', 'romance', 'thriller', 'self-help', 'poetry', 'graphic-novel', 
                'adventure', 'horror', 'true-crime', 'childrens', 'young-adult', 'classic-literature', 
                'philosophy', 'anthology', 'memoir', 'short-story', 'historical-fiction', 
]
Genre = Literal[
                'fiction', 'non-fiction', 'biography', 'mystery', 'fantasy', 'science-fiction',
                'historical', 'romance', 'thriller', 'self-help', 'poetry', 'graphic-novel', 
                'adventure', 'horror', 'true-crime', 'childrens', 'young-adult', 'classic-literature', 
                'philosophy', 'anthology', 'memoir', 'short-story', 'historical-fiction', 
]
valid_genres_string = str(valid_genres)
with open('prompts/request_emoji.txt', 'r') as file: 
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
    blurb_prompt = file.read() 

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

        #TODO Non-essential properties 
        self.rec_by = None 
        self.emoji = None 
        self.notes = None

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
        #fill genre 
        if self.genre is None: 
            prompt = genre_prompt + f"\n{valid_genres_string}\n\n{self.title}"
            genre_string = llm_api_call(prompt=prompt)
            assert genre_string in valid_genres
            self.genre = genre_string
        #fill blurb 
        if self.blurb is None: 
            prompt = blurb_prompt + f"\n\n{self.title}"
            blurb_string =llm_api_call(prompt=prompt)
            self.blurb = blurb_string


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

def llm_api_call(prompt: str, max_tokens: int = 4096, temperature: float = 0.7, frequency_penalty:float = 0.0, model:str = "gpt-4-turbo") -> str:
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

def bookstring_to_csv(bookstring:str)-> str: 
    """
    Parses the raw string text from a booklist into a csv format
    """
    prompt_full = processing_prompt + bookstring
    csv_formatted = llm_api_call(prompt_full)
    return csv_formatted

def is_valid_csv(csv_string):
    rows = csv_string.strip().split("\n")
    
    # Determine the number of columns from the header row
    num_columns = len(rows[0].split(","))
    
    for row in rows:
        # Basic parsing of CSV row, not handling special cases like quotes
        fields = row.split(",")
        
        # Check if the number of fields in this row matches the header
        if len(fields) != num_columns:
            return False
    
    return True

def pdf_to_booklist(path:str): 
    #pdf to string
    string = extract_text_from_pdf(path)
    #string to csv 
    csv = bookstring_to_csv(string)
    try:
        assert is_valid_csv(csv)
    except:
        raise ValueError("Invalid CSV")
        print(csv)
    #parse_response
    return parse_csv_response(csv)

def parse_csv_response(response_text: str, autofill:bool = True) -> List[Book]:
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
    #skip first row 
    next(reader,None)
    for row in tqdm(reader, "Processing Rows"):
        try: 
            title, author, completed, rating, blurb = row  # Unpacking row values
            # Convert 'completed' to boolean, 'rating' to float if present
            completed = completed == "True"
            rating = float(rating) if rating else None  
            genre = None 
            book = Book(title, author, genre, completed, blurb, rating) 
            books.append(book)
        except: 
            print(row)
            raise ValueError("Error in parsing CSV formatted str")
    if autofill:
        for book in tqdm(books, "autofilling fields"):
            book.llm_autofill()
    return books


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

def python_to_notion_database(notion_key: str, booklist: List[Book], parent_page: str): 
    """ 
    Given a list of Books, creates a Notion Database with entries corresponding to each book.

    Parameters: 
    - notion_key (str): the api key for the Notion integration 
    - booklist (List[Book]): A list of Books to transfer to Notion 
    - parent_page (str): the id of the parent page where the book will be created 
    
    Returns: 
    - database_id (str): the database id associated with the new Notion database 

    """ 
    # create database on parent page 
    database_id = create_booklist_database(parent_page=parent_page, notion_key=notion_key) 
    # for each book in booklist, add page 
    for book in booklist:
        page_id = add_booklist_page(book, database_id, notion_key=notion_key)
    return database_id


def infer_emoji(book: Book) -> str: 
    """
    Uses an LLM API call to infer an appropriate emoji representing the book

    Parameters: 
    - book (Book): The book to infer an emoji for 

    Returns: 
    - emoji (str):  A Unicode Emoji to represent the book 
    """
    #fill book if not already complete 
    book.llm_autofill() 
    #contsruct prompt 
    full_prompt = emoji_prompt + book.blurb
    #llmapi call 
    response_text = llm_api_call(full_prompt)
    #quality check
    assert is_emoji(response_text)
    return response_text


def create_booklist_database(parent_page: str, notion_key:str) -> str:
    """
    Creates a Notion database and returns the associated database id. Include properties for 
    Title, Author, Genre, Status, Rating and Rec By. Include blurb as a subpage. 

    Parameters: 
    - parent_page (str): the ID of the parent page of the database, which can be another page, database, or workspace. 
    
    Returns:
    - database_id (str): the ID of the created database
    """
    notion = Client(auth=notion_key)
    
    #create dict/json
    parent = {"type": "page_id","page_id": parent_page}
    title = [
                {
                    "type": "text",
                    "text": {
                        "content": "Test Database",
                    },
                },
            ]
    properties = {
            "Title": {
                "type": "title",
                "title": {},
            },
            "Author": {
                "type": "rich_text",
                "rich_text": {},
            },            
            "Genre": {
                "type": "select",
                "select": {
                    "options": [
                        {"name": "Fantasy", "color": "blue"},
                        {"name": "Sci-Fi", "color": "purple"},
                        {"name": "Mystery", "color": "gray"},
                        {"name": "Non-Fiction", "color": "brown"},
                        # Add more genres as needed
                    ]
                }
            },
            "Status":{
                "type": "select", 
                "select": {
                    "options" :[ 
                        {
                            "name": "Completed", 
                            "color": "green"
                        }, 
                        {
                            "name": "Not Started", 
                            "color": "gray"
                        },                         
                        {
                            "name": "In Progress", 
                            "color": "orange"
                        }, 
                    ]
                }
            },
            "Rating": {
                "type": "select",
                "select": {
                    "options": [
                        {"name": "⭐", "color": "yellow"},
                        {"name": "⭐⭐", "color": "yellow"},
                        {"name": "⭐⭐⭐", "color": "yellow"},
                        {"name": "⭐⭐⭐⭐", "color": "yellow"},
                        {"name": "⭐⭐⭐⭐⭐", "color": "yellow"},
                        {"name": "Not Rated", "color": "default"} 
                    ]
                }
            },
            "Recommended By": {
                "type": "select",
                "select": {}
            },
            "Want To Read": {
                "type": "multi_select", 
                "multi_select": {} 
            }          
    }
    properties["Genre"] = {
        "type": "select",
        "select": {
            "options": [
                {"name": genre.replace('-', ' ').title(), "color": "default"} 
                for genre in valid_genres
            ]
        } 
    }   
    args = {"parent":parent, "title":title, "properties":properties}
    #use client and endpoint 
    response = notion.databases.create(**args)
    #return id 
    return response['id']

def add_booklist_page(book: Book, database_id: str, notion_key: str) -> str: 
    """
    Adds a row to the database representing the booklist in Notion, cooresponding to the supplied Book. 

    Params: 
    - book (Book): the book object representing the book to be added to the database 
    - database_id (str): the id of the Notion database representing the booklist. 

    Returns: 
    - id (str): the id of the new booklist page in the database 
    """
    # create client 
    notion = Client(auth=notion_key)
    parent= {"database_id":database_id}
    icon = infer_emoji(book)
    status_name = "Completed" if book.completed else "Not Started"

    properties = {
        'Title': {
            "title": [
                {"text": {"content": book.title}}
            ]
        },
        'Rating': {
            "select": {
                "name":"Not Rated"
            }
        },
        'Author': {
            "rich_text": [
                {"text": {"content": book.author}}
            ]
        },
        'Status': {
            "select": {"name":status_name}
        },
        'Genre': {
            "select": {"name":book.genre.replace('-', ' ').title()}
        },
    }
    children = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": book.blurb,
                        }
                    }
                ]
            }
        }
    ]

    icon = {
        "type": "emoji",
        "emoji": "📚"
    }

    args = {
        "parent":parent,
        "properties":properties,
        "icon":icon, 
        "children":children
    }

    #api call 
    response = notion.pages.create(**args)
    return response["id"]


def sample_book() -> Book:
    """
    Returns a sample Book object with non-emoji parameters autofilled 
    """ 
    book = Book("Crime and Punishment")
    book.llm_autofill() 
    return book 

def sample_booklist() -> List: 
    """
    Returns a sample booklist, a python List of Book objects with their non-emoji parameters autofilled 
    """
    booklist = [Book("Crime and Punishment"), 
                Book("The Cat in the Hat"), 
                Book("Eragon"),
                Book("Dune"),
                Book("Never Finished")
                ] 
    for book in booklist:
        book.llm_autofill()
    return booklist 

def is_emoji(s:str) -> bool:
    """
    Determines if the string s is a valid emoji in unicode 
    """
    emoji_ranges = [
        ('\U0001F600', '\U0001F64F'),  # Emoticons
        ('\U0001F300', '\U0001F5FF'),  # Miscellaneous Symbols and Pictographs
        ('\U0001F680', '\U0001F6FF'),  # Transport and Map Symbols
        ('\U0001F700', '\U0001F77F'),  # Alchemical Symbols
        ('\U0001F780', '\U0001F7FF'),  # Geometric Shapes Extended
        ('\U0001F800', '\U0001F8FF'),  # Supplemental Arrows-C
        ('\U0001F900', '\U0001F9FF'),  # Supplemental Symbols and Pictographs
        ('\U0001FA00', '\U0001FA6F'),  # Chess Symbols
        ('\U0001FA70', '\U0001FAFF'),  # Symbols and Pictographs Extended-A
        ('\U00002702', '\U000027B0'),  # Dingbats
        ('\U000024C2', '\U0001F251')   # Enclosed characters
    ]

    def in_range(uchar):
        return any(start <= uchar <= end for start, end in emoji_ranges)

    return all(in_range(char) for char in s) 
