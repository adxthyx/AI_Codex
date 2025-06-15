# Code Assistant with Llama 70B-Instruct

A powerful CLI tool to help with error detection, debugging, and documentation of both GitHub projects and local codebases. This assistant leverages the Groq API to provide intelligent code analysis and suggestions.

## Features

- **Error Detection**: Analyze code for potential bugs, syntax errors, and anti-patterns
- **Debugging Assistance**: Get help understanding and fixing error messages and tracebacks
- **Documentation Generation**: Auto-generate documentation for functions, classes, modules, and entire files
- **GitHub Integration**: Analyze repository information and file history
- **Codebase Analysis**: Get insights about your project structure and complexity
- **Code Explanation**: Get plain-language explanations of complex code
- **README Generation**: Create professional README files for your projects
- **Code Commenting**: Add helpful comments to your code automatically

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/code-assistant.git
cd code-assistant

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Requirements

Create a `requirements.txt` file with these dependencies:

```
requests>=2.28.0
gitpython>=3.1.30
```

## Setup

You'll need to set up a Groq API key:

1. Sign up at [groq.com](https://groq.com) and obtain an API key
2. Set it as an environment variable:
   ```bash
   export GROQ_API_KEY=your_api_key_here
   ```
   On Windows: `set GROQ_API_KEY=your_api_key_here`

Alternatively, you can pass it directly with the `--api-key` argument.

## Usage

### Error Detection

```bash
python code_assistant.py detect-errors --file path/to/your/file.py
```

### Debug Code

```bash
python code_assistant.py debug --file path/to/your/file.py
```

### Generate Documentation

```bash
python code_assistant.py document --file path/to/your/file.py --type function
```

Available documentation types: `function`, `class`, `module`, `file`

### Analyze Codebase

```bash
python code_assistant.py analyze --path path/to/your/project
```

### GitHub Repository Information

```bash
python code_assistant.py github --repo-path path/to/your/repo
```

### Get File History

```bash
python code_assistant.py history --file path/to/your/file.py
```

### Explain Code

```bash
python code_assistant.py explain --file path/to/your/file.py
```

### Generate Project README

```bash
python code_assistant.py readme --description "My awesome project" --features "Feature 1" "Feature 2" "Feature 3"
```

### Add Comments to Code

```bash
python code_assistant.py comment --file path/to/your/file.py
```

## Examples

### Error Detection Example

```bash
$ python code_assistant.py detect-errors --file my_script.py

=== Error Detection Results ===
I've analyzed your code and found the following issues:

1. Potential missing import: The code uses 'json.loads' but 'json' is not imported
2. Unused variable 'result' on line 15
3. Possible division by zero on line 28 - consider adding a check before dividing
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
