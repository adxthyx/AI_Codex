import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QTextEdit, QFileDialog, 
                            QComboBox, QLineEdit, QListWidget, QSplitter, QTreeView,
                            QMessageBox, QGroupBox)
from PyQt5.QtGui import QFont, QIcon, QTextCursor, QColor, QPalette
from PyQt5.QtCore import Qt, QSize, QDir
from PyQt5.QtWidgets import QFileSystemModel
import qdarkstyle

# Import from your app.py
from app import (GroqAssistant, GitHubAssistant, CodebaseAnalyzer, 
                ErrorAnalyzer, DocumentationGenerator)

class CodeAssistantUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize components from app.py
        self.init_assistants()
        
        # Setup UI
        self.setWindowTitle("Code Assistant")
        self.setGeometry(100, 100, 1200, 800)
        self.setup_ui()
        
    def init_assistants(self):
        """Initialize all the assistant classes from app.py"""
        try:
            # Try to load from environment variable
            self.groq_assistant = GroqAssistant()
            self.github_assistant = GitHubAssistant()
            self.codebase_analyzer = CodebaseAnalyzer()
            self.codebase_analyzer.set_groq_assistant(self.groq_assistant)
            self.error_analyzer = ErrorAnalyzer(self.groq_assistant)
            self.doc_generator = DocumentationGenerator(self.groq_assistant)
            self.api_initialized = True
        except ValueError:
            # API key not found, will prompt later
            self.api_initialized = False
    
    def setup_ui(self):
        """Setup the main user interface"""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create sidebar for file navigation
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        
        # File system model for the tree view
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.currentPath())
        
        # File tree view
        self.file_tree = QTreeView()
        self.file_tree.setModel(self.model)
        self.file_tree.setRootIndex(self.model.index(QDir.currentPath()))
        self.file_tree.setColumnWidth(0, 250)
        self.file_tree.setMinimumWidth(300)
        self.file_tree.clicked.connect(self.file_selected)
        
        # Repo info section
        repo_group = QGroupBox("Repository Info")
        repo_layout = QVBoxLayout(repo_group)
        self.repo_info = QTextEdit()
        self.repo_info.setReadOnly(True)
        self.repo_info.setMaximumHeight(150)
        
        repo_btn = QPushButton("Get Repo Info")
        repo_btn.clicked.connect(self.get_repo_info)
        
        repo_layout.addWidget(self.repo_info)
        repo_layout.addWidget(repo_btn)
        
        # Add widgets to sidebar
        sidebar_layout.addWidget(QLabel("Project Files"))
        sidebar_layout.addWidget(self.file_tree)
        sidebar_layout.addWidget(repo_group)
        
        # Main content area with tabs
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.code_tab = self.create_code_tab()
        self.analyze_tab = self.create_analyze_tab()
        self.document_tab = self.create_document_tab()
        self.debug_tab = self.create_debug_tab()
        
        # Add tabs
        self.tabs.addTab(self.code_tab, "Code Editor")
        self.tabs.addTab(self.analyze_tab, "Analyze")
        self.tabs.addTab(self.document_tab, "Documentation")
        self.tabs.addTab(self.debug_tab, "Debug")
        
        # Add tabs to content layout
        content_layout.addWidget(self.tabs)
        
        # API key warning if needed
        if not self.api_initialized:
            api_widget = QWidget()
            api_layout = QHBoxLayout(api_widget)
            api_layout.addWidget(QLabel("GROQ API Key:"))
            self.api_key_input = QLineEdit()
            self.api_key_input.setEchoMode(QLineEdit.Password)
            api_layout.addWidget(self.api_key_input)
            api_btn = QPushButton("Set API Key")
            api_btn.clicked.connect(self.set_api_key)
            api_layout.addWidget(api_btn)
            content_layout.addWidget(api_widget)
        
        # Status bar at the bottom
        self.statusBar().showMessage("Ready")
        
        # Create splitter between sidebar and content
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(sidebar_widget)
        splitter.addWidget(content_widget)
        splitter.setSizes([300, 900])
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
    
    def create_code_tab(self):
        """Create the code editor tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Header with file info
        header_layout = QHBoxLayout()
        self.file_path_label = QLabel("No file selected")
        header_layout.addWidget(self.file_path_label)
        
        # File operations
        open_btn = QPushButton("Open File")
        open_btn.clicked.connect(self.open_file)
        save_btn = QPushButton("Save File")
        save_btn.clicked.connect(self.save_file)
        
        header_layout.addWidget(open_btn)
        header_layout.addWidget(save_btn)
        header_layout.addStretch()
        
        # Code editor
        self.code_editor = QTextEdit()
        self.code_editor.setFont(QFont("Courier New", 10))
        
        # Code actions
        actions_layout = QHBoxLayout()
        explain_btn = QPushButton("Explain Code")
        explain_btn.clicked.connect(self.explain_code)
        suggest_btn = QPushButton("Suggest Improvements")
        suggest_btn.clicked.connect(self.suggest_improvements)
        comment_btn = QPushButton("Add Comments")
        comment_btn.clicked.connect(self.add_comments)
        
        actions_layout.addWidget(explain_btn)
        actions_layout.addWidget(suggest_btn)
        actions_layout.addWidget(comment_btn)
        
        # Results area
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)
        self.code_results = QTextEdit()
        self.code_results.setReadOnly(True)
        results_layout.addWidget(self.code_results)
        
        # Add components to layout
        layout.addLayout(header_layout)
        layout.addWidget(self.code_editor)
        layout.addLayout(actions_layout)
        layout.addWidget(results_group)
        
        return tab
    
    def create_analyze_tab(self):
        """Create the code analysis tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Analysis controls
        controls_layout = QHBoxLayout()
        
        self.analyze_path = QLineEdit()
        self.analyze_path.setText(os.getcwd())
        controls_layout.addWidget(QLabel("Path:"))
        controls_layout.addWidget(self.analyze_path)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_analyze_path)
        controls_layout.addWidget(browse_btn)
        
        analyze_btn = QPushButton("Analyze Codebase")
        analyze_btn.clicked.connect(self.analyze_codebase)
        controls_layout.addWidget(analyze_btn)
        
        # Analysis results
        self.analysis_results = QTextEdit()
        self.analysis_results.setReadOnly(True)
        
        # File list from analysis
        files_group = QGroupBox("Python Files")
        files_layout = QVBoxLayout(files_group)
        
        self.files_list = QListWidget()
        self.files_list.itemClicked.connect(self.analyze_selected_file)
        
        analyze_file_btn = QPushButton("Analyze Selected File")
        analyze_file_btn.clicked.connect(lambda: self.analyze_selected_file(self.files_list.currentItem()))
        
        files_layout.addWidget(self.files_list)
        files_layout.addWidget(analyze_file_btn)
        
        # Split view for results
        results_splitter = QSplitter(Qt.Horizontal)
        results_splitter.addWidget(files_group)
        results_splitter.addWidget(self.analysis_results)
        results_splitter.setSizes([300, 700])
        
        # Add to layout
        layout.addLayout(controls_layout)
        layout.addWidget(results_splitter)
        
        return tab
    
    def create_document_tab(self):
        """Create the documentation generation tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Documentation controls
        controls_layout = QHBoxLayout()
        
        self.doc_type = QComboBox()
        self.doc_type.addItems(["function", "class", "module", "file", "README"])
        controls_layout.addWidget(QLabel("Document Type:"))
        controls_layout.addWidget(self.doc_type)
        
        self.doc_file_path = QLineEdit()
        controls_layout.addWidget(QLabel("File:"))
        controls_layout.addWidget(self.doc_file_path)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_doc_file)
        controls_layout.addWidget(browse_btn)
        
        generate_btn = QPushButton("Generate Documentation")
        generate_btn.clicked.connect(self.generate_docs)
        controls_layout.addWidget(generate_btn)
        
        # README specific options
        readme_group = QGroupBox("README Options")
        readme_layout = QVBoxLayout(readme_group)
        
        self.project_desc = QTextEdit()
        self.project_desc.setPlaceholderText("Project Description")
        self.project_desc.setMaximumHeight(100)
        
        self.project_features = QTextEdit()
        self.project_features.setPlaceholderText("Key Features (one per line)")
        self.project_features.setMaximumHeight(100)
        
        readme_layout.addWidget(QLabel("Project Description:"))
        readme_layout.addWidget(self.project_desc)
        readme_layout.addWidget(QLabel("Key Features:"))
        readme_layout.addWidget(self.project_features)
        
        # Results
        self.doc_results = QTextEdit()
        self.doc_results.setReadOnly(True)
        
        # Layout
        layout.addLayout(controls_layout)
        layout.addWidget(readme_group)
        layout.addWidget(self.doc_results)
        
        return tab
    
    def create_debug_tab(self):
        """Create the debugging tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Debug controls
        controls_layout = QHBoxLayout()
        
        self.debug_file_path = QLineEdit()
        controls_layout.addWidget(QLabel("File:"))
        controls_layout.addWidget(self.debug_file_path)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_debug_file)
        controls_layout.addWidget(browse_btn)
        
        # Error input
        error_group = QGroupBox("Error Message")
        error_layout = QVBoxLayout(error_group)
        
        self.error_text = QTextEdit()
        error_layout.addWidget(self.error_text)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        detect_btn = QPushButton("Detect Errors")
        detect_btn.clicked.connect(self.detect_errors)
        
        debug_btn = QPushButton("Debug Error")
        debug_btn.clicked.connect(self.debug_error)
        
        run_btn = QPushButton("Run File")
        run_btn.clicked.connect(self.run_file)
        
        actions_layout.addWidget(detect_btn)
        actions_layout.addWidget(debug_btn)
        actions_layout.addWidget(run_btn)
        
        # Results
        self.debug_results = QTextEdit()
        self.debug_results.setReadOnly(True)
        
        # Layout
        layout.addLayout(controls_layout)
        layout.addWidget(error_group)
        layout.addLayout(actions_layout)
        layout.addWidget(self.debug_results)
        
        return tab
    
    def set_api_key(self):
        """Set the Groq API key and initialize components"""
        api_key = self.api_key_input.text()
        if not api_key:
            QMessageBox.warning(self, "API Key Required", "Please enter your Groq API key")
            return
        
        try:
            # Initialize components with API key
            self.groq_assistant = GroqAssistant(api_key=api_key)
            self.github_assistant = GitHubAssistant()
            self.codebase_analyzer = CodebaseAnalyzer()
            self.codebase_analyzer.set_groq_assistant(self.groq_assistant)
            self.error_analyzer = ErrorAnalyzer(self.groq_assistant)
            self.doc_generator = DocumentationGenerator(self.groq_assistant)
            
            self.api_initialized = True
            self.statusBar().showMessage("API key set successfully")
            
            # Save API key to .env file
            with open('.env', 'w') as f:
                f.write(f"GROQ_API_KEY={api_key}")
            
            QMessageBox.information(self, "Success", "API key set and saved to .env file")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize with API key: {str(e)}")
    
    # File handling functions
    def file_selected(self, index):
        """Handle file selection from tree view"""
        file_path = self.model.filePath(index)
        if os.path.isfile(file_path):
            self.file_path_label.setText(file_path)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.code_editor.setText(f.read())
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to open file: {str(e)}")
    
    def open_file(self):
        """Open a file dialog to select a file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File")
        if file_path:
            self.file_path_label.setText(file_path)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.code_editor.setText(f.read())
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to open file: {str(e)}")
    
    def save_file(self):
        """Save the current file"""
        file_path = self.file_path_label.text()
        if file_path == "No file selected":
            file_path, _ = QFileDialog.getSaveFileName(self, "Save File")
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.code_editor.toPlainText())
                self.statusBar().showMessage(f"Saved: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save file: {str(e)}")
    
    # Repository functions
    def get_repo_info(self):
        """Get and display repository information"""
        if not self.github_assistant:
            QMessageBox.warning(self, "Not Initialized", "GitHub assistant not initialized")
            return
        
        try:
            info = self.github_assistant.get_repo_info()
            self.repo_info.setText(str(info))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to get repository info: {str(e)}")
    
    # Code tab functions
    def explain_code(self):
        """Explain the current code"""
        if not self.api_initialized:
            QMessageBox.warning(self, "API Key Required", "Please set your Groq API key first")
            return
        
        code = self.code_editor.toPlainText()
        if not code:
            QMessageBox.warning(self, "Empty Code", "Please enter or open some code first")
            return
        
        self.statusBar().showMessage("Explaining code...")
        try:
            result = self.groq_assistant.explain_code(code)
            self.code_results.setText(result)
            self.statusBar().showMessage("Code explanation completed")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to explain code: {str(e)}")
            self.statusBar().showMessage("Error explaining code")
    
    def suggest_improvements(self):
        """Suggest improvements for the current code"""
        if not self.api_initialized:
            QMessageBox.warning(self, "API Key Required", "Please set your Groq API key first")
            return
        
        code = self.code_editor.toPlainText()
        if not code:
            QMessageBox.warning(self, "Empty Code", "Please enter or open some code first")
            return
        
        self.statusBar().showMessage("Analyzing for improvements...")
        try:
            result = self.groq_assistant.suggest_improvements(code)
            self.code_results.setText(result)
            self.statusBar().showMessage("Analysis completed")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to suggest improvements: {str(e)}")
            self.statusBar().showMessage("Error analyzing code")
    
    def add_comments(self):
        """Add comments to the current code"""
        if not self.api_initialized:
            QMessageBox.warning(self, "API Key Required", "Please set your Groq API key first")
            return
        
        code = self.code_editor.toPlainText()
        if not code:
            QMessageBox.warning(self, "Empty Code", "Please enter or open some code first")
            return
        
        self.statusBar().showMessage("Adding comments...")
        try:
            result = self.doc_generator.generate_code_comments(code)
            self.code_results.setText(result)
            self.statusBar().showMessage("Comments generated")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate comments: {str(e)}")
            self.statusBar().showMessage("Error generating comments")
    
    # Analyze tab functions
    def browse_analyze_path(self):
        """Browse for a directory to analyze"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.analyze_path.setText(dir_path)
    
    def analyze_codebase(self):
        """Analyze the specified codebase"""
        if not self.api_initialized:
            QMessageBox.warning(self, "API Key Required", "Please set your Groq API key first")
            return
        
        path = self.analyze_path.text()
        if not path or not os.path.isdir(path):
            QMessageBox.warning(self, "Invalid Path", "Please enter a valid directory path")
            return
        
        self.statusBar().showMessage("Analyzing codebase...")
        try:
            self.codebase_analyzer = CodebaseAnalyzer(base_path=path)
            self.codebase_analyzer.set_groq_assistant(self.groq_assistant)
            
            # Get structure
            structure = self.codebase_analyzer.analyze_codebase_structure()
            result_text = f"=== Codebase Structure ===\n"
            result_text += f"Python files: {structure['python_files']}\n"
            result_text += f"JavaScript files: {structure['js_files']}\n"
            result_text += f"HTML files: {structure['html_files']}\n"
            result_text += f"CSS files: {structure['css_files']}\n"
            result_text += f"Total files: {structure['total_files']}\n\n"
            
            # Update file list
            self.files_list.clear()
            python_files = self.codebase_analyzer.find_files(extension=".py")
            for file_path in python_files:
                self.files_list.addItem(file_path)
            
            self.analysis_results.setText(result_text)
            self.statusBar().showMessage("Codebase analysis completed")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to analyze codebase: {str(e)}")
            self.statusBar().showMessage("Error analyzing codebase")
    
    def analyze_selected_file(self, item):
        """Analyze a selected file from the list"""
        if not item:
            return
        
        file_path = item.text()
        if not os.path.isfile(file_path):
            return
        
        self.statusBar().showMessage(f"Analyzing {file_path}...")
        try:
            analysis = self.codebase_analyzer.analyze_python_file(file_path)
            
            result_text = f"=== Analysis for {file_path} ===\n"
            result_text += f"Size: {analysis['size_bytes']} bytes\n"
            result_text += f"Lines: {analysis['line_count']}\n\n"
            
            result_text += "Classes:\n"
            for cls in analysis['classes']:
                result_text += f"- {cls['name']} (line {cls['line']})\n"
            
            result_text += "\nFunctions:\n"
            for func in analysis['functions']:
                result_text += f"- {func['name']}({', '.join(func['args'])}) (line {func['line']})\n"
            
            result_text += "\nImports:\n"
            for imp in analysis['imports']:
                result_text += f"- {imp}\n"
            
            if analysis['issues']:
                result_text += "\nPotential Issues:\n"
                result_text += analysis['issues']
            
            self.analysis_results.setText(result_text)
            self.statusBar().showMessage("File analysis completed")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to analyze file: {str(e)}")
            self.statusBar().showMessage("Error analyzing file")
    
    # Documentation tab functions
    def browse_doc_file(self):
        """Browse for a file to document"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File")
        if file_path:
            self.doc_file_path.setText(file_path)
    
    def generate_docs(self):
        """Generate documentation based on selected options"""
        if not self.api_initialized:
            QMessageBox.warning(self, "API Key Required", "Please set your Groq API key first")
            return
        
        doc_type = self.doc_type.currentText()
        
        if doc_type == "README":
            description = self.project_desc.toPlainText()
            features_text = self.project_features.toPlainText()
            features = [f.strip() for f in features_text.split('\n') if f.strip()]
            
            if not description or not features:
                QMessageBox.warning(self, "Missing Information", "Please provide a project description and at least one feature")
                return
            
            self.statusBar().showMessage("Generating README...")
            try:
                result = self.doc_generator.generate_project_readme(description, features)
                self.doc_results.setText(result)
                self.statusBar().showMessage("README generated")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to generate README: {str(e)}")
                self.statusBar().showMessage("Error generating README")
        else:
            file_path = self.doc_file_path.text()
            if not file_path or not os.path.isfile(file_path):
                QMessageBox.warning(self, "Invalid File", "Please select a valid file")
                return
            
            self.statusBar().showMessage(f"Generating {doc_type} documentation...")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if doc_type == "function":
                    result = self.doc_generator.generate_function_docs(content)
                elif doc_type == "class":
                    result = self.doc_generator.generate_class_docs(content)
                elif doc_type == "module":
                    result = self.doc_generator.generate_module_docs(content)
                else:
                    result = self.groq_assistant.generate_documentation(content, doc_type=doc_type)
                
                self.doc_results.setText(result)
                self.statusBar().showMessage("Documentation generated")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to generate documentation: {str(e)}")
                self.statusBar().showMessage("Error generating documentation")
    
    # Debug tab functions
    def browse_debug_file(self):
        """Browse for a file to debug"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File")
        if file_path:
            self.debug_file_path.setText(file_path)
    
    def detect_errors(self):
        """Detect errors in the selected file"""
        if not self.api_initialized:
            QMessageBox.warning(self, "API Key Required", "Please set your Groq API key first")
            return
        
        file_path = self.debug_file_path.text()
        if not file_path or not os.path.isfile(file_path):
            QMessageBox.warning(self, "Invalid File", "Please select a valid file")
            return
        
        self.statusBar().showMessage("Detecting errors...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result = self.groq_assistant.detect_errors(content)
            self.debug_results.setText(result)
            self.statusBar().showMessage("Error detection completed")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to detect errors: {str(e)}")
            self.statusBar().showMessage("Error in error detection")
    
    def debug_error(self):
        """Debug error in the selected file"""
        if not self.api_initialized:
            QMessageBox.warning(self, "API Key Required", "Please set your Groq API key first")
            return
        
        file_path = self.debug_file_path.text()
        if not file_path or not os.path.isfile(file_path):
            QMessageBox.warning(self, "Invalid File", "Please select a valid file")
            return
        
        error_message = self.error_text.toPlainText()
        if not error_message:
            QMessageBox.warning(self, "Missing Error", "Please enter the error message")
            return
        
        self.statusBar().showMessage("Debugging error...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result = self.groq_assistant.debug_error(content, error_message)
            self.debug_results.setText(result)
            self.statusBar().showMessage("Debugging completed")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to debug error: {str(e)}")
            self.statusBar().showMessage("Error in debugging")
    
    def run_file(self):
        """Run the selected file and capture output/errors"""
        file_path = self.debug_file_path.text()
        if not file_path or not os.path.isfile(file_path):
            QMessageBox.warning(self, "Invalid File", "Please select a valid file")
            return
        
        self.statusBar().showMessage("Running file...")
        try:
            import subprocess
            import sys
            
            result = subprocess.run([sys.executable, file_path], 
                                   capture_output=True, text=True)
            
            output = result.stdout
            error = result.stderr
            
            if error:
                self.error_text.setText(error)
                self.debug_results.setText(f"File execution encountered errors. Error message has been copied to the error field.")
            else:
                self.debug_results.setText(f"File executed successfully.\n\nOutput:\n{output}")
            
            self.statusBar().showMessage("File execution completed")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to run file: {str(e)}")
            self.statusBar().showMessage("Error running file")


def main():
    app = QApplication(sys.argv)
    
    # Set dark theme
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    
    window = CodeAssistantUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()