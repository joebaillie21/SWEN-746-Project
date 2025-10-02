#!/usr/bin/env python3
"""
repo_miner.py

A command-line tool to:
  1) Fetch and normalize commit data from GitHub

Sub-commands:
  - fetch-commits
"""

from datetime import datetime
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
    except Exception as e:
        print(e)

    # B) If token was not retrieved from .env, get from environment var
    if not token:
        try:
          token = os.environ.get('GITHUB_TOKEN')
        except Exception as e:
          print(e)
          return None

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
            'date' : commit.commit.author.date.isoformat() if commit.commit.author.date else None,
            'message' : commit.commit.message
          }
        records.append(record)
        count+=1
       
       

    # 5) Build DataFrame from records
    df = pd.DataFrame(records)

    return df
    
def fetch_issues(repo_name: str, state: str = "all", max_issues: int = None) -> pd.DataFrame:
    """
    Fetch up to `max_issues` from the specified GitHub repository (issues only).
    Returns a DataFrame with columns: id, number, title, user, state, created_at, closed_at, comments.
    """
    # 1) Read GitHub token from environment
    token = None

    # A) Attempt to get a token from the .env file
    try:
      token = ghtoken.ghtoken_from_dotenv()
    except Exception as e:
        print(e)

    # B) If token was not retrieved from .env, get from environment var
    if not token:
        try:
          token = os.environ.get('GITHUB_TOKEN')
        except Exception as e:
          print(e)
          return None

    # 2) Initialize GitHub client and get the repo
    instance = Github(auth=github.Auth.Token(token))
    repo = instance.get_repo(repo_name)

    # 3) Fetch issues, filtered by state ('all', 'open', 'closed')
    issues = repo.get_issues(state=state)

    # 4) Normalize each issue (skip PRs)
    records = []
    for idx, issue in enumerate(issues):
        if max_issues and idx >= max_issues:
            break
        # Skip pull requests
        if issue.pull_request:
            continue

        # Calculate open duration in days
        open_duration_days = None
        if issue.created_at and issue.closed_at:
            duration = issue.closed_at - issue.created_at
            open_duration_days = duration.days
           

        
        # Append records
        record = {
            'id': issue.id,
            'number': issue.number,
            'title': issue.title,
            'user': issue.user.login if issue.user else None,
            'state': issue.state,
            'created_at': issue.created_at.isoformat() if hasattr(issue.created_at, 'isoformat') else str(issue.created_at) if issue.created_at else None,
            'closed_at': issue.closed_at.isoformat() if hasattr(issue.closed_at, 'isoformat') else str(issue.closed_at) if issue.closed_at else None,
            'open_duration_days': open_duration_days,
            'comments': issue.comments
        }
        records.append(record)

    # 5) Build DataFrame
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

    c2 = subparsers.add_parser("fetch-issues", help="Fetch issues and save to CSV")
    c2.add_argument("--repo",  required=True, help="Repository in owner/repo format")
    c2.add_argument("--state", choices=["all","open","closed"], default="all",
                    help="Filter issues by state")
    c2.add_argument("--max",   type=int, dest="max_issues",
                    help="Max number of issues to fetch")
    c2.add_argument("--out",   required=True, help="Path to output issues CSV")

    args = parser.parse_args()

    # # Dispatch based on selected command
    if args.command == "fetch-commits":
        df = fetch_commits(args.repo, args.max_commits)
        if df.empty:
           sys.exit(-1)
        df.to_csv(args.out, index=False)
        print(f"Saved {len(df)} commits to {args.out}")

    elif args.command == "fetch-issues":
        df = fetch_issues(args.repo, args.state, args.max_issues)
        if df.empty:
           print("No issues found.")
           sys.exit(-1)
        df.to_csv(args.out, index=False)
        print(f"Saved {len(df)} issues to {args.out}")

if __name__ == "__main__":
    main()
