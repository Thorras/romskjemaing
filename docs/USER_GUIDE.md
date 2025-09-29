# Romskjema Generator - User Guide

## Overview

The Romskjema Generator is a comprehensive tool for generating enhanced room schedules from IFC files, compliant with Norwegian standards NS 8360 and NS 3940. The tool provides advanced data analysis, quality assessment, and multiple export formats.

## Features

### Core Features
- **IFC File Processing**: Load and parse IFC files with optimized performance
- **NS Standards Compliance**: Full support for NS 8360 naming and NS 3940 classification
- **Enhanced Data Export**: Comprehensive room data with Phase 2B and 2C sections
- **Data Quality Analysis**: Automated quality assessment and recommendations
- **Multiple Export Formats**: JSON, CSV, Excel, and PDF export options

### Advanced Features
- **Batch Processing**: Handle large datasets with memory management
- **Caching System**: Intelligent caching for improved performance
- **Configuration Management**: Customizable export profiles and settings
- **Real-time Monitoring**: Progress tracking and performance statistics

## Installation

### Prerequisites
- Python 3.8 or higher
- Windows 10/11 or Linux
- 4GB RAM minimum (8GB recommended)
- 1GB free disk space

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/romskjema-generator.git
   cd romskjema-generator
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation**:
   ```bash
   python main.py --version
   ```

## Quick Start

### Basic Usage

1. **Start the application**:
   ```bash
   python main.py
   ```

2. **Load an IFC file**:
   - Click "Open IFC File" button
   - Select your IFC file
   - Wait for processing to complete

3. **Review data quality**:
   - Check the Data Quality Dashboard
   - Review recommendations for improvement

4. **Export room schedule**:
   - Click "Export" button
   - Select export format and profile
   - Choose output location
   - Click "Export" to generate

### Command Line Usage

```bash
# Basic export
python main.py --input building.ifc --output room_schedule.json

# Advanced export with specific profile
python main.py --input building.ifc --output room_schedule.json --profile production

# Batch processing
python main.py --input building.ifc --output room_schedule.json --batch --chunk-size 100
```

## Export Profiles

### Core Profile
- **Purpose**: Basic room data export
- **Sections**: Identification, IFC metadata, geometry, classification
- **Use Case**: Simple room schedules, basic data analysis

### Advanced Profile
- **Purpose**: Comprehensive export with traditional sections
- **Sections**: Core + surfaces, space boundaries, relationships
- **Use Case**: Detailed room analysis, traditional workflows

### Production Profile
- **Purpose**: Full production export with all features
- **Sections**: All sections including Phase 2B and 2C
- **Use Case**: Complete room schedules, production workflows

## Data Quality Analysis

### Quality Metrics
- **NS 8360 Compliance**: Room naming standard compliance
- **NS 3940 Classification**: Function code classification
- **Data Completeness**: Quantities, surfaces, boundaries, relationships
- **Export Readiness**: Overall readiness for export

### Recommendations
The system provides automatic recommendations for:
- Improving naming compliance
- Adding missing data
- Enhancing data quality
- Optimizing export readiness

## Configuration Management

### Export Profiles
- **Create Custom Profiles**: Define custom export configurations
- **Duplicate Profiles**: Copy existing profiles for modification
- **Profile Management**: Save, load, and delete profiles

### Application Settings
- **General Settings**: Default profiles, output directories
- **Performance Settings**: Memory limits, cache settings, batch processing
- **Advanced Settings**: Logging, debugging options

## Batch Processing

### Memory Management
- **Chunk Size**: Control memory usage with chunk processing
- **Memory Limits**: Set maximum memory usage
- **Streaming Export**: Reduce memory usage for large datasets

### Performance Optimization
- **Parallel Processing**: Multi-threaded processing for better performance
- **Caching**: Intelligent caching for repeated operations
- **Progress Tracking**: Real-time progress updates

## Export Formats

### JSON Export
- **Format**: Structured JSON with metadata
- **Sections**: Configurable based on export profile
- **Use Case**: Data integration, API consumption

### CSV Export
- **Format**: Comma-separated values
- **Sections**: Flat structure with all data
- **Use Case**: Spreadsheet analysis, data import

### Excel Export
- **Format**: Microsoft Excel workbook
- **Sections**: Multiple sheets with organized data
- **Use Case**: Professional reports, client delivery

### PDF Export
- **Format**: Portable Document Format
- **Sections**: Formatted report with tables
- **Use Case**: Documentation, printing

## Troubleshooting

### Common Issues

#### Memory Issues
- **Problem**: Out of memory errors
- **Solution**: Reduce chunk size, increase memory limits, use streaming export

#### Performance Issues
- **Problem**: Slow processing
- **Solution**: Enable caching, use batch processing, optimize IFC file

#### Export Issues
- **Problem**: Export fails or incomplete
- **Solution**: Check data quality, validate IFC file, review error logs

### Error Messages

#### "IFC file not found"
- **Cause**: Invalid file path or file doesn't exist
- **Solution**: Check file path, ensure file exists

#### "Invalid IFC version"
- **Cause**: Unsupported IFC version
- **Solution**: Use IFC2x3, IFC4, IFC4x1, or IFC4x3

#### "Memory limit exceeded"
- **Cause**: Dataset too large for available memory
- **Solution**: Use batch processing, reduce chunk size

## Best Practices

### IFC File Preparation
- **Clean Geometry**: Ensure clean, valid geometry
- **Proper Naming**: Use NS 8360 compliant naming
- **Complete Data**: Include all required properties
- **Valid Classification**: Use proper NS 3940 codes

### Performance Optimization
- **Use Caching**: Enable caching for repeated operations
- **Batch Processing**: Use batch processing for large datasets
- **Memory Management**: Monitor memory usage and adjust settings
- **Regular Cleanup**: Clear cache and temporary files regularly

### Data Quality
- **Regular Validation**: Check data quality before export
- **Follow Standards**: Adhere to NS 8360 and NS 3940 standards
- **Complete Information**: Ensure all required data is present
- **Review Recommendations**: Follow system recommendations

## Support

### Documentation
- **User Guide**: This document
- **API Documentation**: Available in `docs/api/`
- **Examples**: Available in `examples/`

### Getting Help
- **Issues**: Report issues on GitHub
- **Questions**: Ask questions in discussions
- **Feature Requests**: Submit feature requests

### Version Information
- **Current Version**: 2.0.0
- **Python Version**: 3.8+
- **Last Updated**: 2024

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

We welcome contributions! Please see CONTRIBUTING.md for guidelines.

## Changelog

### Version 2.0.0
- Added Phase 2B and 2C sections
- Implemented data quality analysis
- Added batch processing capabilities
- Enhanced caching system
- Improved user interface

### Version 1.0.0
- Initial release
- Basic IFC processing
- Core export functionality
- NS standards compliance
