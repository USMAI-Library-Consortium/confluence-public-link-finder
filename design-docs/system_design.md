# System Design: Confluence Public Page Finder

This document outlines the system design for a Python script that identifies all publicly accessible pages on a Confluence (Server/Data Center) instance. This design is based on the provided PRD and API format.

## 1. Overview & Architecture

The system will be a single, standalone Python script. The user will configure their base Confluence URL at the top of the file and run the script from their terminal.

The script's architecture is based on a simple **Extract, Transform, Load (ETL)** process:

1.  **Extract:** Iteratively fetch all paginated results from the Confluence `/rest/api/content` endpoint, querying only for pages. Critically, these requests are made **anonymously** (without authentication), so the API will only return content visible to the public. We also want to pull what space this page belongs to.
2.  **Transform:** Parse the collected JSON responses. For each item, filter for non-archived content and extract the `title` and `_links.webui`. The `webui` relative path will be combined with the `CONFLUENCE_BASE_URL` to create a full, clickable URL.
3.  **Load:** Write the transformed list of (Title, URL) pairs into a single `.csv` file in the same directory.

## 2. Core Technology Stack

To maintain simplicity as requested, the script will rely only on standard Python libraries and one common external library.

* **Language:** Python 3.x
* **Libraries:**
    * `requests`: To make HTTP GET requests to the Confluence API.
    * `csv`: (Python built-in) To write the data to a `.csv` file.
    * `sys`: (Python built-in) To print feedback and exit on critical errors.

## 3. Component Design (Script Structure)

The script will be organized into logical functions.

### 3.1. Configuration (Global)

A set of clearly marked variables will be placed at the top of the file, as requested in Story 3.

```python
# --- CONFIGURATION ---
# The *full* base URL of your Confluence site.
# Example: "[https://confluence.usmai.org](https://confluence.usmai.org)"
CONFLUENCE_BASE_URL = "[https://confluence.usmai.org](https://confluence.usmai.org)"

# The API endpoint to start scanning from.
API_START_ENDPOINT = "/rest/api/content"

# The name of the output file.
OUTPUT_FILENAME = "public_pages.csv"

# List of space keys to exclude from the final report due to them being archived, per RFC-3.
ARCHIVED_SPACES = ['COV19', 'DR']
# --- END CONFIGURATION ---
```

### 3.2. Main Function

This function will orchestrate the entire process and include top-level error handling.

The function will have a try/accept architecture to catch errors thrown by any of the E, T, or L processes. 

Tasks: 
1. Call fetch_all_public_pages() to get the raw page data.
2. Call process_page_data() to clean the data.
3. Call write_to_csv() to save the file.
4. Print final success message.

Exception Handling:
- ConnectionError, HTTPError, etc - print a helpful error message and exit. 

### 3.3. API Fetcher

This function will handle the loop for pulling the URLs from the Confluence API. It will use the `type=page` query param to only pull content that are the 'page' type. 

Function Definition: `fetch_all_public_pages(url)`

INPUTS:
- `start_url`: The URL that the function should start with

OUTPUTS:
- `pages`: a list of all page data

Loop Architecture: 
1. Make an unauthenticated requests.get() call.
2. Check for HTTP errors (e.g., 404, 500).
3. Parse the JSON response.
4. Add the contents of the results array to `pages`
5. Update the progress.
6. Get the next URL from `_links.next`. If the key doesn't exist, terminate the loop.

### 3.4. Data Processor

Logic: This function transforms the raw API data into the simple CSV format.

`process_page_data(raw_pages_list, base_url)`

INPUTS:
- `raw_pages_list`: The list of all page data pulled by the process described in 4.3
- `base_url`: Confluence Base URL, used for constructing the URL that will be added to the output file.

OUTPUTS:
- `cleaned_pages`: list of tuples (str, str): A list of Page Titles and their corresponding URLS.

Loop Architecture:
1. Extract the Space Key from the `item["_expandable"]["container"]` path, which is in the format `/rest/api/space/SYSTEMS` with `SYSTEMS` being the desired key. 
2. Check whether a page is archived by comparing the space with a list of archived spaces. The list, for all intents and purposes, is static to `['COV19', 'DR']`
3. If a page is NOT archived, extract title and relative URL & proceed with the following steps
4. Generate full URL with `base_url` plus relative URL
5. Append the tuple of Title and Full URL to the `cleaned_pages`

### 3.5. CSV Writer

Writes the data to the CSV.

INPUTS:
- `cleaned_pages` list of tuples (str, str): A list of Page Titles and their corresponding URLS.
- `filename` str: The filename to write.

Logic:
1. Use `csv` module to open the file
2. Write headers `["Page Title", "Page URL"]`
3. Save all processed page data

## 4. Error Handling Strategy

This design directly addresses "Helpful Errors" (Story 5).

Error Condition,Trigger,User Message
Connection Error,requests.exceptions.ConnectionError,"""Error: Could not connect to [URL]. Please check the CONFLUENCE_BASE_URL and your internet connection."""
Invalid API URL,HTTP 404 (Not Found),"""Error: The API endpoint returned a 404 (Not Found). Is the API_START_ENDPOINT correct?"""
Site Down,HTTP 5xx (Server Error),"""Error: The Confluence server returned a [Code] error. The site may be down. Please try again later."""
Permissions Error,PermissionError (on file write),"""Error: Could not write to [filename]. Is the file already open in Excel, or is the folder read-only?"""
Unexpected Data,"KeyError (e.g., results not in JSON)","""Error: The API response was in an unexpected format. The Confluence API may have changed."""