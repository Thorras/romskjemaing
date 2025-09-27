# IFC Room Schedule Application - Deployment Guide

## 🚀 Quick Start

### Windows
1. Run `deploy.bat`
2. Find executable in `deployment/IFC-Room-Schedule.exe`

### macOS/Linux
1. Run `chmod +x deploy.sh && ./deploy.sh`
2. Find executable in `deployment/IFC-Room-Schedule`

## 📦 Deployment Options

### 1. Standalone Executable (Recommended)

**Advantages:**
- No Python installation required
- Single file distribution
- Easy for end users

**Build Command:**
```bash
python build_executable.py
```

**Output:**
- `dist/IFC-Room-Schedule(.exe)` - Standalone executable
- `deployment/` - Complete package with documentation

### 2. Python Package Installation

**For developers or Python users:**

```bash
# Install from source
pip install -e .

# Or install from PyPI (when published)
pip install ifc-room-schedule
```

**Run:**
```bash
ifc-room-schedule
# or
python main.py
```

### 3. Docker Deployment

**Build and run:**
```bash
# Build image
docker build -t ifc-room-schedule .

# Run with GUI (Linux/macOS)
xhost +local:docker
docker run -it --rm \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v $(pwd)/data:/app/data \
    ifc-room-schedule

# Or use docker-compose
docker-compose up
```

## 🔧 Build Requirements

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 500MB free space

### Python Dependencies
```
ifcopenshell>=0.7.0    # IFC file processing
PyQt6>=6.5.0           # GUI framework
pandas>=2.0.0          # Data processing
openpyxl>=3.1.0        # Excel export
reportlab>=4.0.0       # PDF export
```

### Build Dependencies
```
pyinstaller>=5.0.0     # Executable building
pytest>=7.0.0          # Testing
black>=23.0.0          # Code formatting
flake8>=6.0.0          # Linting
```

## 📋 Pre-Deployment Checklist

### ✅ Code Quality
- [ ] All tests pass (`pytest tests/`)
- [ ] Code formatted (`black .`)
- [ ] No linting errors (`flake8`)
- [ ] Documentation updated

### ✅ Functionality
- [ ] IFC file loading works
- [ ] Space extraction functions
- [ ] Export formats (JSON, CSV, Excel, PDF) work
- [ ] Error handling is robust
- [ ] UI is responsive

### ✅ Compatibility
- [ ] Tested on target operating systems
- [ ] Dependencies are compatible
- [ ] File paths work cross-platform
- [ ] Memory usage is acceptable

## 🎯 Distribution Strategies

### 1. Direct Distribution
- Share the `deployment/` folder
- Include README and sample files
- Provide installation instructions

### 2. Installer Creation

**Windows (NSIS):**
```bash
# Install NSIS from https://nsis.sourceforge.io/
makensis installer.nsi
```

**macOS (create-dmg):**
```bash
npm install -g create-dmg
create-dmg deployment/IFC-Room-Schedule.app
```

**Linux (AppImage):**
```bash
# Use linuxdeploy or AppImageKit
linuxdeploy --appdir deployment --executable IFC-Room-Schedule --create-appimage
```

### 3. Package Repositories

**PyPI (Python Package Index):**
```bash
python setup.py sdist bdist_wheel
twine upload dist/*
```

**Homebrew (macOS):**
```ruby
# Create homebrew formula
class IfcRoomSchedule < Formula
  desc "Desktop application for IFC room schedule generation"
  homepage "https://github.com/buildingpro/ifc-room-schedule"
  url "https://github.com/buildingpro/ifc-room-schedule/archive/v1.0.0.tar.gz"
  # ... formula details
end
```

## 🔍 Troubleshooting

### Common Issues

**1. PyInstaller Build Fails**
```bash
# Clear cache and rebuild
pyinstaller --clean main.spec
```

**2. Missing Dependencies**
```bash
# Add hidden imports to build_executable.py
--hidden-import=missing_module
```

**3. Large Executable Size**
```bash
# Use --exclude-module to remove unused modules
--exclude-module=tkinter
```

**4. Qt Platform Plugin Issues**
```bash
# Set environment variable
export QT_QPA_PLATFORM=xcb  # Linux
export QT_QPA_PLATFORM=cocoa  # macOS
```

### Performance Optimization

**Reduce Executable Size:**
- Use `--exclude-module` for unused modules
- Use UPX compression (optional)
- Remove debug symbols

**Improve Startup Time:**
- Use `--onedir` instead of `--onefile` for faster startup
- Optimize imports in main.py
- Use lazy loading for heavy modules

## 📊 Deployment Metrics

### File Sizes (Approximate)
- **Executable**: 150-300 MB (includes Python runtime and all dependencies)
- **Source Code**: ~5 MB
- **Test Files**: ~10 MB

### Performance Benchmarks
- **Startup Time**: 2-5 seconds
- **IFC File Loading**: 1-10 seconds (depending on file size)
- **Export Generation**: 1-5 seconds
- **Memory Usage**: 100-500 MB (depending on IFC file size)

## 🛡️ Security Considerations

### Code Signing
- Sign executables for Windows/macOS
- Use certificates from trusted authorities
- Include timestamp servers

### Antivirus Compatibility
- Test with major antivirus software
- Submit to VirusTotal for analysis
- Use established build tools and dependencies

## 📈 Release Process

### Version Management
1. Update version in `setup.py`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v1.0.0`
4. Build and test deployment
5. Create GitHub release
6. Distribute to users

### Continuous Integration
```yaml
# .github/workflows/build.yml
name: Build and Deploy
on: [push, pull_request]
jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [windows-latest, macos-latest, ubuntu-latest]
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest
      - name: Build executable
        run: python build_executable.py
```

## 📞 Support

For deployment issues:
1. Check this documentation
2. Review error logs
3. Test on clean system
4. Contact development team

---

**Ready to deploy? Run the deployment script for your platform!**

Windows: `deploy.bat`
Unix/Linux/macOS: `./deploy.sh`