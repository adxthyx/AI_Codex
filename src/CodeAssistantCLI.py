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