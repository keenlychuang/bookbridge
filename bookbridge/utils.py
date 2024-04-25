import requests
import json 
import pickle
import csv 
import fitz
import io 
import os 
import re
import unicodedata
from book import *
from tqdm import tqdm
from dotenv import load_dotenv
from notion_client import Client

load_dotenv() 

def bookstring_to_csv(bookstring:str, openai_api_key:str)-> str: 
    """
    Parses the raw string text from a booklist into a csv format
    """
    with open('../prompts/booklist_to_csv.txt', 'r') as file: 
        processing_prompt = file.read() 
    prompt_full = processing_prompt + bookstring
    csv_formatted = llm_api_call(prompt_full, openai_api_key)
    print("Reformatted booklist...")
    return csv_formatted

def is_valid_csv(csv_string:str):
    """
    Determines if the csv_string is in a valid csv format that could be processed by the csv package 
    """
    # Use StringIO to convert the string into a file-like object for the CSV reader
    csv_file_like_object = io.StringIO(csv_string)
    
    reader = csv.reader(csv_file_like_object)
    rows = list(reader)
    
    if not rows:
        return False  # Returns False for empty CSV strings
    
    # Determine the number of columns from the header row
    num_columns = len(rows[0])
    
    for row in rows:
        # Now fields are correctly parsed by the csv.reader
        if len(row) != num_columns:
            return False
    
    return True

def pdf_to_booklist(path:str, openai_api_key:str): 
    #pdf to string
    string = extract_text_from_pdf(path)
    #string to csv 
    print("Restructuring your booklist...")
    csv = bookstring_to_csv(string, openai_api_key)
    try:
        assert is_valid_csv(csv)
    except:
        print(csv)
        raise ValueError("Invalid CSV")
    #parse_response
    return parse_csv_response(csv, openai_api_key)

# refactor 
def parse_csv_response(response_text: str, openai_api_key:str, autofill:bool = True) -> List[Book]:
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
            book.llm_autofill(openai_api_key)
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

def python_to_notion_database(notion_key: str, booklist: List[Book], parent_page: str, openai_api_key:str): 
    """ 
    Given a list of Books, creates a Notion Database with entries corresponding to each book.

    Parameters: 
    - notion_key (str): the api key for the Notion integration 
    - booklist (List[Book]): A list of Books to transfer to Notion 
    - parent_page (str): the id of the parent page where the book will be created 
    
    Returns: 
    - url (str): the url associated with the new Notion database 

    """ 
    # create database on parent page 
    url = create_booklist_database(parent_page=parent_page, notion_key=notion_key) 
    database_id = search_notion_id(url)
    # for each book in booklist, add page 
    for book in tqdm(booklist, "converting to notion"):
        page_id = add_booklist_page(book, database_id, notion_key=notion_key, openai_api_key= openai_api_key)
    return url
 

def infer_emoji(book: Book, openai_api_key:str) -> str:
    """
    Uses an LLM API call to infer an appropriate emoji representing the book

    Parameters: 
    - book (Book): The book to infer an emoji for 

    Returns: 
    - emoji (str): A Unicode Emoji to represent the book 

    Attempts the API call up to three times if necessary.
    """
    # Fill book if not already complete
    book.llm_autofill(openai_api_key)
    # Construct prompt
    with open('../prompts/request_emoji.txt', 'r') as file:
        emoji_prompt = file.read()
    full_prompt = emoji_prompt + book.blurb

    max_attempts = 2
    attempts = 0
    
    while attempts < max_attempts:
        try:
            # LLM API call
            response_text = llm_api_call(full_prompt, openai_api_key)
            # Quality check
            if is_emoji(response_text):
                return response_text
            else:
                attempts += 1
                print(f"Attempt {attempts}: Emoji response did not pass quality check. Retrying...")
        except Exception as e:
            attempts += 1
            print(f"Attempt {attempts}: API call failed with error: {e}. Retrying...")

    print(response_text)
    raise ValueError("Failed to infer an emoji after maximum attempts.")


def create_booklist_database(parent_page: str, notion_key:str) -> str:
    """
    Creates a Notion database and returns the associated database id. Include properties for 
    Title, Author, Genre, Status, Rating and Rec By. Include blurb as a subpage. 

    Parameters: 
    - parent_page (str): the ID of the parent page of the database, which can be another page, database, or workspace. 
    
    Returns:
    - url (str): the ID of the created database
    """
    database_name = "Imported Booklist"
    notion = Client(auth=notion_key)
    
    #create dict/json
    parent = {"type": "page_id","page_id": parent_page}
    title = [
                {
                    "type": "text",
                    "text": {
                        "content": database_name,
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
    icon = {
        "type": "emoji",
        "emoji": "📚"
    }
    args = {"parent":parent, "title":title, "properties":properties, "icon":icon}
    #use client and endpoint 
    response = notion.databases.create(**args)
    #return url
    return response['url']

def add_booklist_page(book: Book, database_id: str, notion_key: str, openai_api_key:str) -> str: 
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
    icon = infer_emoji(book, openai_api_key)
    status_name = "Completed" if book.completed else "Not Started"

    properties = {
        'Title': {
            "title": [
                {"text": {"content": book.title}}
            ]
        },
        #TODO, pick rating 
        'Rating': {
            "select": {
                "name":book.rating_selection
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
        "emoji": icon
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

def is_emoji(s: str) -> bool:
    """
    Determines if the string s contains at least one valid emoji.
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
    
    # Check if any character in the string falls within any emoji range
    return any(in_range(char) for char in s)

def search_notion_id(url:str) -> str: 
    """
    Searches a URL for a non-segmented, 32-character notion database ID and returns it if found.
    """
    regex = r"([a-f0-9]{32})"
    match = re.search(regex, url, re.IGNORECASE)

    if match:
        return match.group(1)
    else:
        return None

def pdf_to_notion(path:str, parent_page:str, notion_key:str, openai_api_key:str) -> str: 
    """
    Given the str path to a pdf containing a booklist, attempt to convert the booklist to a new notion database and return the database id. 

    Params: 
    - path (str): the path to the pdf booklist 
    - parent_page (str): the id of the parent page that will contain the new database 
    - notion_key (str): the api key for the integration with access to the notion parent page of the new database 

    Returns:
    - url (str): the url of the notion database containing the inferred information from the booklist. 
    """
    # pdf to python list 
    print("Reading through your booklist...")
    booklist = pdf_to_booklist(path, openai_api_key)
    # python list to notion 
    print("Creating a Notion page for you...")
    url = python_to_notion_database(notion_key, booklist, parent_page, openai_api_key)
    return url