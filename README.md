# BlueStacks Window Capture and ROI Streaming

This project captures the BlueStacks window and streams the region of interest (ROI) for game automation.

## Features

- **Window Detection**: Automatically finds and connects to BlueStacks window
- **ROI Capture**: Captures specific game area based on calibrated positions
- **Real-time Streaming**: Live display of captured area with FPS counter

## Requirements

```
pip install opencv-python numpy mss pygetwindow keyboard pyautogui
```

## Quick Start

1. **Start BlueStacks** and open your game
2. **Run calibration** (if not done already):
   ```
   python main.py
   # Choose option 1 for calibration
   ```
3. **Test capture** functionality:
   ```
   python capture_demo.py
   ```
4. **Run skill selection** with live capture:
   ```
   python main.py
   # Choose option 2 for auto skill detection
   ```

## Usage

### Integration with Skill Selection

The capture functionality is integrated into the skill selection system:

```python
from skillSelection import skillSelection
import json

# Load calibrated positions
with open('positions.json', 'r') as f:
    positions = json.load(f)

# Run skill selection with live capture
stop_flag = {'stop': False}
skillSelection(positions, stop_flag)
```
If the calibration file is not being read correctly you can try adding the absolute path to the file instead of what there. found in **main.py** file. 

## Controls
⚠️⚠️⚠️⚠️
IMPORTANT
⚠️⚠️⚠️⚠️
- **Q**: Quit/stop stream

## File Structure

- `window_capture.py`: Core capture functionality
- `skillSelection.py`: Enhanced with capture integration
- `capture_demo.py`: Test and demo script
- `main.py`: Main application entry point
- `calibration_tool.py`: Position calibration tool
- `positions.json`: Calibrated position data

## Troubleshooting

1. **"BlueStacks window not found"**
   - Make sure BlueStacks is running and visible
   - Try alternative window titles: "BlueStacks App Player", "BlueStacks 5", etc.

2. **Poor performance**
   - Lower the FPS in `start_capture_thread(fps=15)`
   - Reduce the ROI size for smaller capture area

3. **No display window**
   - Make sure OpenCV is installed: `pip install opencv-python`
   - Check if display drivers are working

## Recommendations
- Don't use Elemental Domain rune to avoid false positive detections of the start buttons