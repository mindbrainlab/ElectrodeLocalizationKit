# Windows Setup and Cross-Platform Compatibility

This document describes the changes made to ensure the PyQt6 GUI works correctly on Windows.

## Changes Made for Cross-Platform Compatibility

### 1. Platform-Specific Styling (`src/ui/platform_styles.py`)
A new module handles platform detection and applies Windows-specific adjustments:
- High DPI scaling support
- Widget padding adjustments for Windows rendering
- QGroupBox title positioning fixes
- Button and input widget minimum height settings

### 2. Updated Main Application (`src/main.py`)
- Added high DPI scale factor configuration before QApplication creation
- Automatically applies platform-specific stylesheet adjustments
- Uses `Qt.HighDpiScaleFactorRoundingPolicy.PassThrough` for better scaling

### 3. Base Stylesheet Improvements (`src/ui/style_blue.css`)
- Added explicit padding to buttons, spinboxes, and groupboxes
- Improved QGroupBox title positioning with `subcontrol-origin` and `subcontrol-position`
- Set minimum heights for input widgets to prevent clipping
- Enhanced cross-platform compatibility without breaking macOS appearance

## Known Platform Differences

### Windows-Specific Behavior
- **Font Rendering**: Windows renders fonts slightly larger than macOS at the same point size
- **DPI Scaling**: Windows uses system DPI scaling which affects widget sizes
- **Border Rendering**: Rounded corners and gradients may appear differently
- **Widget Spacing**: Native Windows controls have different padding defaults

### Testing on Windows
When testing on Windows, verify:
1. All buttons are fully visible with readable text
2. QGroupBox titles don't overlap with content
3. Spinboxes and input fields display values without clipping
4. Tab labels are fully visible
5. Sliders are easily grabbable

## Additional Recommendations

### For Future Development
1. **Avoid Fixed Sizes**: Use layouts and size policies instead of hardcoded pixel dimensions
2. **Test on Both Platforms**: Always test GUI changes on both macOS and Windows
3. **Use Relative Sizing**: Prefer relative units and constraints over absolute pixel values
4. **DPI Awareness**: Design with high DPI displays in mind (4K monitors, etc.)

### If Issues Persist
If you encounter layout issues on Windows:
1. Adjust scale factors in `platform_styles.py`
2. Add more specific Windows adjustments to `get_platform_stylesheet_adjustments()`
3. Consider platform-specific minimum sizes in the UI designer
4. Test with Windows display scaling at 100%, 125%, 150%, and 200%

## Environment Variables for Testing
You can force specific DPI scaling for testing:
```bash
# Windows CMD
set QT_SCALE_FACTOR=1.5
python src/main.py

# Windows PowerShell
$env:QT_SCALE_FACTOR="1.5"
python src/main.py
```

## Technical Details

### High DPI Support
The application now uses `Qt.HighDpiScaleFactorRoundingPolicy.PassThrough` which:
- Allows fractional scale factors (e.g., 1.25, 1.5)
- Prevents rounding artifacts
- Works better with Windows display scaling settings

### Stylesheet Priority
Styles are applied in this order:
1. Base stylesheet from `pyloc_main_window.py` (auto-generated from Qt Designer)
2. External stylesheet from `style_blue.css`
3. Platform-specific adjustments from `platform_styles.py`

This ensures platform adjustments override base styles without editing generated code.
