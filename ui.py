import sys
import os
import threading
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QFileDialog, QComboBox,
    QListWidget, QSplitter, QFrame, QGroupBox, QTreeWidget, QTreeWidgetItem,
    QDialog, QMessageBox, QProgressBar, QCheckBox, QGridLayout, QScrollArea
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QIcon, QFont, QPixmap, QPalette, QColor, QTextCursor

# Import your existing classes from app.py
from app import (
    GroqAssistant, GitHubAssistant, CodebaseAnalyzer, 
    ErrorAnalyzer, DocumentationGenerator
)

# Define colors and styles for UI
DARK_BG = "#1E1E1E"
LIGHTER_BG = "#252526"
ACCENT_COLOR = "#569CD6"
TEXT_COLOR = "#D4D4D4"
ERROR_COLOR = "#F44747"
SUCCESS_COLOR = "#6A9955"
BORDER_COLOR = "#3C3C3C"

STYLE_SHEET = f"""
QMainWindow, QDialog {{
    background-color: {DARK_BG};
    color: {TEXT_COLOR};
}}
QTabWidget::pane {{
    border: 1px solid {BORDER_COLOR};
    background-color: {LIGHTER_BG};
}}
QTabBar::tab {{
    background-color: {DARK_BG};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    padding: 8px 12px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {LIGHTER_BG};
    border-bottom-color: {ACCENT_COLOR};
}}
QTreeWidget, QListWidget, QTextEdit, QLineEdit, QComboBox {{
    background-color: {LIGHTER_BG};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    padding: 4px;
}}
QPushButton {{
    background-color: {ACCENT_COLOR};
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    min-width: 80px;
}}
QPushButton:hover {{
    background-color: #4A85C5;
}}
QPushButton:pressed {{
    background-color: #3D70A9;
}}
QPushButton:disabled {{
    background-color: #494949;
    color: #A0A0A0;
}}
QGroupBox {{
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 22px;
    color: {TEXT_COLOR};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 5px;
}}
QProgressBar {{
    background-color: {LIGHTER_BG};
    color: white;
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {ACCENT_COLOR};
    width: 10px;
}}
QSplitter::handle {{
    background-color: {BORDER_COLOR};
}}
QLabel {{
    color: {TEXT_COLOR};
}}
QScrollArea {{
    border: none;
}}
"""

# Task worker for running operations in background
class TaskWorker(QThread):
    task_completed = pyqtSignal(str, object)
    task_error = pyqtSignal(str, str)
    
    def __init__(self, task_name, task_func, *args, **kwargs):
        super().__init__()
        self.task_name = task_name
        self.task_func = task_func
        self.args = args
        self.kwargs = kwargs
        
    def run(self):
        try:
            result = self.task_func(*self.args, **self.kwargs)
            self.task_completed.emit(self.task_name, result)
        except Exception as e:
            self.task_error.emit(self.task_name, str(e))


class CodeAssistantUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Code Assistant")
        self.setMinimumSize(1000, 700)
        
        # Initialize components
        self.load_api_key()
        self.init_ui()
        self.init_components()
        
        # Apply style
        self.setStyleSheet(STYLE_SHEET)
        
    def load_api_key(self):
        """Load Groq API key from environment"""
        self.api_key = os.environ.get("GROQ_API_KEY", "")
        
    def init_components(self):
        """Initialize backend components"""
        if self.api_key:
            self.groq_assistant = GroqAssistant(api_key=self.api_key)
            self.github_assistant = GitHubAssistant()
            self.codebase_analyzer = CodebaseAnalyzer()
            self.codebase_analyzer.set_groq_assistant(self.groq_assistant)
            self.error_analyzer = ErrorAnalyzer(groq_assistant=self.groq_assistant)
            self.doc_generator = DocumentationGenerator(groq_assistant=self.groq_assistant)
            self.status_label.setText("Ready - API key loaded")
        else:
            self.status_label.setText("WARNING: No API key found. Set GROQ_API_KEY environment variable.")
            
    def init_ui(self):
        """Initialize the user interface"""
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget for different features
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.create_code_analysis_tab()
        self.create_error_detection_tab()
        self.create_documentation_tab()
        self.create_github_tab()
        self.create_settings_tab()
        
        # Add status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Initializing...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedWidth(150)
        self.progress_bar.hide()
        
        status_layout.addWidget(self.status_label, 1)
        status_layout.addWidget(self.progress_bar)
        
        # Add elements to main layout
        main_layout.addWidget(self.tab_widget, 1)
        main_layout.addLayout(status_layout)
        
    def create_code_analysis_tab(self):
        """Create the code analysis tab"""
        code_analysis_tab = QWidget()
        layout = QVBoxLayout(code_analysis_tab)
        
        # File selection area
        file_select_layout = QHBoxLayout()
        self.code_file_path = QLineEdit()
        self.code_file_path.setPlaceholderText("Select a file to analyze...")
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_for_code_file)
        
        file_select_layout.addWidget(QLabel("File:"))
        file_select_layout.addWidget(self.code_file_path, 1)
        file_select_layout.addWidget(browse_button)
        
        # Analysis options
        options_group = QGroupBox("Analysis Options")
        options_layout = QGridLayout(options_group)
        
        explain_button = QPushButton("Explain Code")
        explain_button.clicked.connect(self.explain_code)
        
        improve_button = QPushButton("Suggest Improvements")
        improve_button.clicked.connect(self.suggest_improvements)
        
        options_layout.addWidget(explain_button, 0, 0)
        options_layout.addWidget(improve_button, 0, 1)
        
        # Results area
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout(results_group)
        
        self.analysis_results = QTextEdit()
        self.analysis_results.setReadOnly(True)
        self.analysis_results.setMinimumHeight(300)
        
        results_layout.addWidget(self.analysis_results)
        
        # Add all components to main layout
        layout.addLayout(file_select_layout)
        layout.addWidget(options_group)
        layout.addWidget(results_group, 1)
        
        self.tab_widget.addTab(code_analysis_tab, "Code Analysis")
    
    def create_error_detection_tab(self):
        """Create the error detection tab"""
        error_tab = QWidget()
        layout = QVBoxLayout(error_tab)
        
        # File selection area
        file_select_layout = QHBoxLayout()
        self.error_file_path = QLineEdit()
        self.error_file_path.setPlaceholderText("Select a file to check for errors...")
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_for_error_file)
        
        file_select_layout.addWidget(QLabel("File:"))
        file_select_layout.addWidget(self.error_file_path, 1)
        file_select_layout.addWidget(browse_button)
        
        # Error message area (optional)
        error_msg_group = QGroupBox("Error Message (Optional)")
        error_msg_layout = QVBoxLayout(error_msg_group)
        
        self.error_message = QTextEdit()
        self.error_message.setPlaceholderText("Paste error message here if available...")
        self.error_message.setMaximumHeight(100)
        
        error_msg_layout.addWidget(self.error_message)
        
        # Actions
        actions_layout = QHBoxLayout()
        
        detect_button = QPushButton("Detect Errors")
        detect_button.clicked.connect(self.detect_errors)
        
        debug_button = QPushButton("Debug Errors")
        debug_button.clicked.connect(self.debug_errors)
        
        run_file_button = QPushButton("Run File")
        run_file_button.clicked.connect(self.run_file)
        
        actions_layout.addWidget(detect_button)
        actions_layout.addWidget(debug_button)
        actions_layout.addWidget(run_file_button)
        actions_layout.addStretch()
        
        # Results area
        results_group = QGroupBox("Error Analysis Results")
        results_layout = QVBoxLayout(results_group)
        
        self.error_results = QTextEdit()
        self.error_results.setReadOnly(True)
        
        results_layout.addWidget(self.error_results)
        
        # Add all components to main layout
        layout.addLayout(file_select_layout)
        layout.addWidget(error_msg_group)
        layout.addLayout(actions_layout)
        layout.addWidget(results_group, 1)
        
        self.tab_widget.addTab(error_tab, "Error Detection")
    
    def create_documentation_tab(self):
        """Create the documentation generation tab"""
        doc_tab = QWidget()
        layout = QVBoxLayout(doc_tab)
        
        # Left side - file selection and options
        top_layout = QHBoxLayout()
        file_select_layout = QVBoxLayout()
        
        file_path_layout = QHBoxLayout()
        self.doc_file_path = QLineEdit()
        self.doc_file_path.setPlaceholderText("Select file to document...")
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_for_doc_file)
        
        file_path_layout.addWidget(QLabel("File:"))
        file_path_layout.addWidget(self.doc_file_path, 1)
        file_path_layout.addWidget(browse_button)
        
        # Documentation type
        doc_type_layout = QHBoxLayout()
        doc_type_layout.addWidget(QLabel("Documentation Type:"))
        self.doc_type_combo = QComboBox()
        self.doc_type_combo.addItems(["Function", "Class", "Module", "File"])
        doc_type_layout.addWidget(self.doc_type_combo)
        doc_type_layout.addStretch()
        
        # Generate button
        generate_layout = QHBoxLayout()
        generate_button = QPushButton("Generate Documentation")
        generate_button.clicked.connect(self.generate_documentation)
        generate_layout.addWidget(generate_button)
        generate_layout.addStretch()
        
        # Add components to left side layout
        file_select_layout.addLayout(file_path_layout)
        file_select_layout.addLayout(doc_type_layout)
        file_select_layout.addLayout(generate_layout)
        file_select_layout.addStretch()
        
        # README Generator
        readme_group = QGroupBox("README Generator")
        readme_layout = QVBoxLayout(readme_group)
        
        desc_layout = QVBoxLayout()
        desc_layout.addWidget(QLabel("Project Description:"))
        self.project_description = QTextEdit()
        self.project_description.setMaximumHeight(80)
        desc_layout.addWidget(self.project_description)
        
        features_layout = QVBoxLayout()
        features_layout.addWidget(QLabel("Key Features (one per line):"))
        self.project_features = QTextEdit()
        self.project_features.setMaximumHeight(80)
        features_layout.addWidget(self.project_features)
        
        readme_button_layout = QHBoxLayout()
        generate_readme_button = QPushButton("Generate README")
        generate_readme_button.clicked.connect(self.generate_readme)
        readme_button_layout.addWidget(generate_readme_button)
        readme_button_layout.addStretch()
        
        readme_layout.addLayout(desc_layout)
        readme_layout.addLayout(features_layout)
        readme_layout.addLayout(readme_button_layout)
        
        # Results area
        results_group = QGroupBox("Generated Documentation")
        results_layout = QVBoxLayout(results_group)
        
        self.doc_results = QTextEdit()
        self.doc_results.setReadOnly(True)
        
        save_doc_button = QPushButton("Save Documentation")
        save_doc_button.clicked.connect(self.save_documentation)
        
        results_layout.addWidget(self.doc_results)
        results_layout.addWidget(save_doc_button)
        
        # Add components to main layout
        top_layout.addLayout(file_select_layout)
        top_layout.addWidget(readme_group)
        
        layout.addLayout(top_layout)
        layout.addWidget(results_group, 1)
        
        self.tab_widget.addTab(doc_tab, "Documentation")
    
    def create_github_tab(self):
        """Create the GitHub integration tab"""
        github_tab = QWidget()
        layout = QVBoxLayout(github_tab)
        
        # Repository path
        repo_layout = QHBoxLayout()
        self.repo_path = QLineEdit()
        self.repo_path.setPlaceholderText("Enter repository path...")
        self.repo_path.setText(os.getcwd())  # Default to current directory
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_for_repo)
        
        repo_layout.addWidget(QLabel("Repository:"))
        repo_layout.addWidget(self.repo_path, 1)
        repo_layout.addWidget(browse_button)
        
        # Actions
        actions_layout = QHBoxLayout()
        
        get_info_button = QPushButton("Get Repo Info")
        get_info_button.clicked.connect(self.get_repo_info)
        
        analyze_repo_button = QPushButton("Analyze Codebase")
        analyze_repo_button.clicked.connect(self.analyze_codebase)
        
        actions_layout.addWidget(get_info_button)
        actions_layout.addWidget(analyze_repo_button)
        actions_layout.addStretch()
        
        # Split view for results
        splitter = QSplitter(Qt.Horizontal)
        
        # File tree
        file_group = QGroupBox("Repository Files")
        file_layout = QVBoxLayout(file_group)
        
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["Files"])
        self.file_tree.itemDoubleClicked.connect(self.file_tree_item_clicked)
        
        refresh_button = QPushButton("Refresh Files")
        refresh_button.clicked.connect(self.load_repo_files)
        
        file_layout.addWidget(self.file_tree)
        file_layout.addWidget(refresh_button)
        
        # Results area
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout(results_group)
        
        self.github_results = QTextEdit()
        self.github_results.setReadOnly(True)
        
        results_layout.addWidget(self.github_results)
        
        # Add components to splitter
        splitter.addWidget(file_group)
        splitter.addWidget(results_group)
        splitter.setSizes([300, 700])
        
        # Add components to main layout
        layout.addLayout(repo_layout)
        layout.addLayout(actions_layout)
        layout.addWidget(splitter, 1)
        
        self.tab_widget.addTab(github_tab, "Repository Analysis")
    
    def create_settings_tab(self):
        """Create the settings tab"""
        settings_tab = QWidget()
        layout = QVBoxLayout(settings_tab)
        
        # API Key settings
        api_key_group = QGroupBox("API Settings")
        api_key_layout = QVBoxLayout(api_key_group)
        
        key_layout = QHBoxLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter Groq API Key...")
        self.api_key_input.setText(self.api_key)
        self.api_key_input.setEchoMode(QLineEdit.Password)
        
        show_key = QCheckBox("Show")
        show_key.stateChanged.connect(self.toggle_key_visibility)
        
        save_key_button = QPushButton("Save API Key")
        save_key_button.clicked.connect(self.save_api_key)
        
        key_layout.addWidget(QLabel("Groq API Key:"))
        key_layout.addWidget(self.api_key_input, 1)
        key_layout.addWidget(show_key)
        key_layout.addWidget(save_key_button)
        
        # Model settings
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"])
        self.model_combo.currentTextChanged.connect(self.change_model)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        
        api_key_layout.addLayout(key_layout)
        api_key_layout.addLayout(model_layout)
        
        # Theme settings
        theme_group = QGroupBox("Interface Settings")
        theme_layout = QVBoxLayout(theme_group)
        
        # About section
        about_group = QGroupBox("About")
        about_layout = QVBoxLayout(about_group)
        
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setHtml("""
        <h2>Code Assistant</h2>
        <p>A powerful AI-powered assistant for your coding needs.</p>
        <p>Features:</p>
        <ul>
            <li>Code analysis and explanation</li>
            <li>Error detection and debugging</li>
            <li>Documentation generation</li>
            <li>Repository analysis</li>
        </ul>
        <p>This application uses the Groq API to provide AI-powered code assistance.</p>
        """)
        
        about_layout.addWidget(about_text)
        
        # Add components to main layout
        layout.addWidget(api_key_group)
        layout.addWidget(theme_group)
        layout.addWidget(about_group)
        layout.addStretch()
        
        self.tab_widget.addTab(settings_tab, "Settings")
    
    # Event handlers
    def browse_for_code_file(self):
        """Open file dialog to select a code file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Code File", "", "Python Files (*.py);;All Files (*)")
        if file_path:
            self.code_file_path.setText(file_path)
    
    def browse_for_error_file(self):
        """Open file dialog to select a file for error detection"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "Python Files (*.py);;All Files (*)")
        if file_path:
            self.error_file_path.setText(file_path)
    
    def browse_for_doc_file(self):
        """Open file dialog to select a file for documentation"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "Python Files (*.py);;All Files (*)")
        if file_path:
            self.doc_file_path.setText(file_path)
    
    def browse_for_repo(self):
        """Open directory dialog to select a repository"""
        repo_path = QFileDialog.getExistingDirectory(self, "Select Repository Directory")
        if repo_path:
            self.repo_path.setText(repo_path)
            self.load_repo_files()
    
    def explain_code(self):
        """Explain the selected code file"""
        file_path = self.code_file_path.text()
        if not file_path or not os.path.isfile(file_path):
            self.show_error("Please select a valid file")
            return
            
        try:
            self.status_label.setText("Analyzing code...")
            self.progress_bar.show()
            self.progress_bar.setValue(20)
            
            def task_func():
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                return self.groq_assistant.explain_code(code)
            
            worker = TaskWorker("explain_code", task_func)
            worker.task_completed.connect(self.handle_task_completed)
            worker.task_error.connect(self.handle_task_error)
            worker.start()
            
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
    
    def suggest_improvements(self):
        """Suggest improvements for the selected code file"""
        file_path = self.code_file_path.text()
        if not file_path or not os.path.isfile(file_path):
            self.show_error("Please select a valid file")
            return
            
        try:
            self.status_label.setText("Analyzing for improvements...")
            self.progress_bar.show()
            self.progress_bar.setValue(20)
            
            def task_func():
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                return self.groq_assistant.suggest_improvements(code)
            
            worker = TaskWorker("suggest_improvements", task_func)
            worker.task_completed.connect(self.handle_task_completed)
            worker.task_error.connect(self.handle_task_error)
            worker.start()
            
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
    
    def detect_errors(self):
        """Detect errors in the selected file"""
        file_path = self.error_file_path.text()
        if not file_path or not os.path.isfile(file_path):
            self.show_error("Please select a valid file")
            return
            
        try:
            self.status_label.setText("Detecting errors...")
            self.progress_bar.show()
            self.progress_bar.setValue(20)
            
            def task_func():
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                return self.groq_assistant.detect_errors(code)
            
            worker = TaskWorker("detect_errors", task_func)
            worker.task_completed.connect(self.handle_task_completed)
            worker.task_error.connect(self.handle_task_error)
            worker.start()
            
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
    
    def debug_errors(self):
        """Debug errors in the selected file"""
        file_path = self.error_file_path.text()
        error_msg = self.error_message.toPlainText()
        
        if not file_path or not os.path.isfile(file_path):
            self.show_error("Please select a valid file")
            return
            
        try:
            self.status_label.setText("Debugging errors...")
            self.progress_bar.show()
            self.progress_bar.setValue(20)
            
            def task_func():
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                return self.groq_assistant.debug_error(code, error_msg)
            
            worker = TaskWorker("debug_errors", task_func)
            worker.task_completed.connect(self.handle_task_completed)
            worker.task_error.connect(self.handle_task_error)
            worker.start()
            
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
    
    def run_file(self):
        """Run the selected file to capture errors"""
        file_path = self.error_file_path.text()
        if not file_path or not os.path.isfile(file_path):
            self.show_error("Please select a valid file")
            return
            
        try:
            self.status_label.setText("Running file...")
            self.progress_bar.show()
            self.progress_bar.setValue(50)
            
            def task_func():
                try:
                    import sys
                    import subprocess
                    result = subprocess.run([sys.executable, file_path], 
                                         capture_output=True, text=True)
                    if result.returncode != 0:
                        self.error_message.setText(result.stderr)
                        return f"File execution failed with errors:\n\n{result.stderr}"
                    else:
                        return f"File executed successfully!\n\nOutput:\n{result.stdout}"
                except Exception as e:
                    return f"Error running file: {str(e)}"
            
            worker = TaskWorker("run_file", task_func)
            worker.task_completed.connect(self.handle_task_completed)
            worker.task_error.connect(self.handle_task_error)
            worker.start()
            
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
    
    def generate_documentation(self):
        """Generate documentation for the selected file"""
        file_path = self.doc_file_path.text()
        doc_type = self.doc_type_combo.currentText().lower()
        
        if not file_path or not os.path.isfile(file_path):
            self.show_error("Please select a valid file")
            return
            
        try:
            self.status_label.setText(f"Generating {doc_type} documentation...")
            self.progress_bar.show()
            self.progress_bar.setValue(20)
            
            def task_func():
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                return self.groq_assistant.generate_documentation(code, doc_type=doc_type)
            
            worker = TaskWorker("generate_documentation", task_func)
            worker.task_completed.connect(self.handle_task_completed)
            worker.task_error.connect(self.handle_task_error)
            worker.start()
            
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
    
    def generate_readme(self):
        """Generate README for the project"""
        description = self.project_description.toPlainText()
        features_text = self.project_features.toPlainText()
        features = [f.strip() for f in features_text.split('\n') if f.strip()]
        
        if not description:
            self.show_error("Please enter a project description")
            return
            
        if not features:
            self.show_error("Please enter at least one feature")
            return
            
        try:
            self.status_label.setText("Generating README...")
            self.progress_bar.show()
            self.progress_bar.setValue(20)
            
            def task_func():
                return self.doc_generator.generate_project_readme(description, features)
            
            worker = TaskWorker("generate_readme", task_func)
            worker.task_completed.connect(self.handle_task_completed)
            worker.task_error.connect(self.handle_task_error)
            worker.start()
            
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
    
    def save_documentation(self):
        """Save the generated documentation to a file"""
        doc_content = self.doc_results.toPlainText()
        if not doc_content:
            self.show_error("No documentation to save")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Documentation", "", 
                                                 "Markdown Files (*.md);;Text Files (*.txt);;All Files (*)")
        if not file_path:
            return
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            self.status_label.setText(f"Documentation saved to {file_path}")
        except Exception as e:
            self.show_error(f"Error saving file: {str(e)}")
    
    def get_repo_info(self):
        """Get information about the repository"""
        repo_path = self.repo_path.text()
        if not repo_path or not os.path.isdir(repo_path):
            self.show_error("Please select a valid repository directory")
            return
            
        try:
            self.status_label.setText("Getting repository information...")
            self.progress_bar.show()
            self.progress_bar.setValue(30)
            
            def task_func():
                github_assistant = GitHubAssistant(repo_path=repo_path)
                info = github_assistant.get_repo_info()
                return json.dumps(info, indent=2)
            
            worker = TaskWorker("get_repo_info", task_func)
            worker.task_completed.connect(self.handle_task_completed)
            worker.task_error.connect(self.handle_task_error)
            worker.start()
            
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
    
    def analyze_codebase(self):
        """Analyze the codebase structure"""
        repo_path = self.repo_path.text()
        if not repo_path or not os.path.isdir(repo_path):
            self.show_error("Please select a valid repository directory")
            return
            
        try:
            self.status_label.setText("Analyzing codebase structure...")
            self.progress_bar.show()
            self.progress_bar.setValue(10)
            
            def task_func():
                analyzer = CodebaseAnalyzer(base_path=repo_path)
                analyzer.set_groq_assistant(self.groq_assistant)
                structure = analyzer.analyze_codebase_structure()
                
                result = f"Codebase Analysis Results:\n"
                result += f"Python Files: {structure['python_files']}\n"
                result += f"JavaScript Files: {structure['js_files']}\n"
                result += f"HTML Files: {structure['html_files']}\n"
                result += f"CSS Files: {structure['css_files']}\n"
                result += f"Total Files: {structure['total_files']}\n\n"
                
                # Analyze Python files (limit to first 3 to avoid long processing)
                python_files = analyzer.find_files(extension=".py")
                if python_files:
                    result += f"Found {len(python_files)} Python files. Analyzing first 3...\n\n"
                    for i, file_path in enumerate(python_files[:3]):
                        result += f"File {i+1}: {os.path.basename(file_path)}\n"
                        analysis = analyzer.analyze_python_file(file_path)
                        result += f"- Classes: {len(analysis['classes'])}\n"
                        result += f"- Functions: {len(analysis['functions'])}\n"
                        result += f"- Imports: {len(analysis['imports'])}\n"
                        if analysis['classes']:
                            result += "- Class names: " + ", ".join([c['name'] for c in analysis['classes']]) + "\n"
                        result += "\n"
                
                return result
            
            worker = TaskWorker("analyze_codebase", task_func)
            worker.task_completed.connect(self.handle_task_completed)
            worker.task_error.connect(self.handle_task_error)
            worker.start()
            
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
    
    def load_repo_files(self):
        """Load repository files into the tree view"""
        repo_path = self.repo_path.text()
        if not repo_path or not os.path.isdir(repo_path):
            self.show_error("Please select a valid repository directory")
            return
            
        try:
            self.status_label.setText("Loading repository files...")
            self.file_tree.clear()
            
            def add_directory_to_tree(parent_item, dir_path, relative_path=""):
                for item in os.listdir(dir_path):
                    item_path = os.path.join(dir_path, item)
                    item_rel_path = os.path.join(relative_path, item)
                    
                    # Skip hidden files and common directories to exclude
                    if item.startswith('.') or item in ['__pycache__', 'venv', 'env', 'node_modules']:
                        continue
                        
                    if os.path.isdir(item_path):
                        dir_item = QTreeWidgetItem(parent_item, [item])
                        dir_item.setData(0, Qt.UserRole, item_rel_path)
                        add_directory_to_tree(dir_item, item_path, item_rel_path)
                    else:
                        file_item = QTreeWidgetItem(parent_item, [item])
                        file_item.setData(0, Qt.UserRole, item_rel_path)
            
            # Add the root directory
            root_item = QTreeWidgetItem(self.file_tree, [os.path.basename(repo_path)])
            root_item.setData(0, Qt.UserRole, "")
            add_directory_to_tree(root_item, repo_path)
            
            # Expand the root item
            self.file_tree.expandItem(root_item)
            self.status_label.setText("Repository files loaded")
            
        except Exception as e:
            self.show_error(f"Error loading repository files: {str(e)}")
    
    def file_tree_item_clicked(self, item, column):
        """Handle double-click on file tree item"""
        relative_path = item.data(0, Qt.UserRole)
        if not relative_path:
            return
            
        full_path = os.path.join(self.repo_path.text(), relative_path)
        
        if os.path.isfile(full_path):
            try:
                # Show file info
                file_info = f"File: {relative_path}\n"
                file_info += f"Size: {os.path.getsize(full_path)} bytes\n"
                
                # Get file history
                github_assistant = GitHubAssistant(repo_path=self.repo_path.text())
                history = github_assistant.get_file_history(relative_path)
                
                file_info += "\nCommit History:\n"
                for commit in history:
                    if "error" in commit:
                        file_info += f"Error: {commit['error']}\n"
                    else:
                        file_info += f"- {commit['message'].strip()} ({commit['author']})\n"
                
                # For Python files, show more detailed analysis
                if full_path.endswith('.py'):
                    analyzer = CodebaseAnalyzer(base_path=self.repo_path.text())
                    analysis = analyzer.analyze_python_file(full_path)
                    
                    file_info += "\nFile Analysis:\n"
                    file_info += f"Classes: {len(analysis['classes'])}\n"
                    for cls in analysis['classes']:
                        file_info += f"- {cls['name']} (line {cls['line']})\n"
                    
                    file_info += f"\nFunctions: {len(analysis['functions'])}\n"
                    for func in analysis['functions']:
                        args_str = ", ".join(func['args'])
                        file_info += f"- {func['name']}({args_str}) (line {func['line']})\n"
                
                self.github_results.setText(file_info)
                
            except Exception as e:
                self.show_error(f"Error analyzing file: {str(e)}")
    
    def toggle_key_visibility(self, state):
        """Toggle API key visibility"""
        if state == Qt.Checked:
            self.api_key_input.setEchoMode(QLineEdit.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.Password)
    
    def save_api_key(self):
        """Save API key to environment"""
        new_key = self.api_key_input.text().strip()
        if not new_key:
            self.show_error("Please enter a valid API key")
            return
            
        # In a real application, you might want to save this to a config file
        # For now, we'll just update the runtime environment
        os.environ["GROQ_API_KEY"] = new_key
        self.api_key = new_key
        
        # Reinitialize components with the new key
        self.init_components()
        
        self.status_label.setText("API key saved and applied")
    
    def change_model(self, model_name):
        """Change the model used by Groq assistant"""
        if hasattr(self, 'groq_assistant'):
            self.groq_assistant.model = model_name
            self.status_label.setText(f"Model changed to {model_name}")
    
    def handle_task_completed(self, task_name, result):
        """Handle task completion"""
        self.progress_bar.setValue(100)
        
        # Update the appropriate result display based on task name
        if task_name in ["explain_code", "suggest_improvements"]:
            self.analysis_results.setText(result)
        elif task_name in ["detect_errors", "debug_errors", "run_file"]:
            self.error_results.setText(result)
        elif task_name in ["generate_documentation", "generate_readme"]:
            self.doc_results.setText(result)
        elif task_name in ["get_repo_info", "analyze_codebase"]:
            self.github_results.setText(result)
        
        # Update status and hide progress bar
        self.status_label.setText(f"{task_name.replace('_', ' ').title()} completed")
        
        # Hide progress bar after a short delay
        QTimer.singleShot(1000, self.progress_bar.hide)
    
    def handle_task_error(self, task_name, error_message):
        """Handle task error"""
        self.progress_bar.hide()
        self.status_label.setText(f"Error in {task_name}: {error_message}")
        self.show_error(f"Error in {task_name}: {error_message}")
    
    def show_error(self, message):
        """Show error message dialog"""
        QMessageBox.critical(self, "Error", message)


def main():
    """Main function to run the application"""
    app = QApplication(sys.argv)
    
    # Set application icon
    app_icon = QIcon()
    
    # Apply dark theme palette
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(DARK_BG))
    dark_palette.setColor(QPalette.WindowText, QColor(TEXT_COLOR))
    dark_palette.setColor(QPalette.Base, QColor(LIGHTER_BG))
    dark_palette.setColor(QPalette.AlternateBase, QColor(DARK_BG))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(TEXT_COLOR))
    dark_palette.setColor(QPalette.ToolTipText, QColor(TEXT_COLOR))
    dark_palette.setColor(QPalette.Text, QColor(TEXT_COLOR))
    dark_palette.setColor(QPalette.Button, QColor(LIGHTER_BG))
    dark_palette.setColor(QPalette.ButtonText, QColor(TEXT_COLOR))
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(ACCENT_COLOR))
    dark_palette.setColor(QPalette.Highlight, QColor(ACCENT_COLOR))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(dark_palette)
    
    # Set font
    # font = QFont("Segoe UI", 9)
    # app.setFont(font)
    
    # Create and show the main window
    window = CodeAssistantUI()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()