#!/usr/bin/env python3

"""
Confluence Public Page Finder
This script scans a Confluence Server/Data Center instance to find all pages
that are accessible to the public (i.e., anonymously, without a login).
It loops through the Confluence API's /rest/api/content endpoint and
generates a CSV report of all discoverable public pages.
"""

import sys
import csv
import requests
from requests.exceptions import ConnectionError, HTTPError, RequestException

# --- CONFIGURATION ---
# The *full* base URL of your Confluence site.
# Example: "https://confluence.usmai.org"
CONFLUENCE_BASE_URL = "https://usmai.org/portal"

# The API endpoint to start scanning from.
API_START_ENDPOINT = "/rest/api/content"

# The name of the output file.
OUTPUT_FILENAME = "non_archived_public_pages.csv"

# Page Counts CSV Filename
PAGE_COUNTS_FILE = "PageCountViews.csv"

# List of space keys to exclude from the final report, per RFC-3.
ARCHIVED_SPACES = ['COV19', 'DR', 'NEXTILS']

# The year threshold for highlighting archivable candidates, per RFC-4.
# Any page last modified in or before this year will be marked.
ARCHIVE_THRESHOLD_YEAR = 2019
# --- END CONFIGURATION ---


def fetch_all_public_pages(start_url):
    """
    Fetches all paginated, anonymous results from the Confluence API.

    This function makes unauthenticated requests, so it only receives
    data that is visible to an anonymous user.

    Args:
        start_url (str): The initial API URL to query.

    Raises:
        HTTPError: If the server returns a 4xx or 5xx error.
        ConnectionError: If the script cannot connect to the server.
        RequestException: For other 'requests' related errors.
        KeyError: If the API response format is unexpected.

    Returns:
        list: A list of all raw "result" dictionaries from the API.
    """
    print(f"Starting anonymous scan at: {start_url}")
    all_results = []
    next_page_url = start_url
    page_count = 1

    # RFC-5: Added history.createdBy to fetch creator details
    initial_params = {'type': 'page', 'expand': 'history.lastUpdated,history.createdBy'}

    # Keep fetching pages as long as a 'next' link is provided
    while next_page_url:
        try:
            # Only apply the initial_params on the *first* request.
            # Subsequent 'next_url' values from the API will already include
            # all necessary parameters.
            params = initial_params if next_page_url == start_url else None

            # Make the anonymous GET request
            response = requests.get(next_page_url, params=params)

            # Check for HTTP errors (e.g., 404, 500)
            response.raise_for_status()

            data = response.json()

            # Add results from this page
            results = data.get('results', [])
            if results:
                all_results.extend(results)
                # PRD Story 4: Show progress
                print(f"  ... Fetched page {page_count} ({len(results)} items)")
            else:
                print("  ... No results on this page.")

            # Find the URL for the next page of results
            if 'next' in data.get('_links', {}):
                # The 'next' link is relative, so we build the full URL
                next_page_url = CONFLUENCE_BASE_URL.rstrip('/') + data['_links']['next']
                page_count += 1
            else:
                next_page_url = None  # We are done, stop the loop

        except HTTPError as http_err:
            # PRD Story 5: Helpful Errors
            if http_err.response.status_code == 404:
                print(f"\nError: The API endpoint returned a 404 (Not Found).")
                print(f"Failed URL: {next_page_url}")
                print(f"Is the API_START_ENDPOINT ('{API_START_ENDPOINT}') correct?")
            elif http_err.response.status_code >= 500:
                print(f"\nError: The Confluence server returned a {http_err.response.status_code} error.")
                print("The site may be down or experiencing issues. Please try again later.")
            else:
                print(f"\nAn HTTP error occurred: {http_err}")
            raise  # Re-raise to be caught by main
        except ConnectionError:
            # PRD Story 5: Helpful Errors
            print(f"\nError: Could not connect to {CONFLUENCE_BASE_URL}.")
            print("Please check the CONFLUENCE_BASE_URL and your internet connection.")
            raise  # Re-raise
        except (KeyError, ValueError):
            # KeyError if 'results' or '_links' is missing
            # ValueError if response is not valid JSON
            print(f"\nError: The API response was in an unexpected format.")
            print("The Confluence API may have changed or the URL is incorrect.")
            raise  # Re-raise

    print(f"Finished fetching. Found {len(all_results)} total items.")
    return all_results

def extract_page_counts_dict(page_counts_file):
    dictionary = {}

    with open(page_counts_file, newline='') as f:
        countreader = csv.reader(f)

        for row in countreader:
            if row[8] != 'Views':
                dictionary[row[1]] = int(row[8])

    return dictionary

def process_page_data(raw_results: list[dict], base_url, archive_year_threshold: int, page_counts):
    """
    Filters the raw API results for "page" type and extracts title and URL.

    Per RFC-3, this function also filters out pages from archived spaces.

    Args:
        raw_results (list): List of raw item dictionaries from the API.
        base_url (str): The base Confluence URL to build full URLs.
        active_year_threshold (int): Threshold for marking a page as not being modified in a while

    Returns:
        list: A list of dictionaries containing the data for a page.
    """
    cleaned_pages: list[dict] = []
    print(f"  -> Processing {len(raw_results)} items. Filtering archived spaces...")
    
    for item in raw_results:
        try:
            # --- Start: RFC-3 Change ---
            # The 'space' path is like '/rest/api/space/SYSTEMS'
            # We split by '/' and take the last part to get the space key.
            space_key = item['_expandable']['space'].split('/')[-1]

            # If the space is in the archived list, skip this item
            if space_key in ARCHIVED_SPACES:
                continue
            # --- End: RFC-3 Change ---

            # If not archived, proceed
            title = item['title']

            view_count = page_counts.get(title, 0)

            # The webui link is relative, needs the base URL
            relative_url = item['_links']['webui']
            full_url = base_url + relative_url

            # RFC-5 - Extract Creator Name
            # We use .get() chains to avoid KeyErrors if data is missing or user is anonymous
            creator_name = item.get('history', {}).get('createdBy', {}).get('displayName', 'Unknown/Anonymous')

            # RFC-5 - Extract Last Modifier Name
            modifier_name = item.get('history', {}).get('lastUpdated', {}).get('by', {}).get('displayName', 'Unknown/Anonymous')

            # RFC-4: Check if the page is a candidate for archiving
            is_archivable = False  # Default
            try:
                # The 'when' field is an ISO 8601 string: "2018-05-15T14:42:15.839Z"
                last_updated_str = item['history']['lastUpdated']['when']
                # We only need the year, so we split the string and take the first part
                last_updated_year = int(last_updated_str.split('-')[0])
                
                if last_updated_year <= archive_year_threshold:
                    is_archivable = True
            except (KeyError, IndexError, TypeError, ValueError):
                # Handle pages with missing history or unexpected date formats
                print(f"Warning: Could not determine last-modified date for '{title}'.")
        
            # RFC-5: Added creator_name and modifier_name to the tuple
            cleaned_pages.append({
                "title": title,
                "full_url": full_url,
                "creator_name": creator_name,
                "last_modifier_name": modifier_name,
                "is_archivable": is_archivable,
                "view_count": view_count
            })
        
        except KeyError as e:
            # This handles items missing a title, link, or expandable container
            print(f"Warning: Skipping an item due to missing data (KeyError: {e}).")

    print(f"  -> Found {len(cleaned_pages)} non-archived public pages.")
    return cleaned_pages


def write_to_csv(pages_list: list[dict], filename):
    """
    Writes the list of dictionaries to a CSV file. Sorts them by viewcount, descending first.

    Args:
        pages_list (list): The list of page data dictionaries.
        filename (str): The name of the CSV file to create.

    Raises:
        PermissionError: If the file cannot be written.
    """
    # Sort by descending viewcount so that we can prioritize high-traffic pages 
    pages_list.sort(key=lambda x: x['view_count'], reverse=True)

    try:
        # PRD Story 2: Create a single CSV file
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write headers
            writer.writerow(["Page Title", "Page URL", "Creator", "Last Modifier", "View Count", "Last Modified 6+ Years Ago?"])

            # Write all the page data
            # We loop manually to format the boolean as 'Yes' or an empty string
            for page_info in pages_list:
                # RFC-4: Create status for whether a page is a likely candidate for archiving.
                archive_status = "Yes" if page_info["is_archivable"] else ""
                writer.writerow([page_info["title"], page_info["full_url"], page_info["creator_name"], page_info["last_modifier_name"], page_info["view_count"], archive_status])

    except PermissionError:
        # PRD Story 5: Helpful Errors
        print(f"\nError: Could not write to {filename}.")
        print("Is the file already open in Excel, or is the folder read-only?")
        raise  # Re-raise
    except Exception as e:
        print(f"\nAn unexpected error occurred while writing the file: {e}")
        raise  # Re-raise


def main():
    """
    Main function to orchestrate the scan and report generation.
    """
    print("--- Confluence Public Page Finder ---")

    # Basic validation of the base URL
    if not CONFLUENCE_BASE_URL or not CONFLUENCE_BASE_URL.startswith("http"):
        print(f"Error: CONFLUENCE_BASE_URL ('{CONFLUENCE_BASE_URL}') seems invalid.")
        print("It must start with 'http://' or 'https://'.")
        sys.exit(1)

    # Clean trailing slash if present, to avoid double slashes
    base_url = CONFLUENCE_BASE_URL.rstrip('/')
    start_url = base_url + API_START_ENDPOINT

    try:
        # 1. Extract
        raw_data = fetch_all_public_pages(start_url)
        raw_page_counts_info = extract_page_counts_dict(PAGE_COUNTS_FILE)

        # 2. Transform
        print(f"\nProcessing {len(raw_data)} items to find pages...")
        public_pages = process_page_data(raw_data, base_url, ARCHIVE_THRESHOLD_YEAR, raw_page_counts_info)

        if not public_pages:
            print("\nScan complete! No public pages were found.")
            sys.exit(0)

        # 3. Load
        print(f"Writing {len(public_pages)} public pages to {OUTPUT_FILENAME}...")

        # --- Start: RFC-4 Change ---
        # Count archivable candidates for the final report
        archive_candidate_count = sum(1 for page in public_pages if page["is_archivable"]) # page[4] is the boolean
        print(f"  -> Of these, {archive_candidate_count} pages are candidates for archiving (modified in or before {ARCHIVE_THRESHOLD_YEAR}).")
        # --- End: RFC-4 Change ---

        write_to_csv(public_pages, OUTPUT_FILENAME)

        # PRD Step 5: Final Success Message
        print("\n---")
        print(f"Scan complete! Found {len(public_pages)} public pages.")
        print(f"({archive_candidate_count} are potential archive candidates)")
        print(f"Your report is ready: {OUTPUT_FILENAME}")
        print("---")

    except (RequestException, PermissionError):
        # Errors are already printed by the functions that raised them.
        print("\nScan failed. Please fix the error above and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()