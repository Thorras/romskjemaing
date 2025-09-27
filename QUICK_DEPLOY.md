# 🚀 Quick Deployment Guide

## Windows Users

1. **Double-click** `deploy.bat`
2. **Wait** for build to complete
3. **Find executable** in `deployment/IFC-Room-Schedule.exe`
4. **Share** the entire `deployment/` folder

## macOS/Linux Users

1. **Open terminal** in project directory
2. **Run**: `chmod +x deploy.sh && ./deploy.sh`
3. **Find executable** in `deployment/IFC-Room-Schedule`
4. **Share** the entire `deployment/` folder

## What Gets Created

```
deployment/
├── IFC-Room-Schedule(.exe)    # Main executable
├── README.md                  # User documentation
├── LICENSE                    # License file
└── sample_files/              # Sample IFC files (if available)
```

## Distribution

### For End Users
- **Share** the `deployment/` folder
- **No Python installation** required
- **Double-click** executable to run

### For Developers
- **Use** `pip install -e .` for development
- **Run** `python main.py` directly
- **Modify** and rebuild as needed

## Troubleshooting

### Build Fails
- Ensure Python 3.8+ is installed
- Check all dependencies are available
- Run tests first: `python -m pytest tests/`

### Executable Won't Run
- Check antivirus software
- Verify all files in deployment folder
- Try running from command line for error messages

### Large File Size
- Normal for standalone executable (150-300MB)
- Includes Python runtime and all dependencies
- Consider using Python package for smaller distribution

---

**Ready to deploy? Run the script for your platform!**