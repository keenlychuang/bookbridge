import random
import os
from tqdm import tqdm 
from typing import Literal, Optional, List
from dotenv import load_dotenv
from openai import OpenAI
from importlib import resources
from pathlib import Path
from enum import Enum

# Assuming this script is in the package root (next to prompts/)
current_file_path = Path(__file__).resolve()
package_root = current_file_path.parent  # This is the 'bookbridge/bookbridge/' directory
repo_root = package_root.parent # where everything else is located 
prompts_path = package_root / "prompts"

valid_genres = [
                'fiction', 'non-fiction', 'biography', 'mystery', 'fantasy', 'science-fiction',
                'historical', 'romance', 'thriller', 'self-help', 'poetry', 'graphic-novel', 
                'adventure', 'horror', 'true-crime', 'childrens', 'young-adult', 'classic-literature', 
                'philosophy', 'anthology', 'memoir', 'short-story', 'historical-fiction', 'magical-realism'
                ]
Genre = Literal[
                'fiction', 'non-fiction', 'biography', 'mystery', 'fantasy', 'science-fiction',
                'historical', 'romance', 'thriller', 'self-help', 'poetry', 'graphic-novel', 
                'adventure', 'horror', 'true-crime', 'childrens', 'young-adult', 'classic-literature', 
                'philosophy', 'anthology', 'memoir', 'short-story', 'historical-fiction', 'magical-realism'
                ]
valid_genres_string = str(valid_genres)

names_list = [
    "Aiden", 
    "Priya", 
    "Santiago", 
    "Mei", 
    "Youssef", 
    "Olga", 
    "Declan", 
    "Fatima", 
    "Hiro", 
    "Sofia"
]

SMART_MODEL = "gpt-4-turbo"
FAST_MODEL = "gpt-3.5-turbo"

# Enum for possible states of book completion, for readability 
class BookStatus(Enum):
    NOT_STARTED = 0
    IN_PROGRESS = 1
    COMPLETED = 2

    @staticmethod
    # convert valid int to corresponding book status 
    def from_int(value):
        for status in BookStatus:
            if status.value == value:
                return status
        raise ValueError(f"No corresponding BookStatus found for value: {value}")

    def __str__(self):
        if self == BookStatus.NOT_STARTED:
            return "Not Started"
        elif self == BookStatus.IN_PROGRESS:
            return "In Progress"
        elif self == BookStatus.COMPLETED:
            return "Completed"
        else:
            return "Unknown Status"

class Book:
    def __init__(self, title: str, author: str = None, genre: Optional[Genre] = None, status: BookStatus = BookStatus.NOT_STARTED, blurb: str = None, rating: float = None, recs:List=None):
        """
        Initializes a new Book instance.

        Parameters:
        - title (str): The title of the book.
        - author (str, optional): The author of the book. Default is None.
        - genre (Optional[Genre], optional): The genre of the book from a predefined set. Default is None.
        - status (bool, optional): Flag indicating if the book has been read. Default is False.
        - blurb (str, optional): A short description or blurb of the book. Default is None.
        - rating (float, optional): The personal rating given to the book, on a five point scale. Default is None.
        # - notes (str, optional): Additional notes or comments about the book. Default is None.
        """
        assert title is not None, "Title cannot be None"
        self.title = title
        self.author = author
        self.genre = genre
        self.blurb = blurb
        self.status = status
        self.rating = round(rating) if rating is not None else None 
        self.rating_selection = "Not Rated"
        self.recs=[recommender for recommender in recs] if recs != None else [] 
        self.emoji = None 
        # self.notes = None

        self.update_rating_selection() 

    def llm_autofill(self, openai_api_key) -> str:
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
            with open(prompts_path/'infer_author.txt', 'r') as file:
                author_prompt = file.read() 
            prompt = author_prompt + f"\n\n{self.title}"
            author_string = llm_api_call(prompt=prompt, openai_api_key= openai_api_key, model=FAST_MODEL)
            self.author = author_string 
        #fill genre 
        if self.genre is None: 
            with open(prompts_path/'infer_genre.txt', 'r') as file:
                genre_prompt = file.read() 
            prompt = genre_prompt + f"\n{valid_genres_string}\n\n{self.title}"
            genre_string = llm_api_call(prompt=prompt, openai_api_key= openai_api_key)
            self.genre = genre_string
        #fill blurb 
        if self.blurb is None: 
            with open(prompts_path/'infer_blurb.txt', 'r') as file:
                blurb_prompt = file.read() 
            prompt = blurb_prompt + f"\n\n{self.title}"
            blurb_string =llm_api_call(prompt=prompt, openai_api_key= openai_api_key, model=FAST_MODEL)
            self.blurb = blurb_string
    
    def update_rating_selection(self) -> None: 
        """
        Update the selection of the rating based on the numerical value. Assumes a five point scale, natural numbers
        """ 
        if self.rating == None: 
            self.rating_selection = "Not Rated"
        match self.rating: 
            case 1:
                self.rating_selection = "⭐"
            case 2: 
                self.rating_selection = "⭐⭐"
            case 3: 
                self.rating_selection = "⭐⭐⭐"
            case 4: 
                self.rating_selection = "⭐⭐⭐⭐"
            case 5: 
                self.rating_selection = "⭐⭐⭐⭐⭐"

    def __str__(self) -> str:
        """
        Provides a formatted string representation of the book instance.

        Returns:
        str: A string detailing the book's title, author, other attributes, and recommenders.
        """
        # Convert the list of recommenders to a string, handling the case where it might be None or empty
        recommenders_str = ", ".join(self.recs) if self.recs else "N/A"
        return (
            f"Title: {self.title}\n"
            f"    Author: {self.author or 'N/A'}\n"
            f"    Genre: {self.genre or 'N/A'}\n"
            f"    Status: {self.status}\n"
            f"    Blurb: {self.blurb or 'N/A'}\n"
            f"    Rating: {self.rating or 'N/A'}\n"
            f"    Recommenders: {recommenders_str}\n"
        )

def llm_api_call(prompt: str,openai_api_key:str,  max_tokens: int = 4096, temperature: float = 0.7, frequency_penalty:float = 0.0, model:str = FAST_MODEL) -> str:
    """
    Calls the openai llm API using a provided text prompt to generate text.

    Parameters:
    - prompt (str): The text prompt to send to the API. 
    - max_tokens (int, optional): The maximum number of tokens to generate. Default is 150.
    - temperature (float, optional): The creativity temperature. Default is 0.7.
    - model (str): the name of the model to be used 

    Returns:
    str: The text generated by the API.

    Raises:
    NotImplementedError: Indicates the function hasn't been implemented yet.
    """
    load_dotenv() 
    client = OpenAI() 
    client.api_key = openai_api_key 
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

def llm_api_call_chained(prompt: str,openai_api_key:str,  max_tokens: int = 2048, temperature: float = 0.7, frequency_penalty:float = 0.0, model:str = SMART_MODEL, max_calls:int = 5) -> str:
    """
    Chained implementation of the llm api call for long outputs. Iteratively feeds output of an llm api call back into the model until the output is complete.  
    """
    client = OpenAI() 
    client.api_key = openai_api_key
    combined_prompt = [{'role':'system', 'content':prompt}]
    responses, finishes = [],[] 
    finish = None 
    num_calls = 0 
    
    # #use smart model if we exceed a certain context length. Assume 4 chars is about 1 token. 
    # current_context_chars = len(prompt)
    # max_fast_model_context = 4 * 10000

    while finish != 'stop' and num_calls < max_calls: 
        num_calls += 1 
        # if current_context_chars > max_fast_model_context:
        #     model = SMART_MODEL
        #     print("Swapped to larger model for increased context")
        print("Calling Model...")
        response = client.chat.completions.create(
            model=model,
            messages = combined_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            frequency_penalty=frequency_penalty)
        print(f"Got resopnse! Call #:{num_calls}")
        string_response = response.choices[0].message.content
        print(f"Last Line:{string_response.splitlines()[-1]}")
        print(f"Response Length: {len(string_response)} chars")
        # current_context_chars += len(string_response)
        responses.append(string_response) 
        finish = response.choices[0].finish_reason 
        finishes.append(finish)
        print(f"End reason: {finish}")
        new_message = {'role': 'user', 
                       'content': string_response}
        combined_prompt.append(new_message)
        print(f"Num of messages in prompt:{len(combined_prompt)}")
    output = "".join(responses)
    return output 

def sample_book(openai_api_key:str) -> Book:
    """
    Returns a sample Book object with non-emoji parameters autofilled 
    """ 
    book = Book("Crime and Punishment")
    book.llm_autofill(openai_api_key) 
    book.recs.append("Johnny")
    return book 

def sample_booklist(openai_api_key:str) -> List: 
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
        book.llm_autofill(openai_api_key)
    return booklist 

def _extract_titles(path_to_folder: str) -> List[str]:
    """
    Extract book titles from txt files in a folder. Assumes each txt file contains EXACTLY
    only book titles separated by new lines.
    """
    titles = []
    # Iterate through each file in the specified folder
    for filename in os.listdir(path_to_folder):
        # Check if the file is a .txt file
        if filename.endswith(".txt"):
            # Construct the full path to the file
            file_path = os.path.join(path_to_folder, filename)
            # Open and read the file
            with open(file_path, 'r', encoding='utf-8') as file:
                # Read the file's content, strip extra whitespace, and split by new lines
                file_contents = file.read().strip()
                titles_in_file = file_contents.split('\n')
                # Extend the main titles list with the titles from this file
                titles.extend(titles_in_file)
    # Remove duplicate titles 
    titles = set(titles)
    # Return the set of titles
    return titles

def pick_random_name_and_capitalize(names: list) -> str:
    """
    Picks a random name from a provided list and returns it with the first letter capitalized.

    :param names: List of names (strings)
    :return: Randomly selected name with the first letter capitalized
    """
    # Ensure the list is not empty
    if not names:
        return "The name list is empty."
    
    # Pick a random name
    random_name = random.choice(names)
    
    # Return the name with the first letter capitalized
    return random_name.capitalize()

# generate a string representing a synthetic booklist of unique books. Adds synthetic recommendations and an output txt file if specified. 
def synthetic_booklist(num_books:int, openai_key:str, status:bool = False, recs:bool = False, write:bool=False) -> str: 
    path_to_folder = repo_root/'data'/'test'/'book_titles'
    possible_books = _extract_titles(path_to_folder)
    num_possible_books = len(possible_books)
    print(f"Number of possible books:{num_possible_books}")
    
    booklist_string = "" 
    booklist = [] 
    # booklist of unique books 
    picked = random.sample(possible_books, num_books)
    for title in tqdm(picked, "filling details"): 
        book = Book(title)
        book.llm_autofill(openai_key) 
        booklist.append(book)
    
    for book in tqdm(booklist, "constructing lines"): 
        # randomly pick a status if specified
        status_string = '' if not status else random.sample({"Complete", "In Progress", "Not Started"},1)
        # randomly add a recommender if specified 
        recs_string = '' if not recs else random.sample({'', pick_random_name_and_capitalize(names_list)},1)
        s = f"{book.title}:{book.blurb}\n"+f"{recs_string}, {status_string}\n"
        booklist_string += s

    # check if writing and output 
    if write: 
        synthetic_title = f"synthetic_booklsit_{num_books}{'r' if recs else ''}{'s' if status else ''}"
        with open(synthetic_title, "w") as file:
            file.write(booklist_string)

    return booklist_string
