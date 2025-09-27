#!/usr/bin/env python3
"""
Setup script for IFC Room Schedule Application
"""

from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ifc-room-schedule",
    version="1.0.0",
    author="Building Professional",
    author_email="contact@buildingpro.com",
    description="Desktop application for importing IFC files and generating room schedules",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/buildingpro/ifc-room-schedule",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Scientific/Engineering :: Architecture",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: Qt",
    ],
    license="MIT",
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-qt>=4.2.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ifc-room-schedule=main:main",
        ],
        "gui_scripts": [
            "ifc-room-schedule-gui=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "ifc_room_schedule": [
            "ui/*.py",
            "parser/*.py",
            "data/*.py",
            "export/*.py",
        ],
    },
    zip_safe=False,
)