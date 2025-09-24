#!/usr/bin/env python3
"""
repo_miner.py

A command-line tool to:
  1) Fetch and normalize commit data from GitHub

Sub-commands:
  - fetch-commits
"""

import os
import argparse
import pandas as pd
from github import Github

def fetch_commits(repo_name: str, max_commits: int = None) -> pd.DataFrame:
    """
    Fetch up to `max_commits` from the specified GitHub repository.
    Returns a DataFrame with columns: sha, author, email, date, message.
    """
    # 1) Read GitHub token from environment
    token = os.getenv("GITHUB_TOKEN")
    if not token:
      raise EnvironmentError("GITHUB_TOKEN environment variable not set")
    print(token)


    # 2) Initialize GitHub client and get the repo
    # TODO

    # 3) Fetch commit objects (paginated by PyGitHub)
    # TODO

    # 4) Normalize each commit into a record dict
    # TODO

    # 5) Build DataFrame from records
    # TODO
    

def main():
   fetch_commits(None, None)

if __name__ == "__main__":
    main()
