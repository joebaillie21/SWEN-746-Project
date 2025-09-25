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
import github
from github import Github
import pandas as pd
import ghtoken
import sys

def fetch_commits(repo_name: str, max_commits: int = None) -> pd.DataFrame:
    """
    Fetch up to `max_commits` from the specified GitHub repository.
    Returns a DataFrame with columns: sha, author, email, date, message.
    """
    # 1) Read GitHub token from environment
    token = None

    # A) Attempt to get a token from the .env file
    try:
      token = ghtoken.ghtoken_from_dotenv()
    except:
        print('No token found from .env file.')

    # B) If token was not retrieved from .env, get from environment var
    if not token:
        try:
          token = os.environ.get('GITHUB_TOKEN')
        except:
          print('No token found from environment. Exitting...')
          sys.exit(0)
        


    # 2) Initialize GitHub client and get the repo
    instance = Github(auth=github.Auth.Token(token))
    repo = instance.get_repo(repo_name)

    # 3) Fetch commit objects (paginated by PyGitHub)
    commits = repo.get_commits()

    # 4) Normalize each commit into a record dict
    records = []
    count = 0
    for commit in commits:
        if max_commits and count >= max_commits:
          break
        record = {
            'sha' : commit.sha,
            'author' : commit.author.name if commit.author else None,
            'email' : commit.author.email if commit.author else None,
            'date' : commit.commit.author.date,
            'message' : commit.commit.message
          }
        records.append(record)
        count+=1
       
       

    # 5) Build DataFrame from records
    df = pd.DataFrame(records)

    return df
    

def main():
    """
    Parse command-line arguments and dispatch to sub-commands.
    """
    parser = argparse.ArgumentParser(
        prog="repo_miner",
        description="Fetch GitHub commits/issues and summarize them"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # # Sub-command: fetch-commits
    c1 = subparsers.add_parser("fetch-commits", help="Fetch commits and save to CSV")
    c1.add_argument("--repo", required=True, help="Repository in owner/repo format")
    c1.add_argument("--max",  type=int, dest="max_commits",
                    help="Max number of commits to fetch")
    c1.add_argument("--out",  required=True, help="Path to output commits CSV")

    args = parser.parse_args()

    # # Dispatch based on selected command
    if args.command == "fetch-commits":
        df = fetch_commits(args.repo, args.max_commits)
        df.to_csv(args.out, index=False)
        print(f"Saved {len(df)} commits to {args.out}")

if __name__ == "__main__":
    main()
