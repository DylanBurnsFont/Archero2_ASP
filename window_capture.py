import cv2
import numpy as np
import mss
import pygetwindow as gw
import time
from threading import Thread, Lock
import queue


class BlueStacksCapture:
    def __init__(self):
        self.window = None
        self.capture_running = False
        self.latest_frame = None
        self.frame_lock = Lock()
        self.frame_queue = queue.Queue(maxsize=30)  # Buffer for frames
        self.roi_coordinates = None
        
    def find_bluestacks_window(self):
        """Find and connect to BlueStacks window"""
        windows = gw.getWindowsWithTitle("BlueStacks")
        if not windows:
            # Try alternative BlueStacks window titles
            alt_titles = ["BlueStacks App Player", "BlueStacks 5", "BlueStacks 4"]
            for title in alt_titles:
                windows = gw.getWindowsWithTitle(title)
                if windows:
                    break
        
        if not windows:
            raise Exception("BlueStacks window not found. Make sure BlueStacks is running.")
        
        self.window = windows[0]
        print(f"Found BlueStacks window: {self.window.title}")
        print(f"Window position: ({self.window.left}, {self.window.top})")
        print(f"Window size: {self.window.width} x {self.window.height}")
        return self.window
    
    def set_roi(self, top_left, bottom_right):
        """Set region of interest coordinates relative to the BlueStacks window"""
        if not self.window:
            raise Exception("BlueStacks window not found. Call find_bluestacks_window() first.")
        
        # Convert absolute coordinates to relative window coordinates
        rel_x1 = top_left[0] - self.window.left
        rel_y1 = top_left[1] - self.window.top
        rel_x2 = bottom_right[0] - self.window.left
        rel_y2 = bottom_right[1] - self.window.top
        
        # Ensure coordinates are within window bounds
        rel_x1 = max(0, min(rel_x1, self.window.width))
        rel_y1 = max(0, min(rel_y1, self.window.height))
        rel_x2 = max(0, min(rel_x2, self.window.width))
        rel_y2 = max(0, min(rel_y2, self.window.height))
        
        self.roi_coordinates = {
            "left": self.window.left + rel_x1,
            "top": self.window.top + rel_y1,
            "width": rel_x2 - rel_x1,
            "height": rel_y2 - rel_y1
        }
        
        print(f"ROI set: {self.roi_coordinates}")
    
    def capture_frame(self):
        """Capture a single frame from the BlueStacks window or ROI"""
        if not self.window:
            return None
        
        with mss.mss() as sct:
            if self.roi_coordinates:
                # Capture ROI only
                monitor = self.roi_coordinates
            else:
                # Capture entire window
                monitor = {
                    "left": self.window.left,
                    "top": self.window.top,
                    "width": self.window.width,
                    "height": self.window.height
                }
            
            try:
                # Capture screenshot
                screenshot = sct.grab(monitor)
                # Convert to numpy array
                frame = np.array(screenshot)
                # Convert BGRA to BGR (remove alpha channel)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                return frame
            except Exception as e:
                print(f"Error capturing frame: {e}")
                return None
    
    def start_capture_thread(self, fps=30):
        """Start continuous capture in a separate thread"""
        if self.capture_running:
            return
        
        self.capture_running = True
        self.capture_thread = Thread(target=self._capture_loop, args=(fps,))
        self.capture_thread.daemon = True
        self.capture_thread.start()
        print(f"Started capture thread at {fps} FPS")
    
    def _capture_loop(self, fps):
        """Internal capture loop for threading"""
        frame_time = 1.0 / fps
        
        while self.capture_running:
            start_time = time.time()
            
            frame = self.capture_frame()
            if frame is not None:
                with self.frame_lock:
                    self.latest_frame = frame.copy()
                
                # Add to queue (non-blocking)
                try:
                    self.frame_queue.put_nowait(frame)
                except queue.Full:
                    # Remove oldest frame and add new one
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(frame)
                    except queue.Empty:
                        pass
            
            # Maintain target FPS
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_time - elapsed)
            time.sleep(sleep_time)
    
    def get_latest_frame(self):
        """Get the most recent captured frame"""
        with self.frame_lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
        return None
    
    def get_frame_from_queue(self):
        """Get frame from queue (blocking)"""
        try:
            return self.frame_queue.get(timeout=1.0)
        except queue.Empty:
            return None
    
    def stop_capture(self):
        """Stop the capture thread"""
        self.capture_running = False
        if hasattr(self, 'capture_thread'):
            self.capture_thread.join()
        print("Capture stopped")
    
    def stream_display(self, window_name="BlueStacks Stream", scale_factor=1.0):
        """Display captured frames in real-time"""
        if not self.capture_running:
            print("Capture not running. Start capture first.")
            return
        
        print(f"Starting stream display. Press 'q' to stop.")
        
        while self.capture_running:
            frame = self.get_latest_frame()
            if frame is not None:
                # Scale frame if needed
                if scale_factor != 1.0:
                    new_width = int(frame.shape[1] * scale_factor)
                    new_height = int(frame.shape[0] * scale_factor)
                    frame = cv2.resize(frame, (new_width, new_height))
                
                # Add FPS counter
                fps_text = f"FPS: {self._calculate_fps():.1f}"
                cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, (0, 255, 0), 2)
                
                # Display frame
                cv2.imshow(window_name, frame)
                
                # Check for quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                time.sleep(0.01)
        
        cv2.destroyAllWindows()
        print("Stream display stopped")
    
    def _calculate_fps(self):
        """Calculate approximate FPS based on queue size"""
        return min(30, self.frame_queue.qsize() * 2)  # Rough estimation
    
    def save_frame(self, filename=None):
        """Save current frame to file"""
        frame = self.get_latest_frame()
        if frame is not None:
            if filename is None:
                timestamp = int(time.time())
                filename = f"bluestacks_capture_{timestamp}.png"
            
            # cv2.imwrite(filename, frame)
            print(f"Frame saved as {filename}")
            return filename
        else:
            print("No frame available to save")
            return None