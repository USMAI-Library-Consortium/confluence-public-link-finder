# PRD: Confluence Public Page Finder

## 1. 🎯 The Goal (Why We're Building This)

Before we move our Confluence site to the cloud, we *must* know which of our ~5200 pages are visible to the public. We need a simple tool that can generate a list of every page anyone on the internet can see.

**The main goal is to get a simple list of public URLs and Page Names that we can open in Excel.**

---

## 2. 👤 The User & Their Needs (User Stories)

The primary user is a **Confluence Administrator** or a **Migration Team Member**.

* **Story 1: The "Anonymous" Scan**
    > **As an** Admin,
    > **I want** a tool that scans our Confluence site *as if it were a random person on the internet* (with no login),
    > **so that** the list it generates *only* includes pages that are truly public.

* **Story 2: The Simple List**
    > **As an** Admin,
    > **I want** the tool to create a **single CSV file** (that I can open in Excel),
    > **so that** I can easily search, filter, sort, and share the list of public pages with my team.

* **Story 3: Easy Setup**
    > **As an** Admin,
    > **I want** to easily **tell the tool my Confluence site's address** (e.g., `https://confluence.usmai.org`) in one obvious place,
    > **so that** I don't have to hunt through code just to run it.

* **Story 4: Clear Feedback**
    > **As an** Admin,
    > **I want** the tool to **show me its progress** as it's running.
    > **so that** I know it's working and hasn't frozen.

* **Story 5: Helpful Errors**
    > **As an** Admin,
    > **I want** the tool to **give me a clear message** if something goes wrong (like I typed the URL wrong or the site is down),
    > **so that** I can fix the problem and try again without guessing.

---

## 3. 🗺️ The Workflow (How It Will Be Used)

This describes the step-by-step experience of the administrator using this script.

1.  **Step 1: Setup (One-time)**
    * The admin gets the script file (e.g., `find_public_pages.py`) and places it in a folder on their computer.
    * They ensure they have Python and the `requests` library installed (a simple one-line command).

2.  **Step 2: Configuration**
    * The admin opens the script file in a simple text editor.
    * At the very top, they find a clearly marked variable called `CONFLUENCE_BASE_URL` and change it to their site's address (e.g., `https://confluence.usmai.org`).
    * They save and close the file.

3.  **Step 3: Running the Scan**
    * The admin opens their computer's terminal (or Command Prompt).
    * They navigate to the folder containing the script.
    * They type `python find_public_pages.py` and press Enter.

4.  **Step 4: Getting Feedback**
    * The script immediately starts running and prints updates to the screen. 
    * It would be preferred, if the API returns resumption or progress, to say what percentage the script has completed. 

5.  **Step 5: Getting the Results**
    * After a few minutes, the script finishes and prints a final message:
        > `Scan complete! Found 234 public pages.`
        > `Your report is ready: public_pages.csv`

6.  **Step 6: Auditing the List**
    * The admin finds the new `public_pages.csv` file in the same folder.
    * They double-click to open it in Excel.
    * The file has two simple columns: **`Page Title`** and **`Page URL`**.
    * To verify, the admin copies a URL from the list, opens a **new incognito/private browser window**, pastes the URL, and confirms the page loads without asking for a login.

---

## 4. ✅ What "Done" Looks Like (Success)

We'll know this tool is successful when...

* ✅ An admin can **run the script without help** from a developer.
* ✅ The script produces a **`public_pages.csv` file**.
* ✅ When we open a URL from the CSV in an **incognito window, the page loads**.
* ✅ When we check a known *private* page, its URL **is not** in the CSV.
* ✅ The list from the CSV can be used as the official "public page list" for the migration audit.