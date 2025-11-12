# Confluence Public Page Searcher - Change Request

This is a change request to implement automated testing for the Confluence Public Page Searcher application.

## End Goals

We want to sample ~10% of the resulting links so that we can verify that the searcher has worked properly. 

## Inputs

We have an existing script which was implemented in Python. We have a PRD and a System Design for that application, which are attached. 

## Basic Requirements

- This process should be relatively quick (we likely want concurrency)
- We should not be sending large per-second volumes, as this site may block us

