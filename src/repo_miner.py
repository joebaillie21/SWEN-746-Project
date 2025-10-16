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

def merge_and_summarize(commits_df: pd.DataFrame, issues_df: pd.DataFrame) -> None:
    """
    Takes two DataFrames (commits and issues) and prints:
      - Top 5 committers by commit count
      - Issue close rate (closed/total)
      - Average open duration for closed issues (in days)
    """
    # Copy to avoid modifying original data
    commits = commits_df.copy()
    issues  = issues_df.copy()

    # 1) Normalize date/time columns to pandas datetime
    commits['date'] = pd.to_datetime(commits['date'], errors='coerce')
    issues['created_at'] = pd.to_datetime(issues['created_at'], errors='coerce')
    issues['closed_at']  = pd.to_datetime(issues['closed_at'], errors='coerce')

    # 2) Top 5 committers
    top_committers = commits['author'].value_counts().head(5)
    
    # 3) Calculate issue close rate
    total_issues = len(issues)
    closed_issues_df = issues[issues['state'] == 'closed']
    close_rate = (len(closed_issues_df) / total_issues) * 100 if total_issues > 0 else 0
    
    # 4) Compute average open duration (days) for closed issues
    avg_open_duration = closed_issues_df['open_duration_days'].mean()

    # 5) Print calculations
    print('Top 5 committers:', top_committers.to_string())
    print('Issue close rate:', close_rate)
    print('Average duration of open issues:', avg_open_duration)
   


def main():
    """
    Parse command-line arguments and dispatch to sub-commands.
    """
    parser = argparse.ArgumentParser(
        prog="repo_miner",
        description="Fetch GitHub commits/issues and summarize them"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sub-command: fetch-commits
    c1 = subparsers.add_parser("fetch-commits", help="Fetch commits and save to CSV")
    c1.add_argument("--repo", required=True, help="Repository in owner/repo format")
    c1.add_argument("--max",  type=int, dest="max_commits",
                    help="Max number of commits to fetch")
    c1.add_argument("--out",  required=True, help="Path to output commits CSV")

    # Sub-command: fetch-issues
    c2 = subparsers.add_parser("fetch-issues", help="Fetch issues and save to CSV")
    c2.add_argument("--repo",  required=True, help="Repository in owner/repo format")
    c2.add_argument("--state", choices=["all","open","closed"], default="all",
                    help="Filter issues by state")
    c2.add_argument("--max",   type=int, dest="max_issues",
                    help="Max number of issues to fetch")
    c2.add_argument("--out",   required=True, help="Path to output issues CSV")

    # Sub-command: summarize
    c3 = subparsers.add_parser("summarize", help="Summarize commits and issues")
    c3.add_argument("--commits", required=True, help="Path to commits CSV file")
    c3.add_argument("--issues",  required=True, help="Path to issues CSV file")

    args = parser.parse_args()

    # Dispatch based on selected command
    if args.command == "fetch-commits":
        df = fetch_commits(args.repo, args.max_commits)
        df.to_csv(args.out, index=False)
        print(f"Saved {len(df)} commits to {args.out}")

    elif args.command == "fetch-issues":
        df = fetch_issues(args.repo, args.state, args.max_issues)
        df.to_csv(args.out, index=False)
        print(f"Saved {len(df)} issues to {args.out}")

    if args.command == "summarize":
        # Read CSVs into DataFrames
        commits_df = pd.read_csv(args.commits)
        issues_df  = pd.read_csv(args.issues)
        # Generate and print the summary
        merge_and_summarize(commits_df, issues_df)

if __name__ == "__main__":
   main()