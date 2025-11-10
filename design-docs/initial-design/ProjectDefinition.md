# Confluence Public Page Searcher

We at USMAI are planning on migrating our Confluence site from self-hosted to Cloud. Our Confluence is designed both as an 'intranet' but also a documentation repository. Some of the pages are public (viewable by anyone on the web), while others require logins with specific permissions. 

As part of our migration, we must figure out which of our ~5200 pages are public. All pages that are not public require logging in to Confluence. 

## End Goals

Main Goal: We would like to retrieve a list of page URLs that are public.

## Project Meta-Info

- This does not need to be a script, but it could
- If there's an existing way to get this information, that would be preferred

## Technical Information

We are running Confluence Data Center 9.2.8. What we know about Confluence that is relevant to this project is this:
- The application has an API
- The API shares permissions with the web UI:

"Accessing Confluence using the REST API involves the same authentication and permissions checks that are required when accessing Confluence in your browser. If you don't log in, you are accessing Confluence anonymously. If you log in but don't have permission to view a particular page or space for example, you will not be able to view it using the Confluence REST API either.

For personal use and scripts, you can use basic authentication with either a username and password, or by creating a personal access token (available from Confluence Data Center 7.9)."

- There is a way to get who has permissions to access a page via the API. However, it will require a follow-up request. 

