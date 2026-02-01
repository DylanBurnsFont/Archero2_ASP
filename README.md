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

### Basic Window Capture

```python
from window_capture import BlueStacksCapture

# Initialize capture
capture = BlueStacksCapture()

# Find BlueStacks window
capture.find_bluestacks_window()

# Capture single frame
frame = capture.capture_frame()

# Start continuous capture
capture.start_capture_thread(fps=30)

# Display live stream
capture.stream_display("Game Stream")

# Stop capture
capture.stop_capture()
```

### ROI (Region of Interest) Capture

```python
# Set ROI using calibrated positions
top_left = [2405, 368]      # From positions.json
bottom_right = [2972, 719]  # From positions.json

capture.set_roi(top_left, bottom_right)
capture.start_capture_thread()
capture.stream_display("Game ROI")
```

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

## Controls

- **Q**: Quit/stop stream
- **S**: Save current frame as PNG
- **C**: Save screenshot (in skill selection mode)

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

## Customization

### Adjust Capture Settings

```python
# Change FPS
capture.start_capture_thread(fps=15)  # Lower for better performance

# Scale display
capture.stream_display("Stream", scale_factor=0.5)  # 50% size

# Larger frame buffer
capture.frame_queue = queue.Queue(maxsize=60)  # 60 frame buffer
```
After runnig the calibration, quit the program finish the run and then start it again from the home screen. The farming should then begin by itself. 

Press the key 'q' on the keyboard while in the terminal where the program was launched to quit the program

### Add Custom Processing

Modify `process_frame_for_skills()` in [skillSelection.py](skillSelection.py) to add:
- Color detection
- Template matching
- OCR text recognition
- Skill pattern recognition

## Recommendations
- Don't use Elemental Domain rune to avoid false positive detections of the start button