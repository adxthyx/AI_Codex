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


class DocumentationGenerator:
    def __init__(self, groq_assistant: GroqAssistant):
        """Initialize documentation generator with Groq assistant."""
        self.groq_assistant = groq_assistant
    
    def generate_function_docs(self, function_code: str) -> str:
        """Generate documentation for a function."""
        return self.groq_assistant.generate_documentation(function_code, doc_type="function")
    
    def generate_class_docs(self, class_code: str) -> str:
        """Generate documentation for a class."""
        return self.groq_assistant.generate_documentation(class_code, doc_type="class")
    
    def generate_module_docs(self, module_code: str) -> str:
        """Generate documentation for a module."""
        return self.groq_assistant.generate_documentation(module_code, doc_type="module")
    
    def generate_project_readme(self, project_description: str, key_features: List[str]) -> str:
        """Generate a README for a project."""
        content = f"Project Description: {project_description}\n\nKey Features:\n"
        for i, feature in enumerate(key_features, 1):
            content += f"{i}. {feature}\n"
        
        messages = [
            {"role": "system", "content": """You are DocuForge, a markdown documentation assistant. Generate complete, well-structured README.md files. Include sections like Title, Description, Features, Installation, Usage, Tech Stack, Contributing, License, and Contact (if available). Use proper markdown syntax and keep the tone clear, concise, and developer-friendly."""},
            {"role": "user", "content": f"Please generate a complete README.md file for my project with the following information:\n\n{content}"}
        ]
        return self.groq_assistant._call_groq_api(messages)
    
    def generate_code_comments(self, code: str) -> str:
        """Generate comments for code."""
        messages = [
            {"role": "system", "content": """You are CommentMate, an expert in adding clear, concise comments to code. Improve readability without modifying functionality. Support idiomatic commenting for various languages."""},
            {"role": "user", "content": f"Please add appropriate comments to this code without changing the code itself:\n\n```\n{code}\n```"}
        ]
        return self.groq_assistant._call_groq_api(messages)


