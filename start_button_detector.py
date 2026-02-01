import cv2
import numpy as np
from typing import Tuple, Optional, List
import time


class StartButtonDetector:
    def __init__(self, start_tl=None, start_br=None, debug_name="start_button"):
        # Very broad HSV color ranges to catch any gold/yellow/orange
        self.lower_orange = np.array([0, 20, 20])       # Almost any warm color
        self.upper_orange = np.array([60, 255, 255])    # Broad range to yellow
        
        # Alternative broad range
        self.lower_yellow = np.array([15, 10, 30])      # Very low saturation threshold
        self.upper_yellow = np.array([45, 255, 255])
        
        # Extremely broad catch-all range
        self.lower_gold = np.array([0, 5, 40])          # Catch almost anything yellowish
        self.upper_gold = np.array([70, 255, 255])
        
        # User-defined start button region
        self.start_tl = start_tl  # Top-left of start button area
        self.start_br = start_br  # Bottom-right of start button area
        
        # Button size constraints (must be at least 70% of user-defined region)
        self.min_button_area = 0.7   # Minimum 70% of region area
        self.max_button_area = 0.99  # Maximum 99% of region area
        
    def detect_start_button(self, frame: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect the Start button in the user-defined region
        Returns: (x, y, width, height) of button bounding box relative to frame, or None if not found
        """
        if frame is None:
            return None
            
        # If no user-defined region is set, return None
        if not self.start_tl or not self.start_br:
            print("Warning: Start button region not defined. Please run calibration.")
            return None
            
        frame_height, frame_width = frame.shape[:2]
        
        # Extract user-defined region from frame
        x1, y1 = self.start_tl
        x2, y2 = self.start_br
        
        # Ensure coordinates are within frame bounds
        x1 = max(0, min(x1, frame_width - 1))
        y1 = max(0, min(y1, frame_height - 1))
        x2 = max(x1 + 1, min(x2, frame_width))
        y2 = max(y1 + 1, min(y2, frame_height))
        
        # Extract the region of interest
        roi = frame[y1:y2, x1:x2]
        
        if roi.size == 0:
            return None
            
        roi_height, roi_width = roi.shape[:2]
        roi_area = roi_height * roi_width
        
        # Convert ROI to HSV for better color detection
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # Create masks for orange/yellow/gold colors with multiple ranges
        mask1 = cv2.inRange(hsv, self.lower_orange, self.upper_orange)
        mask2 = cv2.inRange(hsv, self.lower_yellow, self.upper_yellow)
        mask3 = cv2.inRange(hsv, self.lower_gold, self.upper_gold)
        
        # Combine all masks
        mask = cv2.bitwise_or(mask1, mask2)
        mask = cv2.bitwise_or(mask, mask3)
        
        # Clean up the mask
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours in the ROI
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Find the largest contour by area
        largest_contour = max(contours, key=cv2.contourArea)
        contour_area = cv2.contourArea(largest_contour)
        
        # Check if contour meets size requirements
        min_area = roi_area * self.min_button_area
        max_area = roi_area * self.max_button_area
        
        if contour_area < min_area or contour_area > max_area:
            return None
        
        # Get bounding rectangle of the largest contour
        roi_x, roi_y, roi_w, roi_h = cv2.boundingRect(largest_contour)
        
        # Convert ROI coordinates back to frame coordinates
        frame_x = x1 + roi_x
        frame_y = y1 + roi_y
        
        return (frame_x, frame_y, roi_w, roi_h)

    
    def get_detection_masks(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Get the color detection masks for visualization
        Returns: Combined mask showing detected colors in the user-defined region
        """
        if frame is None or not self.start_tl or not self.start_br:
            return None
            
        frame_height, frame_width = frame.shape[:2]
        
        # Extract user-defined region
        x1, y1 = self.start_tl
        x2, y2 = self.start_br
        
        # Ensure coordinates are within frame bounds
        x1 = max(0, min(x1, frame_width - 1))
        y1 = max(0, min(y1, frame_height - 1))
        x2 = max(x1 + 1, min(x2, frame_width))
        y2 = max(y1 + 1, min(y2, frame_height))
        
        # Extract the region of interest
        roi = frame[y1:y2, x1:x2]
        
        if roi.size == 0:
            return None
        
        # Convert ROI to HSV for better color detection
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # Create masks for orange/yellow/gold colors with multiple ranges
        mask1 = cv2.inRange(hsv, self.lower_orange, self.upper_orange)
        mask2 = cv2.inRange(hsv, self.lower_yellow, self.upper_yellow)
        mask3 = cv2.inRange(hsv, self.lower_gold, self.upper_gold)
        
        # Combine all masks
        roi_mask = cv2.bitwise_or(mask1, mask2)
        roi_mask = cv2.bitwise_or(roi_mask, mask3)
        
        # Clean up the mask
        kernel = np.ones((5, 5), np.uint8)
        cleaned_roi_mask = cv2.morphologyEx(roi_mask, cv2.MORPH_CLOSE, kernel)
        cleaned_roi_mask = cv2.morphologyEx(cleaned_roi_mask, cv2.MORPH_OPEN, kernel)
        
        # Create full-size mask and place ROI mask in the correct position
        full_mask = np.zeros((frame_height, frame_width), dtype=np.uint8)
        full_mask[y1:y2, x1:x2] = cleaned_roi_mask
        
        return full_mask
    
    def detect_with_template_matching(self, frame: np.ndarray, template: np.ndarray, threshold: float = 0.8) -> Optional[Tuple[int, int, int, int]]:
        """
        Alternative detection using template matching
        template: A cropped image of the Start button
        """
        if frame is None or template is None:
            return None
            
        # Convert to grayscale
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY) if len(template.shape) == 3 else template
        
        # Perform template matching
        result = cv2.matchTemplate(gray_frame, gray_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= threshold:
            # Get template dimensions
            template_height, template_width = gray_template.shape
            
            # Return bounding box
            x, y = max_loc
            return (x, y, template_width, template_height)
            
        return None
    
    def is_on_home_screen(self, frame: np.ndarray) -> bool:
        """
        Simple home screen detection - just check if start button exists in the user-defined region
        """
        if frame is None:
            return False
            
        # Simply check if we can detect a start button in the user-defined region
        start_button = self.detect_start_button(frame)
        return start_button is not None
    
    def _get_gold_pixel_ratio(self, frame: np.ndarray) -> float:
        """Calculate ratio of gold/yellow pixels in frame"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Create mask for gold/yellow colors with all ranges
        mask1 = cv2.inRange(hsv, self.lower_orange, self.upper_orange)
        mask2 = cv2.inRange(hsv, self.lower_yellow, self.upper_yellow)
        mask3 = cv2.inRange(hsv, self.lower_gold, self.upper_gold)
        mask = cv2.bitwise_or(mask1, mask2)
        mask = cv2.bitwise_or(mask, mask3)
        
        # Calculate ratio
        gold_pixels = np.sum(mask > 0)
        total_pixels = mask.shape[0] * mask.shape[1]
        
        return gold_pixels / total_pixels if total_pixels > 0 else 0.0
    
    def draw_detection_debug(self, frame: np.ndarray, bbox: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """
        Draw debug visualization on frame
        """
        debug_frame = frame.copy()
        
        # Draw the user-defined region
        if self.start_tl and self.start_br:
            cv2.rectangle(debug_frame, self.start_tl, self.start_br, (255, 0, 0), 2)
            cv2.putText(debug_frame, "START REGION", (self.start_tl[0], self.start_tl[1] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        
        if bbox is None:
            bbox = self.detect_start_button(frame)
            
        
        return debug_frame