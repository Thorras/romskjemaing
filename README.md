# IFC Room Schedule Application

A professional desktop application for importing IFC files, analyzing spatial data, and generating structured room schedules. Built for architects, engineers, and building professionals.

## 🚀 Quick Start

### Download & Run (Recommended)
1. **Windows**: Run `deploy.bat` → Find `deployment/IFC-Room-Schedule.exe`
2. **macOS/Linux**: Run `./deploy.sh` → Find `deployment/IFC-Room-Schedule`

### Or Install from Source
```bash
git clone https://github.com/buildingpro/ifc-room-schedule.git
cd ifc-room-schedule
pip install -e .
ifc-room-schedule
```

## ✨ Features

### 🏗️ IFC Processing
- **Import & Validate** IFC files with comprehensive error handling
- **Extract Spatial Data** - rooms, spaces, surfaces, and boundaries
- **Parse Relationships** between building elements
- **Handle Large Files** with memory-efficient processing

### 📊 Data Analysis
- **Interactive Space Management** with detailed property views
- **Surface Area Calculations** by type (walls, floors, ceilings)
- **Space Boundary Analysis** with geometric calculations
- **Material & Thermal Properties** extraction

### 📤 Export Capabilities
- **JSON** - Structured data with metadata
- **Excel** - Multi-sheet workbooks with formatting
- **CSV** - Tabular data for spreadsheets
- **PDF** - Professional reports with charts

### 🖥️ User Interface
- **Modern PyQt6 Interface** with responsive design
- **Tabbed Navigation** for surfaces and boundaries
- **Real-time Validation** with user-friendly error messages
- **Progress Indicators** for long-running operations

## 📋 System Requirements

- **Operating System**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **Python**: 3.8 or higher (for source installation)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 500MB free space

## 🔧 Installation Options

### 1. Standalone Executable (No Python Required)
```bash
# Windows
deploy.bat

# macOS/Linux
chmod +x deploy.sh && ./deploy.sh
```

### 2. Python Package
```bash
pip install ifc-room-schedule
ifc-room-schedule
```

### 3. Docker
```bash
docker-compose up
```

### 4. Development Setup
```bash
git clone https://github.com/buildingpro/ifc-room-schedule.git
cd ifc-room-schedule
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py
```

## 📖 Usage Guide

### Basic Workflow
1. **Load IFC File** - Use File → Open or drag & drop
2. **Browse Spaces** - Navigate through extracted spaces
3. **Add Descriptions** - Document surfaces and boundaries
4. **Export Data** - Choose format and save results

### Advanced Features
- **Batch Processing** - Handle multiple IFC files
- **Custom Filters** - Filter spaces by properties
- **Error Recovery** - Robust handling of corrupted files
- **Memory Management** - Efficient processing of large files

## 🧪 Quality Assurance

### Test Coverage
- **331 Tests** with 100% pass rate
- **Unit Tests** for all core components
- **Integration Tests** for complete workflows
- **UI Tests** for user interface components

### Code Quality
- **Type Hints** throughout codebase
- **Error Handling** with comprehensive recovery
- **Memory Management** with automatic cleanup
- **Cross-Platform** compatibility

## 🏗️ Architecture

```
ifc_room_schedule/
├── ui/              # PyQt6 user interface
├── parser/          # IFC file processing
├── data/            # Data models and storage
├── export/          # Export engines (JSON, CSV, Excel, PDF)
└── tests/           # Comprehensive test suite
```

## 🤝 Contributing

### Development Setup
```bash
git clone https://github.com/buildingpro/ifc-room-schedule.git
cd ifc-room-schedule
pip install -e ".[dev]"
```

### Running Tests
```bash
pytest tests/ -v                    # Run all tests
pytest tests/test_ui_integration.py # Run specific test file
python -m pytest --cov             # Run with coverage
```

### Code Quality
```bash
black .                 # Format code
flake8                  # Check linting
mypy ifc_room_schedule  # Type checking
```

## 📊 Performance

### Benchmarks
- **Startup Time**: 2-5 seconds
- **IFC Loading**: 1-10 seconds (file size dependent)
- **Export Generation**: 1-5 seconds
- **Memory Usage**: 100-500 MB (file size dependent)

### Supported File Sizes
- **Small Files** (< 10MB): Instant processing
- **Medium Files** (10-100MB): 5-30 seconds
- **Large Files** (100MB+): 1-5 minutes with progress indicators

## 🛠️ Troubleshooting

### Common Issues
- **IFC File Won't Load**: Check file format and permissions
- **Memory Errors**: Close other applications, use 64-bit Python
- **Export Fails**: Verify write permissions in target directory
- **UI Freezes**: Wait for operation to complete or restart

### Getting Help
1. Check [DEPLOYMENT.md](DEPLOYMENT.md) for detailed guides
2. Review error logs in application directory
3. Test with sample IFC files
4. Contact support team

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🏆 Acknowledgments

- **IfcOpenShell** - IFC file processing library
- **PyQt6** - Cross-platform GUI framework
- **Building Industry** - For IFC standards and specifications

## 📞 Support

- **Documentation**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Issues**: GitHub Issues
- **Email**: contact@buildingpro.com

---

**Ready to get started?** Download the latest release or run the deployment script!