import os
import argparse
import json
import re
import subprocess
import glob
from pathlib import Path
import ast
import sys
import traceback
from typing import List, Dict, Any, Optional, Tuple
import requests
from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError
from dotenv import load_dotenv

from dotenv import load_dotenv
load_dotenv()



class GitHubAssistant:
    def __init__(self, repo_path: str = "."):
        """Initialize GitHub assistant with repository path."""
        try:
            self.repo = Repo(repo_path)
            self.repo_path = repo_path
        except InvalidGitRepositoryError:
            print(f"Warning: {repo_path} is not a valid Git repository.")
            self.repo = None
            self.repo_path = repo_path

    def is_git_repo(self) -> bool:
        """Check if the path is a Git repository."""
        return self.repo is not None

    def get_repo_info(self) -> Dict[str, Any]:
        """Get information about the repository."""
        if not self.is_git_repo():
            return {"error": "Not a Git repository"}
        
        try:
            remotes = list(self.repo.remotes)
            remote_urls = {remote.name: [url for url in remote.urls] for remote in remotes}
            
            return {
                "active_branch": self.repo.active_branch.name,
                "remotes": remote_urls,
                "is_dirty": self.repo.is_dirty(),
                "untracked_files": self.repo.untracked_files,
                "last_commit": {
                    "hexsha": self.repo.head.commit.hexsha,
                    "message": self.repo.head.commit.message,
                    "author": str(self.repo.head.commit.author),
                    "committed_date": self.repo.head.commit.committed_datetime.isoformat(),
                }
            }
        except Exception as e:
            return {"error": str(e)}

    def get_file_history(self, file_path: str, max_commits: int = 5) -> List[Dict[str, Any]]:
        """Get commit history for a specific file."""
        if not self.is_git_repo():
            return [{"error": "Not a Git repository"}]
        
        try:
            commits = []
            for commit in self.repo.iter_commits(paths=file_path, max_count=max_commits):
                commits.append({
                    "hexsha": commit.hexsha,
                    "message": commit.message,
                    "author": str(commit.author),
                    "committed_date": commit.committed_datetime.isoformat(),
                })
            return commits
        except Exception as e:
            return [{"error": str(e)}]
