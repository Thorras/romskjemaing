# IFC Room Schedule Application

A professional desktop application for importing IFC files, analyzing spatial data, and generating structured room schedules with NS Standards integration. Built for architects, engineers, and building professionals.

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
- **Performance Optimizations** - caching, batch processing, and memory management

### 📊 Data Analysis
- **Interactive Space Management** with detailed property views
- **Surface Area Calculations** by type (walls, floors, ceilings)
- **Space Boundary Analysis** with geometric calculations
- **Material & Thermal Properties** extraction
- **NS Standards Integration** - NS 8360/NS 3940 compliance validation

### 📤 Export Capabilities
- **JSON** - Structured data with metadata and NS Standards compliance
- **Excel** - Multi-sheet workbooks with formatting
- **CSV** - Tabular data for spreadsheets
- **PDF** - Professional reports with charts

### 🖥️ User Interface
- **Modern PyQt6 Interface** with responsive design
- **Tabbed Navigation** for surfaces and boundaries
- **Real-time Validation** with user-friendly error messages
- **Progress Indicators** for long-running operations
- **Performance Monitoring** - real-time metrics and optimization recommendations

## 📋 System Requirements

- **Operating System**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **Python**: 3.8 or higher (for source installation)
- **Memory**: 4GB RAM minimum, 8GB recommended (16GB for large IFC files)
- **Storage**: 500MB free space
- **Performance**: SSD recommended for optimal IFC processing speed

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
- **Batch Processing** - Handle multiple IFC files with performance optimizations
- **Custom Filters** - Filter spaces by properties
- **Error Recovery** - Robust handling of corrupted files
- **Memory Management** - Efficient processing of large files
- **Performance Monitoring** - Real-time metrics and optimization recommendations
- **NS Standards Integration** - Automatic compliance validation and reporting

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
├── parser/          # IFC file processing with performance optimizations
├── data/            # Data models and storage
├── export/          # Export engines (JSON, CSV, Excel, PDF)
├── mappers/         # NS Standards mappers and classifiers
├── validation/      # NS Standards validators
├── defaults/        # NS 3940 performance defaults
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
- **Performance Optimizations**: Up to 50% faster processing with caching

### Supported File Sizes
- **Small Files** (< 10MB): Instant processing with optimizations disabled
- **Medium Files** (10-100MB): 5-30 seconds with selective caching
- **Large Files** (100MB+): 1-5 minutes with full optimizations and batch processing

### Performance Features
- **Intelligent Caching** - Geometry, properties, and relationships
- **Batch Processing** - Memory-efficient handling of large datasets
- **Memory Management** - Automatic cleanup and optimization
- **Real-time Monitoring** - Performance metrics and recommendations

## 🛠️ Troubleshooting

### Common Issues
- **IFC File Won't Load**: Check file format and permissions
- **Memory Errors**: Close other applications, use 64-bit Python, enable performance optimizations
- **Export Fails**: Verify write permissions in target directory
- **UI Freezes**: Wait for operation to complete or restart
- **Slow Performance**: Enable performance optimizations, check system resources
- **Cache Issues**: Clear cache or restart application

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
- **NS Standards** - Norwegian building standards (NS 8360, NS 3940)
- **Performance Optimization** - Memory management and caching techniques

## 📞 Support

- **Documentation**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Issues**: GitHub Issues
- **Email**: contact@buildingpro.com
- **Performance Issues**: Check performance metrics and optimization recommendations
- **NS Standards**: Refer to NS 8360/NS 3940 documentation for compliance questions

---

**Ready to get started?** Download the latest release or run the deployment script!

**New in v1.1.0**: NS Standards integration, performance optimizations, and enhanced IFC processing!

## 🚀 What's New in v1.1.0

### NS Standards Integration
- **NS 8360 Compliance** - Automatic room name validation and parsing
- **NS 3940 Classification** - Intelligent room type classification and defaults
- **Standards Validation** - Comprehensive compliance checking and reporting

### Performance Optimizations
- **Intelligent Caching** - Up to 50% faster IFC processing
- **Batch Processing** - Memory-efficient handling of large files
- **Real-time Monitoring** - Performance metrics and optimization recommendations
- **Memory Management** - Automatic cleanup and resource optimization

### Enhanced IFC Processing
- **Optimized Parsing** - Faster file loading and data extraction
- **Smart Fallbacks** - Graceful handling of non-compliant data
- **Performance Metrics** - Detailed timing and memory usage statistics
- **Error Recovery** - Robust handling of corrupted or incomplete files

### Technical Improvements
- **Memory Profiling** - Real-time memory usage monitoring
- **Cache Management** - Intelligent cache sizing and TTL
- **Batch Processing** - Configurable batch sizes for optimal performance
- **System Optimization** - Automatic performance tuning based on file size

### Quality Assurance
- **Comprehensive Testing** - 331 tests with 100% pass rate
- **Performance Benchmarks** - Automated performance testing
- **Memory Leak Detection** - Proactive memory management
- **Error Handling** - Robust error recovery and user guidance

### Getting Started with v1.1.0
1. **Download** the latest release or run `deploy.bat`/`deploy.sh`
2. **Load** an IFC file to see NS Standards integration in action
3. **Monitor** performance metrics in real-time
4. **Export** enhanced JSON with NS Standards compliance data
5. **Review** optimization recommendations for your system