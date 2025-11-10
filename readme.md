Here is the content formatted in Markdown:

## Confluence Public Page Auditor

This project provides a two-script utility for finding and verifying publicly accessible pages on a Confluence Server or Data Center instance.

### 1. Public Page Finder

This Python script scans the Confluence `/rest/api/content` endpoint anonymously. It finds all publicly visible pages and writes their titles and URLs to a `public_pages.csv` file. The script handles API pagination and builds full, clickable URLs for the output file.

### 2. Confluence Page Verifier

This script complements the first by automating the audit process. It reads the generated `public_pages.csv` file, takes a random 10% sample of the URLs, and attempts to access them anonymously to confirm they are still public.

To run quickly without being blocked, the script uses:
* **Concurrency:** A `ThreadPoolExecutor` to make many HTTP requests in parallel.
* **Rate Limiting:** A `Semaphore` to limit simultaneous requests (e.g., 5 at a time) and avoid being blocked.

The script reports a final summary of which sampled links passed (returned a 200 OK status) and which failed (e.g., 403 Forbidden, 404 Not Found, or a connection error).

---

## How to Use

**Step 1: Find Public Pages**

1.  Open the first script (e.g., `find_public_pages.py`).
2.  Update the `CONFLUENCE_BASE_URL` variable at the top with your site's URL.
3.  Run the script from your terminal: `python find_public_pages.py`
4.  Wait for it to complete. A `public_pages.csv` file will be created in the same directory.

**Step 2: Verify the Results**

1.  Open the second script (e.g., `verify_pages.py`).
2.  You can adjust the `SAMPLE_PERCENT` or `MAX_CONCURRENT_REQUESTS` at the top if needed.
3.  Run the script: `python verify_pages.py`
4.  The script will test a sample of the links from the CSV and print a summary report to your terminal, highlighting any failures.