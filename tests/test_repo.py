# tests/test_repo_miner.py

import os
import pandas as pd
import pytest
from datetime import datetime, timedelta
from src.repo_miner import fetch_commits, fetch_issues

# --- Helpers for dummy GitHub API objects ---

class DummyAuthor:
    def __init__(self, name, email, date):
        self.name = name
        self.email = email
        self.date = date

class DummyCommitCommit:
    def __init__(self, author, message):
        self.author = author
        self.message = message

class DummyCommit:
    def __init__(self, sha, author, email, date, message):
        self.sha = sha
        self.author = DummyAuthor(author, email, date)
        self.commit = DummyCommitCommit(DummyAuthor(author, email, date), message)

class DummyUser:
    def __init__(self, login):
        self.login = login

class DummyIssue:
    def __init__(self, id_, number, title, user, state, created_at, closed_at, comments, is_pr=False):
        self.id = id_
        self.number = number
        self.title = title
        self.user = DummyUser(user)
        self.state = state
        self.created_at = created_at
        self.closed_at = closed_at
        self.comments = comments
        # attribute only on pull requests
        self.pull_request = DummyUser("pr") if is_pr else None

class DummyRepo:
    def __init__(self, commits, issues):
        self._commits = commits
        self._issues = issues

    def get_commits(self):
        return self._commits

    def get_issues(self, state="all"):
        # filter by state
        if state == "all":
            return self._issues
        return [i for i in self._issues if i.state == state]

class DummyGithub:
    def __init__(self, token):
        assert token == "fake-token"
    def get_repo(self, repo_name):
        # ignore repo_name; return repo set in test fixture
        return self._repo

@pytest.fixture(autouse=True)
def patch_env_and_github(monkeypatch):
    # Set fake token
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    # Create instance first
    gh_instance = DummyGithub("fake-token")
    # Patch Github class - note: it's imported as 'from github import Github'
    monkeypatch.setattr("src.repo_miner.Github", lambda auth: gh_instance)
    return gh_instance

# --- Tests for fetch_commits ---
# An example test case
def test_fetch_commits_basic(patch_env_and_github):
    # Setup dummy commits
    now = datetime.now()
    commits = [
        DummyCommit("sha1", "Alice", "a@example.com", now, "Initial commit\nDetails"),
        DummyCommit("sha2", "Bob", "b@example.com", now - timedelta(days=1), "Bug fix")
    ]
    patch_env_and_github._repo = DummyRepo(commits, [])
    df = fetch_commits("any/repo")
    assert list(df.columns) == ["sha", "author", "email", "date", "message"]
    assert len(df) == 2
    assert df.iloc[0]["message"] == "Initial commit\nDetails"

def test_fetch_commits_limit(patch_env_and_github):
    # More commits than max_commits
    # Setup dummy commits
    now = datetime.now()
    commits = [
        DummyCommit("sha1", "Alice", "a@example.com", now, "Initial commit\nDetails"),
        DummyCommit("sha2", "Bob", "b@example.com", now - timedelta(days=1), "Bug fix"),
        DummyCommit("sha3", "John", "j@example.com", now - timedelta(days=1), "Bug fix")
    ]
    patch_env_and_github._repo = DummyRepo(commits, [])
    df = fetch_commits("any/repo", 2)
    assert list(df.columns) == ["sha", "author", "email", "date", "message"]
    assert len(df) == 2
    assert df.iloc[0]["message"] == "Initial commit\nDetails"
    assert True

def test_fetch_commits_empty(patch_env_and_github):
# Setup dummy commits
    now = datetime.now()
    commits = []
    patch_env_and_github._repo = DummyRepo(commits, [])
    df = fetch_commits("any/repo")
    assert df.empty

        # self.id = id_
        # self.number = number
        # self.title = title
        # self.user = DummyUser(user)
        # self.state = state
        # self.created_at = created_at
        # self.closed_at = closed_at
        # self.comments = comments
        # # attribute only on pull requests
        # self.pull_request = DummyUser("pr") if is_pr else None

def test_fetch_issues_basic(patch_env_and_github):
    # Setup dummy issues
    now = datetime.now()
    issues = [
        DummyIssue("id_1", "1", "Issue 1", "Alice", "closed", datetime(2025, 10, 1), datetime(2025, 10, 1), "CI Broke", False),
        DummyIssue(id_="id_1", number="2", title="Issue 2", user="Bob", state="open", created_at="2025-10-1", closed_at=None, comments="CI still broke", is_pr=False),
    ]
    patch_env_and_github._repo = DummyRepo([], issues=issues)
    df = fetch_issues("any/repo")
    assert list(df.columns) == ["id","number","title","user","state","created_at","closed_at","open_duration_days","comments"]
    assert len(df) == 2
    assert df.iloc[0]["comments"] == "CI Broke"

def test_fetch_issues_limit(patch_env_and_github):
    # More commits than max_commits
    # Setup dummy commits
    now = datetime.now()
    issues = [
        DummyIssue("id_1", "1", "Issue 1", "Alice", "closed", datetime(2025, 10, 1), datetime(2025, 10, 1), "CI Broke", False),
        DummyIssue(id_="id_1", number="2", title="Issue 2", user="Bob", state="open", created_at="2025-10-1", closed_at=None, comments="CI still broke", is_pr=False),
        DummyIssue(id_="id_2", number="3", title="Issue 3", user="Bo", state="open", created_at="2025-10-1", closed_at=None, comments="CI still  still broke", is_pr=False)
    ]
    patch_env_and_github._repo = DummyRepo([], issues)
    df = fetch_issues("any/repo", "all", 2)
    assert list(df.columns) == ["id","number","title","user","state","created_at","closed_at","open_duration_days","comments"]
    assert len(df) == 2
    assert df.iloc[0]["comments"] == "CI Broke"

def test_fetch_issues_empty(patch_env_and_github):
# Setup dummy commits
    now = datetime.now()
    issues = []
    patch_env_and_github._repo = DummyRepo([], issues)
    df = fetch_issues("any/repo")
    assert df.empty