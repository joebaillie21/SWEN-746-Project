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
    github_client = Github(token)
    try:
      repo = github_client.get_repo(repo_name)
    except Exception as e:
      raise ValueError(f"Error accessing repository '{repo_name}': {e}")

    # 3) Fetch commit objects (paginated by PyGitHub)
    commits = []
    for commit in repo.get_commits():
      if max_commits and len(commits) >= max_commits:
        break
      commits.append(commit)

    # 4) Normalize each commit into a record dict
    records = []
    for commit in commits:
      commit_data = {
        "sha": commit.sha,
        "author": commit.author.name if commit.author else None,
        "email": commit.author.email if commit.author else None,
        "date": commit.commit.author.date,
        "message": commit.commit.message,
      }
      records.append(commit_data)

    # 5) Build DataFrame from records
    return pd.DataFrame.from_records(records, columns=["sha", "author", "email", "date", "message"])
    

def main():
   parser = argparse.ArgumentParser(
        prog="repo_miner",
        description="Fetch GitHub commits/issues and summarize them")
   subparsers = parser.add_subparsers(dest="command", required=True)

    # Sub-command: fetch-commits
   c1 = subparsers.add_parser("fetch-commits", help="Fetch commits and save to CSV")
   c1.add_argument("--repo", required=True, help="Repository in owner/repo format")
   c1.add_argument("--max",  type=int, dest="max_commits",
                  help="Max number of commits to fetch")
   c1.add_argument("--out",  required=True, help="Path to output commits CSV")

   args = parser.parse_args()

  # Dispatch based on selected command
   if args.command == "fetch-commits":
      df = fetch_commits(args.repo, args.max_commits)
      df.to_csv(args.out, index=False)
      print(f"Saved {len(df)} commits to {args.out}")

if __name__ == "__main__":
    main()
