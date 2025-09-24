import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime
import os
import tempfile
from src.repo_miner import fetch_commits, main

class TestFetchCommits:
    @patch('src.repo_miner.Github')
    @patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'})
    def test_fetch_commits_success(self, mock_github):
        # Setup mock objects
        mock_commit = Mock()
        mock_commit.sha = "abc123"
        mock_commit.author.name = "Test User"
        mock_commit.author.email = "test@example.com"
        mock_commit.commit.author.date = datetime(2023, 1, 1)
        mock_commit.commit.message = "Test commit"
        
        mock_repo = Mock()
        mock_repo.get_commits.return_value = [mock_commit]
        
        mock_github_instance = Mock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_instance
        
        # Test
        result = fetch_commits("owner/repo", max_commits=1)
        
        # Assertions
        assert len(result) == 1
        assert result.iloc[0]['sha'] == "abc123"
        assert result.iloc[0]['author'] == "Test User"
        assert result.iloc[0]['email'] == "test@example.com"
        assert result.iloc[0]['message'] == "Test commit"

    def test_fetch_commits_no_token(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EnvironmentError, match="GITHUB_TOKEN environment variable not set"):
                fetch_commits("owner/repo")

    @patch('src.repo_miner.Github')
    @patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'})
    def test_fetch_commits_repo_error(self, mock_github):
        mock_github_instance = Mock()
        mock_github_instance.get_repo.side_effect = Exception("Repository not found")
        mock_github.return_value = mock_github_instance
        
        with pytest.raises(ValueError, match="Error accessing repository 'owner/repo'"):
            fetch_commits("owner/repo")

    @patch('src.repo_miner.Github')
    @patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'})
    def test_fetch_commits_max_limit(self, mock_github):
        # Create 5 mock commits
        mock_commits = []
        for i in range(5):
            mock_commit = Mock()
            mock_commit.sha = f"sha{i}"
            mock_commit.author.name = f"User{i}"
            mock_commit.author.email = f"user{i}@example.com"
            mock_commit.commit.author.date = datetime(2023, 1, i+1)
            mock_commit.commit.message = f"Commit {i}"
            mock_commits.append(mock_commit)
        
        mock_repo = Mock()
        mock_repo.get_commits.return_value = mock_commits
        
        mock_github_instance = Mock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_instance
        
        # Test with max_commits=3
        result = fetch_commits("owner/repo", max_commits=3)
        
        assert len(result) == 3

    @patch('src.repo_miner.Github')
    @patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'})
    def test_fetch_commits_missing_author(self, mock_github):
        mock_commit = Mock()
        mock_commit.sha = "abc123"
        mock_commit.author = None
        mock_commit.commit.author.date = datetime(2023, 1, 1)
        mock_commit.commit.message = "Test commit"
        
        mock_repo = Mock()
        mock_repo.get_commits.return_value = [mock_commit]
        
        mock_github_instance = Mock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_instance
        
        result = fetch_commits("owner/repo")
        
        assert len(result) == 1
        assert result.iloc[0]['author'] is None
        assert result.iloc[0]['email'] is None


class TestMain:
    @patch('src.repo_miner.fetch_commits')
    @patch('builtins.print')
    def test_main_fetch_commits_command(self, mock_print, mock_fetch_commits):
        # Setup
        mock_df = pd.DataFrame({
            'sha': ['abc123'],
            'author': ['Test User'],
            'email': ['test@example.com'],
            'date': [datetime(2023, 1, 1)],
            'message': ['Test commit']
        })
        mock_fetch_commits.return_value = mock_df
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as temp_file:
            temp_path = temp_file.name
        
        try:
            # Mock sys.argv
            test_args = ['repo_miner', 'fetch-commits', '--repo', 'owner/repo', '--max', '10', '--out', temp_path]
            with patch('sys.argv', test_args):
                main()
            
            # Verify fetch_commits was called with correct arguments
            mock_fetch_commits.assert_called_once_with('owner/repo', 10)
            
            # Verify CSV was created and contains expected data
            result_df = pd.read_csv(temp_path)
            assert len(result_df) == 1
            assert result_df.iloc[0]['sha'] == 'abc123'
            
            # Verify print was called
            mock_print.assert_called_with(f"Saved 1 commits to {temp_path}")
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @patch('src.repo_miner.fetch_commits')
    @patch('builtins.print')
    def test_main_fetch_commits_no_max(self, mock_print, mock_fetch_commits):
        mock_df = pd.DataFrame({'sha': ['abc123'], 'author': ['Test'], 'email': ['test@example.com'], 'date': [datetime.now()], 'message': ['Test']})
        mock_fetch_commits.return_value = mock_df
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as temp_file:
            temp_path = temp_file.name
        
        try:
            test_args = ['repo_miner', 'fetch-commits', '--repo', 'owner/repo', '--out', temp_path]
            with patch('sys.argv', test_args):
                main()
            
            # Verify fetch_commits was called with None for max_commits
            mock_fetch_commits.assert_called_once_with('owner/repo', None)
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_main_missing_required_args(self):
        test_args = ['repo_miner', 'fetch-commits', '--repo', 'owner/repo']  # Missing --out
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit):
                main()

    def test_main_no_command(self):
        test_args = ['repo_miner']
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit):
                main()