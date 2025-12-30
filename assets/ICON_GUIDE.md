# Icon Creation Guide

## Master File
Start with a **1024x1024 PNG** file. This is your source file that you'll convert to all other sizes.

## Platform-Specific Requirements

### Windows (.ico)
**File:** `assets/icon.ico`

**Sizes needed:**
- 16x16 (taskbar, small icons)
- 32x32 (standard icons)
- 48x48 (large icons)
- 256x256 (high DPI, modern Windows)

**Format:** Multi-size ICO file (one file containing all sizes)

**Tools:**
- Online: https://www.icoconverter.com/
- Online: https://convertio.co/png-ico/
- Command line (ImageMagick): `magick convert icon.png -define icon:auto-resize=256,128,64,48,32,16 icon.ico`

### macOS (.icns)
**File:** `assets/icon.icns`

**Sizes needed:**
- 16x16
- 32x32
- 64x64
- 128x128
- 256x256
- 512x512
- 1024x1024

**Format:** ICNS (Apple's icon format)

**Tools:**
- macOS: Use `iconutil` command (built-in)
  1. Create folder: `icon.iconset/`
  2. Add PNG files named: `icon_16x16.png`, `icon_16x16@2x.png`, etc.
  3. Run: `iconutil -c icns icon.iconset`
- Online: https://cloudconvert.com/png-to-icns
- Online: https://convertio.co/png-icns/

### Linux (.png)
**File:** `assets/icon.png`

**Sizes needed:**
- 512x512 (recommended)
- 256x256 (acceptable alternative)

**Format:** PNG with transparency

**Tools:**
- Any image editor (GIMP, Photoshop, etc.)
- Just resize your 1024x1024 master to 512x512

## Quick Workflow

1. **Create master icon:**
   - Design a 1024x1024 PNG
   - Use transparent background
   - Save as `icon_master.png`

2. **Convert for Windows:**
   ```
   # Using ImageMagick (if installed)
   magick convert icon_master.png -define icon:auto-resize=256,128,64,48,32,16 assets/icon.ico
   
   # Or use online converter: https://www.icoconverter.com/
   ```

3. **Convert for macOS:**
   ```
   # On macOS, create iconset folder structure
   mkdir icon.iconset
   # Add resized PNGs (16x16, 32x32, etc.)
   iconutil -c icns icon.iconset -o assets/icon.icns
   
   # Or use online converter: https://cloudconvert.com/png-to-icns
   ```

4. **Convert for Linux:**
   ```
   # Just resize master to 512x512
   # Using ImageMagick:
   magick convert icon_master.png -resize 512x512 assets/icon.png
   ```

## Design Tips

- **Keep it simple:** Icons should be recognizable at small sizes (16x16)
- **Use transparency:** PNG/ICO/ICNS support alpha channels
- **High contrast:** Ensure visibility on light and dark backgrounds
- **Square format:** Icons are typically square
- **Avoid text:** Text becomes unreadable at small sizes
- **Test at small sizes:** Preview at 16x16 and 32x32

## Free Resources

- **Icon Design Tools:**
  - Figma (free tier)
  - Canva (free tier)
  - GIMP (free, open-source)

- **Icon Libraries:**
  - https://icons8.com/ (free with attribution)
  - https://www.flaticon.com/ (free with attribution)
  - https://thenounproject.com/ (free with attribution)

## Verification

After creating icons, verify they work:
- Windows: Right-click `.ico` file → Properties → should show preview
- macOS: Right-click `.icns` file → Get Info → should show preview
- Linux: Image viewer should display PNG correctly

