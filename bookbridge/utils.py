import requests
import json 
import pickle
import csv 
import fitz
import io 
import os 
import re
import unicodedata
from bookbridge.book import *
from tqdm import tqdm
from dotenv import load_dotenv
from notion_client import Client
from importlib import resources
from pathlib import Path

# Assuming this script is in the package root (next to prompts/)
current_file_path = Path(__file__).resolve()
package_root = current_file_path.parent  # This is the 'bookbridge/bookbridge/' directory
prompts_path = package_root / "prompts"    

load_dotenv() 

def bookstring_to_csv(bookstring:str, llm_key:str)-> str: 
    """
    Parses the raw string text from a booklist into a csv format
    """
    with open(prompts_path / 'booklist_to_csv.txt', 'r') as file: 
        processing_prompt = file.read() 
    prompt_full = processing_prompt + bookstring
    csv_formatted = llm_api_call(prompt_full, llm_key)
    print("Reformatted booklist...")
    return csv_formatted

def is_valid_csv(csv_string):
    rows = csv_string.strip().split('\n')
    
    # Assuming the first row is the header
    num_columns = count_columns(rows[0])
    
    # Check each row for the correct number of columns
    for row in rows:
        if count_columns(row) != num_columns:
            return False
    
    return True

def count_columns(row):
    """
    Counts the number of columns in a row, ignoring commas within quotes.
    """
    in_quotes = False
    column_count = 0
    for i, char in enumerate(row):
        if char == '"' and (i == 0 or row[i-1] != '\\'):  # Check for non-escaped quote
            in_quotes = not in_quotes
        if char == ',' and not in_quotes:
            column_count += 1
    return column_count + 1  # Add one because column count is one more than comma count

def pdf_to_booklist(path:str, llm_key:str, max_attempts:int=2): 
    #pdf to string
    bookstring = extract_text_from_pdf(path)
    #string to csv 
    print("Restructuring your booklist...")
    attempts = 0 

    ### Try multiple times 
    while attempts <= max_attempts: 
        attempts +=1 
        csv = bookstring_to_csv(bookstring, llm_key)
        csv = force_csv_fix(csv)
        if is_valid_csv(csv):
            break 
        print(f"{attempts} csv conversion attempts failed, retrying")

    assert attempts <= max_attempts, f"Failed to convert CSV after {attempts} attempts!"
    #parse_response
    print("Converted to a CSV!")
    return parse_csv_response(csv, llm_key, bookstring)

### 

def parse_csv_response(response_text: str, llm_key:str, document:str, autofill:bool = True) -> List[Book]:
    """
    Parses the response text from an API call into a list of Book instances.

    Parameters:
    - response_text (str): The raw response text from an API call, assunming it is in a csv format

    Returns:
    List[Book]: A list of Book instances parsed from the response.

    Raises:
    NotImplementedError: Indicates the function hasn't been implemented yet.
    """
    #remove empty rows 
    reader = csv.reader(response_text.splitlines())  # Split CSV into rows
    books = []
    #skip first row 
    next(reader,None)
    for row in tqdm(reader, "Processing Rows"):
        title, author, status, rating, recs, blurb = row  # Unpacking row values
        # chagne from status string. Expecting status as 0,1,2
        status = BookStatus.from_int(int(status))
        rating = float(rating) if rating!= "None" else None  
        genre = None 
        # unpacking recs 
        recs = recs.split("/")
        recs = list(filter(lambda recommendation: True if recommendation != '' else False, recs))
        # finding the blurb 
        blurb = find_description(blurb, document, title, llm_key)
        book = Book(title, author, genre, status, blurb, rating, recs) 
        books.append(book)
    if autofill:
        for book in tqdm(books, "autofilling fields"):
            book.llm_autofill(llm_key)
    
    # remove duplicates 
    books = remove_duplicate_books(books)
    return books

def remove_duplicate_books(booklist: List[Book]) -> List[Book]:
    """
    Given a list of book instances, removes duplicate books by Book.title, which is a string.
    """
    seen_titles = set()
    unique_books = []
    for book in booklist:
        if book.title not in seen_titles:
            seen_titles.add(book.title)
            unique_books.append(book)
    
    return unique_books

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

def python_to_notion_database(notion_key: str, booklist: List[Book], parent_page: str, llm_key:str, emoji:bool=True): 
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
    for book in tqdm(booklist, "Converting to Notion"):
        page_id = add_booklist_page(book, database_id, notion_key=notion_key, llm_key= llm_key, emoji=emoji)
    return url
 

def infer_emoji(book: Book, llm_key:str) -> str:
    """
    Uses an LLM API call to infer an appropriate emoji representing the book

    Parameters: 
    - book (Book): The book to infer an emoji for 

    Returns: 
    - emoji (str): A Unicode Emoji to represent the book 

    Attempts the API call up to three times if necessary.
    """
    # Fill book if not already complete
    book.llm_autofill(llm_key)
    # Construct prompt
    with open(prompts_path/ 'request_emoji.txt', 'r') as file:
        emoji_prompt = file.read()
    book_name = f'Book Name: {book.title}\n'
    book_blurb = f'Book Description: {book.blurb}\n' if (book.blurb != None and book.blurb != "") else '' 
    full_prompt = emoji_prompt + book_name + book.blurb

    max_attempts = 4
    attempts = 0
    previous_emojis = [] 

    while attempts < max_attempts:
        try:
            # LLM API call
            if attempts > 0: 
                exclude_text = f'Do not use the following emojis:{previous_emojis}\n'
                new_prompt = full_prompt + exclude_text
                response_text = clean_up_emoji(llm_api_call(new_prompt, llm_key))
            else: 
                response_text = clean_up_emoji(llm_api_call(full_prompt, llm_key))
            # Quality check
            if valid_emoji(response_text):
                return response_text
            else:
                attempts += 1
                previous_emojis.append(response_text)
                print(f"Attempt {attempts}: Emoji response did not pass quality check. Emoji: {response_text} Retrying...")
        except Exception as e:
            attempts += 1
            print(f"Attempt {attempts}: API call failed with error: {e}. Retrying...")

    # If we can't find an emoji, just put down a generic one. 
    print(f"Failed to find emoji, defaulting on 📚...")
    return "📚"

# reduce emoji to base, avoiding modifiers 
# def clean_up_emoji(emoji_string:str):
#     modifier_pattern = re.compile('[\U0001F3FB-\U0001F3FF]')
#     return modifier_pattern.sub('', emoji_string)

def clean_up_emoji(emoji_string: str):
    # Pattern to match common emojis, including those with skin tone modifiers
    emoji_pattern = re.compile('(?:[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U0001F1E0-\U0001F1FF\U00002500-\U00002BEF\U00002B00-\U00002BFF\U00002300-\U000023FF\U00002100-\U0000214F\U00002600-\U000026FF])')
    modifier_pattern = re.compile('[\U0001F3FB-\U0001F3FF]')
    
    # Find all emojis in the string
    emojis = emoji_pattern.findall(emoji_string)
    
    # Take the first emoji found, if any, and remove skin tone modifiers
    if emojis:
        first_emoji = emojis[0]
        return modifier_pattern.sub('', first_emoji)
    else:
        return ''  # Return an empty string if no emoji is found

def force_csv_fix(input_string: str):
    """
    Attempts to fix the input string into a CSV format by ensuring the correct number of fields per line,
    ignoring commas within quoted strings. The summary field (or any field) will not be forcibly enclosed in quotes.
    """

    with open('before_processing.csv', 'w') as file:
        file.write(input_string)

    lines = input_string.strip().split('\n')
    num_fields = lines[0].count(',') + 1  # Assumes the header has the correct number of fields

    corrected_lines = []

    for line in lines:
        if "```" in line: 
            continue 
        corrected_line = ''
        field = ''
        num_commas = 0
        in_quotes = False
        for char in line:
            if char == '"' and not in_quotes:
                # Entering a quoted string
                in_quotes = True
            elif char == '"' and in_quotes:
                # Exiting a quoted string
                in_quotes = False
            if char == ',' and not in_quotes:
                # Count commas only when not in quotes
                num_commas += 1
                corrected_line += field + char
                field = ''
            else:
                field += char

        # Do not force the last field to be enclosed in quotes
        corrected_line += field  # Add the last field directly without modifying it

        missing_commas = (num_fields - 1) - num_commas
        if missing_commas > 0:
            corrected_line += ',' * missing_commas
        elif missing_commas < 0:
            corrected_line = corrected_line[:missing_commas]

        corrected_lines.append(corrected_line)

    corrected_csv = '\n'.join(corrected_lines)

    with open('after_processing.csv', 'w') as file:
        file.write(corrected_csv)

    return corrected_csv

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
                "type": "multi_select",
                "multi_select": {}
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

def add_booklist_page(book: Book, database_id: str, notion_key: str, llm_key:str, emoji:bool=True) -> str: 
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
    icon = infer_emoji(book, llm_key) if emoji else "📚"
    status_name = str(book.status)

    properties = {
        'Title': {
            "title": [
                {"text": {"content": book.title}}
            ]
        },
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

    if book.recs:
        properties['Recommended By'] = {
            "multi_select": [{"name": recommender} for recommender in book.recs]
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

def valid_emoji(s: str) -> bool:
    """
    Determines if the string s contains at least one valid emoji.
    """
    path = 'data/valid_emojis_notion.txt'
    with open('data/valid_emojis_notion.txt', 'r') as file:
        output = file.read()
    notion_emojis = extract_emojis(output)
    return s in notion_emojis

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

def extract_emojis(text:str) -> dict: 
    """
    Returns a mapping of valid emojis based on the emojis returned by notion API
    """ 
    # Define a regex pattern to match emojis encased in double quotes or backtick
    # This example uses a wide range of Unicode blocks to match common emojis, but it is not exhaustive.
    emoji_pattern = r'["`]([\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]+)["`]'

    matches = set(re.findall(emoji_pattern, text))

    return matches 

def pdf_to_notion(path:str, parent_page:str, notion_key:str, llm_key:str,emoji:bool=True) -> str: 
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
    booklist = pdf_to_booklist(path, llm_key)
    # python list to notion 
    print("Creating a Notion page for you...")
    url = python_to_notion_database(notion_key, booklist, parent_page, llm_key, emoji=emoji)
    return url