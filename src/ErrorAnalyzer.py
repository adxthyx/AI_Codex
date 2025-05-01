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



class ErrorAnalyzer:
    def __init__(self, groq_assistant: GroqAssistant):
        """Initialize error analyzer with Groq assistant."""
        self.groq_assistant = groq_assistant
    
    def analyze_traceback(self, traceback_text: str) -> str:
        """Analyze a Python traceback."""
        messages = [
            {"role": "system", "content": """You are TraceFix, a Python error analysis expert. Interpret tracebacks, explain root causes clearly, and suggest accurate fixes. Focus on clarity, correctness, and actionable solutions."""},
            {"role": "user", "content": f"Please analyze this Python traceback and explain what's wrong and how to fix it:\n\n```\n{traceback_text}\n```"}
        ]
        return self.groq_assistant._call_groq_api(messages)
    
    def analyze_runtime_error(self, code: str, error_output: str) -> str:
        """Analyze a runtime error with the code that caused it."""
        return self.groq_assistant.debug_error(code, error_output)
    
    def check_common_errors(self, code: str) -> List[Dict[str, Any]]:
        """Check for common errors in code."""
        errors = []
        
        # Simple pattern matching for common Python issues
        if re.search(r'except:', code) and not re.search(r'except\s+\w+:', code):
            errors.append({
                "type": "Bare except",
                "description": "Using bare 'except:' catches all exceptions including KeyboardInterrupt, which is not recommended.",
                "suggestion": "Specify the exception types to catch, e.g., 'except Exception:'."
            })
        
        if re.search(r'import \*', code):
            errors.append({
                "type": "Wildcard import",
                "description": "Using wildcard imports (import *) can lead to namespace pollution.",
                "suggestion": "Import only what you need explicitly."
            })
        
        if re.search(r'\.readlines\(\)', code) and re.search(r'for.*in', code):
            errors.append({
                "type": "Inefficient file reading",
                "description": "Using .readlines() loads the entire file into memory.",
                "suggestion": "Iterate over the file object directly: 'for line in file:'."
            })
        
        # More sophisticated checks with LLM
        if self.groq_assistant:
            linting_result = self.groq_assistant.detect_errors(code)
            errors.append({
                "type": "LLM Analysis",
                "description": linting_result
            })
        
        return errors
