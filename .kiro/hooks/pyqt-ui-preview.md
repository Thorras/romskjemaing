# PyQt UI Preview Hook

## Trigger
- **Event**: File saved
- **File Pattern**: `**/*ui*.py, **/*widget*.py, **/*window*.py, **/*.ui`

## Description
Generates UI previews and validates PyQt interface changes when UI-related files are modified.

## Instructions
When PyQt UI files are saved:

1. Validate PyQt code syntax and imports:
   ```python
   # Check for common PyQt issues
   - Missing signal connections
   - Incorrect widget hierarchy
   - Memory leaks in widget creation
   ```

2. Generate UI screenshots or mockups:
   - Create visual previews of main windows
   - Capture dialog layouts
   - Document widget arrangements

3. Validate UI components:
   - Check signal/slot connections
   - Verify layout management
   - Test widget accessibility
   - Validate keyboard navigation

4. For .ui files (Qt Designer):
   ```bash
   pyuic6 -x file.ui -o preview_file.py
   ```

5. Generate UI documentation:
   - Widget hierarchy diagrams
   - User interaction flowcharts
   - Accessibility compliance report
   - Cross-platform compatibility notes

6. Test UI responsiveness:
   - Window resizing behavior
   - Layout adaptation
   - Font scaling compatibility

7. Create UI test scenarios:
   - User workflow validation
   - Error dialog testing
   - Progress indicator functionality

8. Update UI guidelines document with:
   - Style consistency checks
   - Color scheme validation
   - Icon usage standards

## Success Criteria
- Visual validation of UI changes
- Early detection of layout issues
- Consistent UI/UX across components
- Automated UI testing scenarios