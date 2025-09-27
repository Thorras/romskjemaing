#!/usr/bin/env python3
"""
Build executable for IFC Room Schedule Application using PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_executable():
    """Build standalone executable using PyInstaller."""
    
    print("🚀 Building IFC Room Schedule Application...")
    
    # Clean previous builds
    if os.path.exists("dist"):
        shutil.rmtree("dist")
        print("✅ Cleaned previous dist directory")
    
    if os.path.exists("build"):
        shutil.rmtree("build")
        print("✅ Cleaned previous build directory")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",                    # Single executable file
        "--windowed",                   # No console window (GUI app)
        "--name=IFC-Room-Schedule",     # Executable name
        "--icon=icon.ico",              # Application icon (if exists)
        "--add-data=ifc_room_schedule;ifc_room_schedule",  # Include package
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui", 
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=ifcopenshell",
        "--hidden-import=pandas",
        "--hidden-import=openpyxl",
        "--hidden-import=reportlab",
        "--collect-all=ifcopenshell",   # Include all IfcOpenShell files
        "--collect-all=PyQt6",          # Include all PyQt6 files
        "main.py"
    ]
    
    # Remove icon parameter if icon doesn't exist
    if not os.path.exists("icon.ico"):
        cmd = [arg for arg in cmd if not arg.startswith("--icon")]
    
    try:
        print("🔨 Running PyInstaller...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ PyInstaller completed successfully")
        
        # Check if executable was created
        if sys.platform == "win32":
            exe_path = "dist/IFC-Room-Schedule.exe"
        else:
            exe_path = "dist/IFC-Room-Schedule"
            
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"✅ Executable created: {exe_path} ({size_mb:.1f} MB)")
            
            # Create deployment package
            create_deployment_package()
        else:
            print("❌ Executable not found!")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    
    return True

def create_deployment_package():
    """Create deployment package with documentation."""
    
    print("📦 Creating deployment package...")
    
    # Create deployment directory
    deploy_dir = "deployment"
    if os.path.exists(deploy_dir):
        shutil.rmtree(deploy_dir)
    os.makedirs(deploy_dir)
    
    # Copy executable
    if sys.platform == "win32":
        exe_name = "IFC-Room-Schedule.exe"
    else:
        exe_name = "IFC-Room-Schedule"
    
    shutil.copy(f"dist/{exe_name}", f"{deploy_dir}/{exe_name}")
    
    # Copy documentation
    files_to_copy = ["README.md", "LICENSE"]
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy(file, deploy_dir)
    
    # Create sample files directory
    sample_dir = f"{deploy_dir}/sample_files"
    os.makedirs(sample_dir, exist_ok=True)
    
    # Copy sample IFC files if they exist
    if os.path.exists("tesfiler"):
        for file in os.listdir("tesfiler"):
            if file.endswith(".ifc"):
                shutil.copy(f"tesfiler/{file}", sample_dir)
                break  # Copy only one sample file
    
    print(f"✅ Deployment package created in '{deploy_dir}' directory")

def install_pyinstaller():
    """Install PyInstaller if not available."""
    try:
        import PyInstaller
        print("✅ PyInstaller is already installed")
        return True
    except ImportError:
        print("📦 Installing PyInstaller...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            print("✅ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install PyInstaller")
            return False

if __name__ == "__main__":
    print("🏗️  IFC Room Schedule Application Builder")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Install PyInstaller if needed
    if not install_pyinstaller():
        sys.exit(1)
    
    # Build executable
    if build_executable():
        print("\n🎉 Build completed successfully!")
        print("\n📁 Files created:")
        print("   - dist/IFC-Room-Schedule(.exe) - Standalone executable")
        print("   - deployment/ - Complete deployment package")
        print("\n🚀 Ready for distribution!")
    else:
        print("\n❌ Build failed!")
        sys.exit(1)