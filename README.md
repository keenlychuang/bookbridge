<div align="center">
    <img src="./assets/icon_color.png" alt="Icon Alt Text" title="Icon Title" width="256"/>
</div>

# BookBridge - Booklist Import Tool

# Booklist Import Tool

Transform your old booklists into a dynamic Notion database with the Booklist Import Tool.  Organize, share, and rediscover your reading history with the help of cutting-edge language models.

## Background and Overview

As an avid reader, I've accumulated a substantial list of books over the years, categorizing them by what I wanted to read, what I had completed, and the type of books they are. With an intention to share my reading journey more publicly and to organize my collection with greater sophistication, I've chosen Notion as the platform for its unparalleled ability to present, store, and share information. On top of being a pleasure to look at, Notion pages are easy to share, publish, modify, and update, and has robust API support for people with more technical inclination. Not sponsored, btw. 

## Installation

To get started with BookBridge, follow these simple installation instructions.

### Prerequisites

- Python 3.7 or higher
- Pip (Python package installer)

### Steps

1. Clone this repository to your local machine using:
   ```
   git clone https://github.com/yourusername/bookbridge.git
   ```
2. Navigate to the cloned directory:
   ```
   cd bookbridge
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To use BookBridge to import your booklist into a Notion database, follow these steps:

1. Obtain an integration token from Notion by creating a new integration.
2. Obtain an API key from OpenAI to use LLMs. This iteration uses `gpt-4-turbo`. 
3. Obtain the URL of the Notion page you want to import the booklist into. If you're new to Notion, the [https://www.notion.so/help/category/new-to-notion](getting started) page is a good place to begin. 
3. Run the tool using the command:
   ```
   python bookbridge.py
   ```

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

K. Simon Chuang - keenlyschuang@gmail.com

Project Link: [https://github.com/keenlychuang/bookbridge](https://github.com/keenlychuang/bookbridge)

## Acknowledgements

- [Notion API](https://developers.notion.com/)
- [Your other dependencies or resources]