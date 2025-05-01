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


class CodebaseAnalyzer:
    def __init__(self, base_path: str = "."):
        """Initialize codebase analyzer with base directory path."""
        self.base_path = os.path.abspath(base_path)
        self.groq_assistant = None
    
    def set_groq_assistant(self, assistant: GroqAssistant):
        """Set the Groq assistant for code analysis."""
        self.groq_assistant = assistant

    def find_files(self, extension: str = ".py", exclude_dirs: List[str] = None) -> List[str]:
        """Find files with specified extension in the codebase."""
        if exclude_dirs is None:
            exclude_dirs = ["venv", "env", "__pycache__", ".git", "node_modules"]
        
        files = []
        for root, dirs, filenames in os.walk(self.base_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for filename in filenames:
                if filename.endswith(extension):
                    files.append(os.path.join(root, filename))
        
        return files

    def analyze_python_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a Python file for structure and potential issues."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        result = {
            "file_path": file_path,
            "size_bytes": os.path.getsize(file_path),
            "line_count": content.count('\n') + 1,
            "classes": [],
            "functions": [],
            "imports": [],
            "issues": []
        }
        
        try:
            tree = ast.parse(content)
            
            # Find classes and functions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    result["classes"].append({
                        "name": node.name,
                        "line": node.lineno,
                    })
                elif isinstance(node, ast.FunctionDef):
                    result["functions"].append({
                        "name": node.name,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args]
                    })
                elif isinstance(node, ast.Import):
                    for name in node.names:
                        result["imports"].append(name.name)
                elif isinstance(node, ast.ImportFrom):
                    for name in node.names:
                        result["imports"].append(f"{node.module}.{name.name}" if node.module else name.name)
            
            # Run static analysis with the LLM if available
            if self.groq_assistant:
                issues = self.groq_assistant.detect_errors(content)
                result["issues"] = issues
            
        except SyntaxError as e:
            result["issues"] = [f"SyntaxError: {str(e)}"]
        except Exception as e:
            result["issues"] = [f"Error analyzing file: {str(e)}"]
        
        return result

    def generate_file_documentation(self, file_path: str) -> str:
        """Generate documentation for a file."""
        if not self.groq_assistant:
            return "Groq assistant not configured. Please set it first."
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.groq_assistant.generate_documentation(content, doc_type="file")
    
    def analyze_codebase_structure(self) -> Dict[str, Any]:
        """Analyze the structure of the codebase."""
        python_files = self.find_files(extension=".py")
        js_files = self.find_files(extension=".js")
        html_files = self.find_files(extension=".html")
        css_files = self.find_files(extension=".css")
        
        return {
            "python_files": len(python_files),
            "js_files": len(js_files),
            "html_files": len(html_files),
            "css_files": len(css_files),
            "total_files": len(python_files) + len(js_files) + len(html_files) + len(css_files)
        }


