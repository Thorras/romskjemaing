# IFC Room Schedule Application

A desktop application for importing IFC files, analyzing spatial data, and generating structured room schedules.

## Features

- Import and validate IFC files
- Extract spatial information (rooms, spaces, surfaces)
- Interactive space management with surface area calculations
- Export room schedules to Excel, CSV, and PDF formats
- User-friendly PyQt6 desktop interface

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python main.py
```

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
```

### Linting
```bash
flake8
```

## Requirements

- Python 3.8+
- IfcOpenShell for IFC file processing
- PyQt6 for the desktop interface
- Additional dependencies listed in requirements.txt