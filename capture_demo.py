"""
Demo script for testing BlueStacks window capture and ROI streaming
Run this to test the capture functionality independently
"""

from window_capture import BlueStacksCapture
import cv2
import time
import keyboard


def test_capture():
    """Test basic window capture functionality"""
    print("=== BlueStacks Capture Test ===")
    
    capture = BlueStacksCapture()
    
    try:
        # Find BlueStacks window
        print("1. Finding BlueStacks window...")
        window = capture.find_bluestacks_window()
        
        # Test single frame capture
        print("2. Capturing single frame...")
        frame = capture.capture_frame()
        if frame is not None:
            print(f"   Frame captured: {frame.shape}")
            # Save test frame
            timestamp = int(time.time())
            filename = f"test_capture_{timestamp}.png"
            cv2.imwrite(filename, frame)
            print(f"   Test frame saved as {filename}")
        else:
            print("   Failed to capture frame")
            return
        
        # Test continuous capture
        print("3. Starting continuous capture...")
        capture.start_capture_thread(fps=30)
        
        print("4. Testing live stream (press 'q' to stop, 's' to save frame)...")
        print("   Close the stream window or press 'q' to continue")
        
        # Start stream in a separate thread so we can control it
        import threading
        stream_thread = threading.Thread(target=capture.stream_display, 
                                        args=("Test Stream", 0.7))
        stream_thread.daemon = True
        stream_thread.start()
        
        # Wait for user to close stream or press q
        while stream_thread.is_alive():
            if keyboard.is_pressed('s'):
                capture.save_frame()
                time.sleep(0.5)  # Prevent multiple saves
            time.sleep(0.1)
        
        print("5. Stream test completed")
        
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        capture.stop_capture()
        print("6. Capture stopped")


def test_roi_capture():
    """Test ROI (Region of Interest) capture"""
    print("\n=== ROI Capture Test ===")
    
    capture = BlueStacksCapture()
    
    try:
        # Find window
        capture.find_bluestacks_window()
        
        # Set a test ROI (center quarter of the window)
        window = capture.window
        center_x = window.left + window.width // 2
        center_y = window.top + window.height // 2
        roi_size = 200
        
        top_left = (center_x - roi_size, center_y - roi_size)
        bottom_right = (center_x + roi_size, center_y + roi_size)
        
        print(f"Setting ROI: {top_left} to {bottom_right}")
        capture.set_roi(top_left, bottom_right)
        
        # Start capture and display
        capture.start_capture_thread(fps=30)
        
        print("ROI Stream starting (press 'q' to stop)...")
        capture.stream_display("ROI Test", 1.5)  # Scale up since ROI is smaller
        
    except Exception as e:
        print(f"Error during ROI test: {e}")
    finally:
        capture.stop_capture()


def test_with_positions():
    """Test using calibrated positions from positions.json"""
    print("\n=== Positions-based ROI Test ===")
    
    try:
        import json
        with open('positions.json', 'r') as f:
            positions = json.load(f)
        
        top_left = positions['top-left']
        bottom_right = positions['bottom-right']
        
        print(f"Using calibrated positions:")
        print(f"  Top-left: {top_left}")
        print(f"  Bottom-right: {bottom_right}")
        
        capture = BlueStacksCapture()
        capture.find_bluestacks_window()
        capture.set_roi(top_left, bottom_right)
        capture.start_capture_thread(fps=30)
        
        print("Game area ROI stream (press 'q' to stop)...")
        capture.stream_display("Game Area ROI", 1.0)
        
    except FileNotFoundError:
        print("positions.json not found. Run calibration first.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'capture' in locals():
            capture.stop_capture()


if __name__ == "__main__":
    print("BlueStacks Capture Demo")
    print("Make sure BlueStacks is running before starting tests")
    print()
    
    while True:
        print("\nSelect test:")
        print("1. Basic capture test")
        print("2. ROI capture test") 
        print("3. Test with calibrated positions")
        print("4. Exit")
        
        choice = input("Enter choice (1-4): ")
        
        if choice == '1':
            test_capture()
        elif choice == '2':
            test_roi_capture()
        elif choice == '3':
            test_with_positions()
        elif choice == '4':
            print("Exiting...")
            break
        else:
            print("Invalid choice")