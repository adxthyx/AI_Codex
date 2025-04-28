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
            {"role": "system", "content": "You are a code review assistant. Analyze the code for potential errors, bugs, and issues."},
            {"role": "user", "content": f"Please analyze this code for errors and suggest improvements:\n\n```\n{code}\n```"}
        ]
        return self._call_groq_api(messages)

    def debug_error(self, code: str, error_message: str) -> str:
        """Debug an error given code and error message."""
        messages = [
            {"role": "system", "content": "You are a debugging assistant. Help fix errors in code."},
            {"role": "user", "content": f"I have the following code:\n\n```\n{code}\n```\n\nAnd I'm getting this error:\n\n{error_message}\n\nPlease help me understand and fix this issue."}
        ]
        return self._call_groq_api(messages)

    def generate_documentation(self, code: str, doc_type: str = "function") -> str:
        """Generate documentation for code."""
        messages = [
            {"role": "system", "content": "You are a documentation assistant. Generate comprehensive documentation for code."},
            {"role": "user", "content": f"Please generate {doc_type} documentation for this code:\n\n```\n{code}\n```"}
        ]
        return self._call_groq_api(messages)

    def explain_code(self, code: str) -> str:
        """Explain what the code does."""
        messages = [
            {"role": "system", "content": "You are a code explanation assistant. Provide clear explanations of code."},
            {"role": "user", "content": f"Please explain what this code does in detail:\n\n```\n{code}\n```"}
        ]
        return self._call_groq_api(messages)

    def suggest_improvements(self, code: str) -> str:
        """Suggest code improvements."""
        messages = [
            {"role": "system", "content": "You are a code improvement assistant. Suggest ways to make code better, more efficient, and follow best practices."},
            {"role": "user", "content": f"Please suggest improvements for this code:\n\n```\n{code}\n```"}
        ]
        return self._call_groq_api(messages)


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


class ErrorAnalyzer:
    def __init__(self, groq_assistant: GroqAssistant):
        """Initialize error analyzer with Groq assistant."""
        self.groq_assistant = groq_assistant
    
    def analyze_traceback(self, traceback_text: str) -> str:
        """Analyze a Python traceback."""
        messages = [
            {"role": "system", "content": "You are an error analysis assistant. Help understand and fix Python tracebacks."},
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
            {"role": "system", "content": "You are a documentation assistant. Generate comprehensive project README files in markdown format."},
            {"role": "user", "content": f"Please generate a complete README.md file for my project with the following information:\n\n{content}"}
        ]
        return self.groq_assistant._call_groq_api(messages)
    
    def generate_code_comments(self, code: str) -> str:
        """Generate comments for code."""
        messages = [
            {"role": "system", "content": "You are a code documentation assistant. Add helpful comments to code."},
            {"role": "user", "content": f"Please add appropriate comments to this code without changing the code itself:\n\n```\n{code}\n```"}
        ]
        return self.groq_assistant._call_groq_api(messages)


class CodeAssistantCLI:
    def __init__(self):
        """Initialize the command-line interface for the code assistant."""
        self.parser = argparse.ArgumentParser(description="Code Assistant using Groq API")
        self.setup_arguments()
        
        # Components will be initialized based on arguments
        self.groq_assistant = None
        self.github_assistant = None
        self.codebase_analyzer = None
        self.error_analyzer = None
        self.doc_generator = None
    
    def setup_arguments(self):
        """Set up command-line arguments."""
        self.parser.add_argument("--api-key", type=str, help="Groq API key (or set GROQ_API_KEY environment variable)")
        self.parser.add_argument("--repo-path", type=str, default=".", help="Path to repository")
        
        subparsers = self.parser.add_subparsers(dest="command", help="Command to execute")
        
        # Error detection command
        error_parser = subparsers.add_parser("detect-errors", help="Detect errors in code")
        error_parser.add_argument("--file", type=str, required=True, help="File to analyze")
        
        # Debug command
        debug_parser = subparsers.add_parser("debug", help="Debug error in code")
        debug_parser.add_argument("--file", type=str, required=True, help="File with error")
        debug_parser.add_argument("--error", type=str, help="Error message")
        
        # Documentation command
        doc_parser = subparsers.add_parser("document", help="Generate documentation")
        doc_parser.add_argument("--file", type=str, required=True, help="File to document")
        doc_parser.add_argument("--type", type=str, choices=["function", "class", "module", "file"], 
                                default="file", help="Type of documentation to generate")
        
        # Codebase analysis command
        analyze_parser = subparsers.add_parser("analyze", help="Analyze codebase")
        analyze_parser.add_argument("--path", type=str, default=".", help="Path to analyze")
        
        # GitHub info command
        github_parser = subparsers.add_parser("github", help="Get GitHub repository information")
        
        # File history command
        history_parser = subparsers.add_parser("history", help="Get file history")
        history_parser.add_argument("--file", type=str, required=True, help="File to get history for")
        
        # Explain code command
        explain_parser = subparsers.add_parser("explain", help="Explain what code does")
        explain_parser.add_argument("--file", type=str, required=True, help="File to explain")
        
        # Readme generation command
        readme_parser = subparsers.add_parser("readme", help="Generate README")
        readme_parser.add_argument("--description", type=str, required=True, help="Project description")
        readme_parser.add_argument("--features", type=str, nargs="+", required=True, help="Key features")
        
        # Comment code command
        comment_parser = subparsers.add_parser("comment", help="Add comments to code")
        comment_parser.add_argument("--file", type=str, required=True, help="File to comment")
    
    def initialize_components(self, args):
        """Initialize components based on arguments."""
        # Initialize Groq Assistant
        api_key = args.api_key or os.environ.get("GROQ_API_KEY")
        self.groq_assistant = GroqAssistant(api_key=api_key)
        
        # Initialize GitHub Assistant
        self.github_assistant = GitHubAssistant(repo_path=args.repo_path)
        
        # Initialize Codebase Analyzer
        self.codebase_analyzer = CodebaseAnalyzer(base_path=args.repo_path)
        self.codebase_analyzer.set_groq_assistant(self.groq_assistant)
        
        # Initialize Error Analyzer
        self.error_analyzer = ErrorAnalyzer(groq_assistant=self.groq_assistant)
        
        # Initialize Documentation Generator
        self.doc_generator = DocumentationGenerator(groq_assistant=self.groq_assistant)
    
    def run(self):
        """Run the command-line interface."""
        args = self.parser.parse_args()
        
        if not args.command:
            self.parser.print_help()
            return
        
        try:
            self.initialize_components(args)
            
            if args.command == "detect-errors":
                self._handle_detect_errors(args)
            elif args.command == "debug":
                self._handle_debug(args)
            elif args.command == "document":
                self._handle_document(args)
            elif args.command == "analyze":
                self._handle_analyze(args)
            elif args.command == "github":
                self._handle_github(args)
            elif args.command == "history":
                self._handle_history(args)
            elif args.command == "explain":
                self._handle_explain(args)
            elif args.command == "readme":
                self._handle_readme(args)
            elif args.command == "comment":
                self._handle_comment(args)
        except Exception as e:
            print(f"Error: {str(e)}")
            traceback.print_exc()
    
    def _handle_detect_errors(self, args):
        """Handle the detect-errors command."""
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                code = f.read()
            
            result = self.groq_assistant.detect_errors(code)
            print("\n=== Error Detection Results ===")
            print(result)
        except Exception as e:
            print(f"Error analyzing file: {str(e)}")
    
    def _handle_debug(self, args):
        """Handle the debug command."""
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                code = f.read()
            
            error_message = args.error
            if not error_message:
                print("Running the file to capture errors...")
                try:
                    result = subprocess.run([sys.executable, args.file], 
                                         capture_output=True, text=True)
                    if result.returncode != 0:
                        error_message = result.stderr
                    else:
                        print("No errors found when running the file.")
                        return
                except Exception as run_err:
                    error_message = str(run_err)
            
            result = self.groq_assistant.debug_error(code, error_message)
            print("\n=== Debugging Results ===")
            print(result)
        except Exception as e:
            print(f"Error debugging file: {str(e)}")
    
    def _handle_document(self, args):
        """Handle the document command."""
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                code = f.read()
            
            result = self.groq_assistant.generate_documentation(code, doc_type=args.type)
            print(f"\n=== {args.type.capitalize()} Documentation ===")
            print(result)
        except Exception as e:
            print(f"Error generating documentation: {str(e)}")
    
    def _handle_analyze(self, args):
        """Handle the analyze command."""
        try:
            self.codebase_analyzer = CodebaseAnalyzer(base_path=args.path)
            self.codebase_analyzer.set_groq_assistant(self.groq_assistant)
            
            structure = self.codebase_analyzer.analyze_codebase_structure()
            print("\n=== Codebase Structure ===")
            print(json.dumps(structure, indent=2))
            
            # Analyze Python files
            python_files = self.codebase_analyzer.find_files(extension=".py")
            if python_files:
                print(f"\nFound {len(python_files)} Python files. Analyzing first 5...")
                for file_path in python_files[:5]:
                    print(f"\n--- Analyzing {file_path} ---")
                    analysis = self.codebase_analyzer.analyze_python_file(file_path)
                    print(f"Classes: {len(analysis['classes'])}")
                    print(f"Functions: {len(analysis['functions'])}")
                    print(f"Imports: {len(analysis['imports'])}")
                    if analysis['issues']:
                        print("Potential issues found:")
                        print(analysis['issues'])
        except Exception as e:
            print(f"Error analyzing codebase: {str(e)}")
    
    def _handle_github(self, args):
        """Handle the github command."""
        try:
            info = self.github_assistant.get_repo_info()
            print("\n=== GitHub Repository Information ===")
            print(json.dumps(info, indent=2))
        except Exception as e:
            print(f"Error getting GitHub information: {str(e)}")
    
    def _handle_history(self, args):
        """Handle the history command."""
        try:
            history = self.github_assistant.get_file_history(args.file)
            print(f"\n=== File History for {args.file} ===")
            print(json.dumps(history, indent=2))
        except Exception as e:
            print(f"Error getting file history: {str(e)}")
    
    def _handle_explain(self, args):
        """Handle the explain command."""
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                code = f.read()
            
            result = self.groq_assistant.explain_code(code)
            print("\n=== Code Explanation ===")
            print(result)
        except Exception as e:
            print(f"Error explaining code: {str(e)}")
    
    def _handle_readme(self, args):
        """Handle the readme command."""
        try:
            result = self.doc_generator.generate_project_readme(args.description, args.features)
            print("\n=== Generated README.md ===")
            print(result)
        except Exception as e:
            print(f"Error generating README: {str(e)}")
    
    def _handle_comment(self, args):
        """Handle the comment command."""
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                code = f.read()
            
            result = self.doc_generator.generate_code_comments(code)
            print("\n=== Code with Comments ===")
            print(result)
        except Exception as e:
            print(f"Error commenting code: {str(e)}")


if __name__ == "__main__":
    cli = CodeAssistantCLI()
    cli.run()