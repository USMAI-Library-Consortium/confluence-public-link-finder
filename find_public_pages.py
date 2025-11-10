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
OUTPUT_FILENAME = "public_pages.csv"
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

    # Keep fetching pages as long as a 'next' link is provided
    while next_page_url:
        try:
            # Make the anonymous GET request
            response = requests.get(next_page_url)

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


def process_page_data(raw_results, base_url):
    """
    Filters the raw API results for "page" type and extracts title and URL.

    Args:
        raw_results (list): List of raw item dictionaries from the API.
        base_url (str): The base Confluence URL to build full URLs.

    Returns:
        list: A list of (title, url) tuples.
    """
    cleaned_pages = []
    for item in raw_results:
        try:
            # We only care about items that are a 'page'
            if item.get('type') == 'page':
                title = item['title']
                # The webui link is relative, needs the base URL
                relative_url = item['_links']['webui']
                full_url = base_url + relative_url

                cleaned_pages.append((title, full_url))
        except KeyError as e:
            # This handles items that are 'page' type but missing a title or link
            print(f"Warning: Skipping an item due to missing data (KeyError: {e}).")

    return cleaned_pages


def write_to_csv(pages_list, filename):
    """
    Writes the list of (title, url) tuples to a CSV file.

    Args:
        pages_list (list): The list of (title, url) tuples.
        filename (str): The name of the CSV file to create.

    Raises:
        PermissionError: If the file cannot be written.
    """
    try:
        # PRD Story 2: Create a single CSV file
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write headers
            writer.writerow(["Page Title", "Page URL"])

            # Write all the page data
            writer.writerows(pages_list)

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

        # 2. Transform
        print(f"\nProcessing {len(raw_data)} items to find pages...")
        public_pages = process_page_data(raw_data, base_url)

        if not public_pages:
            print("\nScan complete! No public pages were found.")
            sys.exit(0)

        # 3. Load
        print(f"Writing {len(public_pages)} public pages to {OUTPUT_FILENAME}...")
        write_to_csv(public_pages, OUTPUT_FILENAME)

        # PRD Step 5: Final Success Message
        print("\n---")
        print(f"Scan complete! Found {len(public_pages)} public pages.")
        print(f"Your report is ready: {OUTPUT_FILENAME}")
        print("---")

    except (RequestException, PermissionError):
        # Errors are already printed by the functions that raised them.
        print("\nScan failed. Please fix the error above and try again.")
        sys.exit(1)
    except Exception as e:
        # Catch any other unexpected error
        print(f"\nAn fatal, unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()