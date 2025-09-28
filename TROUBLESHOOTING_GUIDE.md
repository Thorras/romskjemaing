# 🔧 IFC Room Schedule - Troubleshooting Guide

## 🚨 Common Issues and Solutions

### 1. Memory Issues

#### Problem: "Out of Memory" errors when loading large IFC files
**Symptoms:**
- Application crashes during file loading
- Error message mentioning memory or RAM
- System becomes unresponsive

**Solutions:**
1. **Close other applications** to free up memory
2. **Restart the application** to clear memory leaks
3. **Use lazy loading** - the application now automatically uses batch processing for large files
4. **Upgrade system memory** for files larger than available RAM
5. **Try processing smaller files** to test if the issue is file-specific

#### Advanced Memory Optimization:
- Use **Ctrl+Shift+M** to manually clean memory
- Check **Ctrl+Shift+P** for performance statistics
- Monitor memory usage in Task Manager

---

### 2. File Loading Issues

#### Problem: IFC file won't load or gives validation errors
**Symptoms:**
- "Invalid IFC format" error
- File loads but no spaces found
- Parsing errors during loading

**Solutions:**
1. **Check file extension** - ensure file has .ifc extension
2. **Verify file integrity** - try opening in another IFC viewer
3. **Check file size** - files over 100MB require confirmation
4. **Validate IFC schema** - ensure file uses supported IFC version
5. **Check file permissions** - ensure you have read access

#### Supported File Types:
- ✅ .ifc files (IFC2x3, IFC4, IFC4.1)
- ❌ .dwg, .rvt, .3ds (not supported)

---

### 3. UI Performance Issues

#### Problem: UI freezes or becomes unresponsive
**Symptoms:**
- Application stops responding during operations
- Progress bar stuck
- Cannot interact with interface

**Solutions:**
1. **Wait for operation to complete** - large files take time
2. **Use Cancel button** if available during operations
3. **Enable lazy loading** - automatically used for large datasets
4. **Use F5 to refresh** if interface becomes stuck
5. **Restart application** if completely frozen

#### Performance Tips:
- Use **batch processing** for large files (automatic)
- **Close unused tabs** to reduce memory usage
- **Regular memory cleanup** with Ctrl+Shift+M

---

### 4. Export Issues

#### Problem: Export fails or produces empty files
**Symptoms:**
- Export dialog shows errors
- Generated files are empty or corrupted
- Permission denied errors

**Solutions:**
1. **Check disk space** - ensure sufficient space for export
2. **Verify write permissions** - check folder permissions
3. **Close exported files** if open in other applications
4. **Use different export location** - try desktop or documents
5. **Check data validity** - ensure spaces are loaded properly

#### Export Troubleshooting:
- **JSON**: Check for special characters in space names
- **Excel**: Ensure Excel is not running when exporting
- **PDF**: Verify reportlab is installed
- **CSV**: Check for commas in data fields

---

### 5. Threading Issues

#### Problem: Operations fail with threading errors
**Symptoms:**
- "Threading operation failed" messages
- Fallback to direct execution warnings
- Inconsistent operation behavior

**Solutions:**
1. **System will auto-fallback** - operations continue with direct execution
2. **Restart application** to reset threading system
3. **Check system resources** - ensure sufficient CPU/memory
4. **Update system drivers** - especially graphics drivers
5. **Run as administrator** if permission issues

---

## 🛠️ Diagnostic Tools

### Built-in Diagnostics:
- **Ctrl+Shift+P**: Performance statistics
- **F5**: Refresh view and reload data
- **Ctrl+Shift+M**: Manual memory cleanup
- **F1**: Keyboard shortcuts reference

### Log Files:
- **Location**: Application directory
- **Files**: 
  - `ifc_room_schedule.log` - General application logs
  - `ifc_room_schedule_detailed.log` - Detailed debug logs

### System Requirements Check:
```
Minimum Requirements:
- RAM: 4GB (8GB+ recommended for large files)
- Python: 3.8+
- PyQt6: 6.0+
- IfcOpenShell: Latest version
```

---

## 🔍 Advanced Troubleshooting

### Debug Mode:
1. Run application from command line
2. Check console output for detailed errors
3. Enable verbose logging in settings

### Performance Profiling:
1. Use Ctrl+Shift+P to check resource usage
2. Monitor memory consumption during operations
3. Check threading statistics for optimization

### File Analysis:
1. Use IFC validation tools before loading
2. Check file structure with text editor
3. Verify space entities exist in file

---

## 📞 Getting Help

### Before Reporting Issues:
1. ✅ Check this troubleshooting guide
2. ✅ Try the suggested solutions
3. ✅ Check log files for error details
4. ✅ Note your system specifications
5. ✅ Record steps to reproduce the issue

### Information to Include:
- **System**: OS version, RAM, Python version
- **File**: IFC file size, version, source application
- **Error**: Exact error message and log entries
- **Steps**: What you were doing when the error occurred

---

## 🚀 Performance Optimization Tips

### For Large Files (>100MB):
- ✅ Use lazy loading (automatic)
- ✅ Enable batch processing (automatic)
- ✅ Close other applications
- ✅ Use SSD storage if available
- ✅ Regular memory cleanup

### For Better UI Experience:
- ✅ Use keyboard shortcuts (F1 for list)
- ✅ Adjust font size (Ctrl+/Ctrl-/Ctrl+0)
- ✅ Regular refresh (F5)
- ✅ Monitor performance (Ctrl+Shift+P)

### For Reliable Exports:
- ✅ Ensure sufficient disk space
- ✅ Use simple file paths (avoid special characters)
- ✅ Close target applications before export
- ✅ Regular data validation

---

*Last Updated: September 28, 2025*
*Version: 1.0.0*
