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


class GroqAssistant:
    def __init__(self, api_key: str = None):
        """Initialize the code assistant with Groq API key."""
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key not found. Please provide it or set GROQ_API_KEY environment variable.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama3-70b-8192"  # Default model

    def _call_groq_api(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """Make a call to the Groq API."""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4096
        }
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            print(f"Error calling Groq API: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            return f"Error: {str(e)}"

    def detect_errors(self, code: str) -> str:
        """Detect potential errors in the code."""
        messages = [
            {"role": "system", "content": """"You are CodexRev, an expert code review assistant. Analyze code for bugs, logic flaws, bad practices, and security risks. Suggest concise, actionable improvements with optional corrected snippets. Prioritize clarity, performance, and maintainability. Support multiple languages. Assume user has intermediate-to-advanced knowledge."""},
            {"role": "user", "content": f"Please analyze this code for errors and suggest improvements:\n\n```\n{code}\n```"}
        ]
        return self._call_groq_api(messages)

    def debug_error(self, code: str, error_message: str) -> str:
        """Debug an error given code and error message."""
        messages = [
            {"role": "system", "content": """You are DebugMate, an expert debugging assistant. Analyze code and error messages to identify root causes and suggest precise fixes. Explain issues clearly and offer corrected code or workarounds where needed. Prioritize accuracy and clarity."""},
            {"role": "user", "content": f"I have the following code:\n\n```\n{code}\n```\n\nAnd I'm getting this error:\n\n{error_message}\n\nPlease help me understand and fix this issue."}
        ]
        return self._call_groq_api(messages)

    def generate_documentation(self, code: str, doc_type: str = "function") -> str:
        """Generate documentation for code."""
        messages = [
            {"role": "system", "content": """You are DocuForge, an expert in generating clear, structured, and accurate code documentation. Support various doc types (e.g., function-level, module-level, API). Use appropriate formatting and terminology for the language."""},
            {"role": "user", "content": f"Please generate {doc_type} documentation for this code:\n\n```\n{code}\n```"}
        ]
        return self._call_groq_api(messages)

    def explain_code(self, code: str) -> str:
        """Explain what the code does."""
        messages = [
            {"role": "system", "content": """You are ExplainAI, a code explanation expert. Break down code step by step, clarify logic, and describe functionality in clear, technical terms. Support multiple languages and highlight important behaviors or edge cases."""},
            {"role": "user", "content": f"Please explain what this code does in detail:\n\n```\n{code}\n```"}
        ]
        return self._call_groq_api(messages)

    def suggest_improvements(self, code: str) -> str:
        """Suggest code improvements."""
        messages = [
            {"role": "system", "content": """You are OptiCode, an expert in code optimization and best practices. Suggest improvements for clarity, efficiency, readability, and maintainability. Support multiple languages and modern conventions."""},
            {"role": "user", "content": f"Please suggest improvements for this code:\n\n```\n{code}\n```"}
        ]
        return self._call_groq_api(messages)