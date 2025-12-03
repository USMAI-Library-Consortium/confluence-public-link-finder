import csv
import random
import sys
import threading
import requests
from requests.exceptions import RequestException
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- CONFIGURATION ---
# The file to read from (should match OUTPUT_FILENAME from the first script)
INPUT_FILENAME = "non_archived_public_pages.csv"

# What percentage of links to sample for verification.
# 0.1 = 10%, 0.25 = 25%, etc.
SAMPLE_PERCENT = 0.1

# How many requests to run at the same time.
# Keeps us from getting rate-limited or blocked.
MAX_CONCURRENT_REQUESTS = 5
# --- END CONFIGURATION ---

def check_link(url, title, semaphore):
    """
    Worker function to check a single URL.
    Acquires a semaphore to limit concurrency.
    """
    try:
        # Wait to acquire the semaphore (limits concurrent requests)
        with semaphore:
            # Using HEAD request to be lighter - we only need the status code
            response = requests.head(
                url, 
                allow_redirects=True, 
                timeout=10,
                # Act as an anonymous user (no session or auth cookies)
                headers={'User-Agent': 'Public-Page-Verifier-Script/1.0'}
            )

            # Check for successful status code
            if response.status_code == 200:
                print(f"  [PASS] {title}")
                return ("PASS", title, url)
            else:
                print(f"  [FAIL] {title} (Status: {response.status_code})")
                return ("FAIL", title, url, f"Error: Status code {response.status_code}")

    except RequestException as e:
        # Handle connection errors, timeouts, etc.
        print(f"  [FAIL] {title} (Error: {e.__class__.__name__})")
        return ("FAIL", title, url, f"Error: {e}")
    except Exception as e:
        # Catch any other unexpected errors
        print(f"  [FAIL] {title} (Unexpected Error: {e})")
        return ("FAIL", title, url, f"Unexpected Error: {e}")

def main():
    """
    Main orchestrator function.
    Loads CSV, samples URLs, runs concurrent checks, and prints a report.
    """
    print(f"--- Confluence Page Verifier ---")
    
    # --- 1. Load and Sample Pages ---
    try:
        with open(INPUT_FILENAME, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                header = next(reader) # Skip header
                if header != ["Page Title", "Page URL"]:
                    print(f"Warning: Unexpected CSV headers: {header}")
            except StopIteration:
                print(f"Error: CSV file '{INPUT_FILENAME}' is empty.")
                sys.exit(1)
                
            all_pages = [(row[0], row[1]) for row in reader if row] # [ (title, url) ]

    except FileNotFoundError:
        print(f"Error: Could not find the file '{INPUT_FILENAME}'.")
        print("Please run the 'find_public_pages.py' script first.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to read CSV file: {e}")
        sys.exit(1)

    if not all_pages:
        print("No pages found in the CSV. Nothing to verify.")
        sys.exit(0)

    # Calculate sample size
    total_pages = len(all_pages)
    sample_size = int(total_pages * SAMPLE_PERCENT)
    if sample_size == 0 and total_pages > 0:
        sample_size = 1 # Ensure we test at least one page if possible

    # Get the random sample
    pages_to_test = random.sample(all_pages, sample_size)
    print(f"Loaded {total_pages} pages. Sampling {sample_size} ({SAMPLE_PERCENT:.1%})...\n")

    # --- 2. Initialize Concurrency Tools ---
    semaphore = threading.Semaphore(MAX_CONCURRENT_REQUESTS)
    passed_links = []
    failed_links = []
    futures = []

    # --- 3. Run Concurrent Checks ---
    print(f"Starting verification with {MAX_CONCURRENT_REQUESTS} concurrent workers...")
    
    with ThreadPoolExecutor() as executor:
        # Submit all tasks to the thread pool
        for title, url in pages_to_test:
            futures.append(executor.submit(check_link, url, title, semaphore))

        # Process results as they complete
        for future in as_completed(futures):
            result = future.result()
            if result[0] == "PASS":
                passed_links.append(result)
            else:
                failed_links.append(result)

    # --- 4. Print Final Report ---
    print("\n--- Verification Complete: Final Report ---")
    print("=" * 40)
    print(f"  Total Links Checked: {sample_size}")
    print(f"  Passed: {len(passed_links)}")
    print(f"  Failed: {len(failed_links)}")
    print("=" * 40)

    if failed_links:
        print("\n🚨 FAILED LINKS (Details):\n")
        for _, title, url, error in failed_links:
            print(f"  Page:  {title}")
            print(f"  URL:   {url}")
            print(f"  Reason: {error}")
            print("-" * 20)
    else:
        print("\n✅ All sampled pages verified successfully!")


if __name__ == "__main__":
    main()