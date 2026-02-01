import cv2
import keyboard
import time
import pygetwindow as gw
import mss
import numpy as np
from window_capture import BlueStacksCapture
from start_button_detector import StartButtonDetector
import threading
import pyautogui


def skillSelection(positions, stop_flag):
    topLeft = positions['top-left']
    bottomRight = positions['bottom-right']
    # Use skill area instead of individual points
    skillAreaTL = positions['skill-area-tl']
    skillAreaBR = positions['skill-area-br']
    startTL = positions['start-tl']
    startBR = positions['start-br']
    carouselTL = positions['carousel-tl']
    carouselBR = positions['carousel-br']

    # Initialize BlueStacks capture and Start button detector
    capture = BlueStacksCapture()
    # Convert absolute coordinates to ROI-relative coordinates for the detector
    start_tl_roi = (startTL[0] - topLeft[0], startTL[1] - topLeft[1])
    start_br_roi = (startBR[0] - topLeft[0], startBR[1] - topLeft[1])
    carousel_tl_roi = (carouselTL[0] - topLeft[0], carouselTL[1] - topLeft[1])
    carousel_br_roi = (carouselBR[0] - topLeft[0], carouselBR[1] - topLeft[1])
    start_detector = StartButtonDetector(start_tl_roi, start_br_roi, "start_button")
    carousel_detector = StartButtonDetector(carousel_tl_roi, carousel_br_roi, "carousel_button")
    try:
        # Find BlueStacks window
        capture.find_bluestacks_window()
        
        # Set ROI based on calibrated positions
        capture.set_roi(topLeft, bottomRight)
        
        # Start capture thread
        capture.start_capture_thread(fps=30)
        
        print("Starting skill selection with Start button detection...")
        print("Press 's' to show/hide stream, 'c' to save screenshot")
        print("Press 'h' to check for home screen, 'enter' to click Start button")
        
        # Start stream display with start button visualization
        def enhanced_stream_display():
            """Enhanced stream with start button area visualization"""
            nonlocal level_up_detected, skill_regions
            while not stop_flag['stop']:
                frame = capture.get_latest_frame()
                if frame is not None:
                    display_frame = frame.copy()
                    
                    # Calculate brightness
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    mean_brightness = np.mean(gray)
                    
                    # Convert absolute start button coordinates to ROI-relative coordinates
                    start_tl_roi = (startTL[0] - topLeft[0], startTL[1] - topLeft[1])
                    start_br_roi = (startBR[0] - topLeft[0], startBR[1] - topLeft[1])
                    
                    # Ensure coordinates are within frame bounds
                    frame_height, frame_width = frame.shape[:2]
                    start_tl_roi = (max(0, start_tl_roi[0]), max(0, start_tl_roi[1]))
                    start_br_roi = (min(frame_width, start_br_roi[0]), min(frame_height, start_br_roi[1]))
                    
                    # Detect both types of start buttons
                    main_start_button = start_detector.detect_start_button(frame)
                    carousel_start_button = carousel_detector.detect_start_button(frame)
                    is_home = start_detector.is_on_home_screen(frame)
                    
                    # Show color detection masks as overlays
                    main_mask = start_detector.get_detection_masks(frame)
                    carousel_mask = carousel_detector.get_detection_masks(frame)
                    
                    if main_mask is not None:
                        # Convert mask to colored overlay (red for main start)
                        mask_colored = np.zeros_like(display_frame)
                        mask_colored[:, :, 2] = main_mask  # Red channel
                        display_frame = cv2.addWeighted(display_frame, 0.8, mask_colored, 0.2, 0)
                    
                    if carousel_mask is not None:
                        # Convert mask to colored overlay (green for carousel start)
                        mask_colored = np.zeros_like(display_frame)
                        mask_colored[:, :, 1] = carousel_mask  # Green channel
                        display_frame = cv2.addWeighted(display_frame, 0.8, mask_colored, 0.2, 0)
                    
                    # Draw main start button detection
                    if main_start_button:
                        x, y, w, h = main_start_button
                        # Draw cyan rectangle around detected main button
                        cv2.rectangle(display_frame, (x, y), (x + w, y + h), (255, 255, 0), 3)
                        # Draw center point
                        center_x = x + w // 2
                        center_y = y + h // 2
                        cv2.circle(display_frame, (center_x, center_y), 8, (255, 255, 0), -1)
                        # Add button label
                        cv2.putText(display_frame, "MAIN START BUTTON", (x, y - 15), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    
                    # Draw carousel start button detection
                    if carousel_start_button:
                        x, y, w, h = carousel_start_button
                        # Draw green rectangle around detected carousel button
                        cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                        # Draw center point
                        center_x = x + w // 2
                        center_y = y + h // 2
                        cv2.circle(display_frame, (center_x, center_y), 8, (0, 255, 0), -1)
                        # Add button label
                        cv2.putText(display_frame, "CAROUSEL START BUTTON", (x, y - 15), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    # Show status information
                    cv2.putText(display_frame, f"Brightness: {mean_brightness:.1f}", (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(display_frame, f"Home Screen: {is_home}", (10, 60), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(display_frame, f"Main Start: {main_start_button is not None}", (10, 90), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(display_frame, f"Carousel Start: {carousel_start_button is not None}", (10, 120), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(display_frame, f"Skill Selection: {level_up_detected}", (10, 150), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if level_up_detected else (255, 255, 255), 2)
                    
                    # Calculate and display color areas (always show for debugging)
                    if level_up_detected and skill_regions is not None:
                        color_areas = {"green": 0, "blue": 0, "purple": 0, "gold": 0, "none": 0}
                        total_regions_processed = 0
                        
                        # Calculate total areas from all regions
                        for i, region in enumerate(skill_regions):
                            x, y, w, h = region
                            # skill_regions are already in ROI coordinates, no need to convert
                            roi_x = x
                            roi_y = y
                            
                            if roi_y >= 0 and roi_x >= 0 and roi_y + h <= frame.shape[0] and roi_x + w <= frame.shape[1]:
                                skill_area = frame[roi_y:roi_y+h, roi_x:roi_x+w]
                                if skill_area.size > 0:
                                    total_regions_processed += 1
                                    skill_color, color_area = analyze_skill_color_with_area(skill_area)
                                    
                                    if skill_color in color_areas:
                                        color_areas[skill_color] += color_area
                        
                        # Display debug info and color areas on the right side
                        frame_width = display_frame.shape[1]
                        y_pos = 30
                        cv2.putText(display_frame, f"Regions: {total_regions_processed}/3", 
                                   (frame_width - 180, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                        y_pos += 25
                        
                        # Show all colors including none, and show areas even if 0
                        for color, area in color_areas.items():
                            color_bgr = {"green": (0, 255, 0), "blue": (255, 0, 0), "purple": (255, 0, 255), 
                                       "gold": (0, 255, 255), "none": (128, 128, 128)}[color]
                            cv2.putText(display_frame, f"{color.upper()}: {area}px", 
                                       (frame_width - 180, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_bgr, 2)
                            y_pos += 25
                    
                    # Show skill area outline only when appropriate
                    skill_tl_roi = (skillAreaTL[0] - topLeft[0], skillAreaTL[1] - topLeft[1])
                    skill_br_roi = (skillAreaBR[0] - topLeft[0], skillAreaBR[1] - topLeft[1])
                    
                    # Only show skill regions if level up detected and we're in skill selection
                    if level_up_detected and skill_regions is not None:
                        # Show skill area outline when in skill selection
                        cv2.rectangle(display_frame, skill_tl_roi, skill_br_roi, (255, 0, 255), 2)
                        cv2.putText(display_frame, "SKILL SELECTION ACTIVE", (skill_tl_roi[0], skill_tl_roi[1] - 10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
                        
                        # Draw vertical division lines at 1/3 and 2/3
                        area_width = skill_br_roi[0] - skill_tl_roi[0]
                        area_height = skill_br_roi[1] - skill_tl_roi[1]
                        
                        # Line at 1/3 position
                        line1_x = skill_tl_roi[0] + int(area_width / 3)
                        cv2.line(display_frame, (line1_x, skill_tl_roi[1]), (line1_x, skill_br_roi[1]), (255, 0, 255), 2)
                        
                        # Line at 2/3 position
                        line2_x = skill_tl_roi[0] + int(area_width * 2 / 3)
                        cv2.line(display_frame, (line2_x, skill_tl_roi[1]), (line2_x, skill_br_roi[1]), (255, 0, 255), 2)
                        
                        # Three center points for skill regions
                        cv2.circle(display_frame, (skill_tl_roi[0] + area_width // 6, skill_tl_roi[1] + area_height // 2), 6, (255, 0, 255), -1)
                        cv2.circle(display_frame, (skill_tl_roi[0] + area_width // 2, skill_tl_roi[1] + area_height // 2), 6, (255, 0, 255), -1)
                        cv2.circle(display_frame, (skill_tl_roi[0] + area_width * 5 // 6, skill_tl_roi[1] + area_height // 2), 6, (255, 0, 255), -1)

                        # Show the 3 skill regions
                        for i, region in enumerate(skill_regions):
                            x, y, w, h = region
                            # skill_regions are already in ROI coordinates
                            roi_x = x
                            roi_y = y
                            
                            # Draw skill region
                            cv2.rectangle(display_frame, (roi_x, roi_y), (roi_x + w, roi_y + h), (0, 255, 255), 2)
                            
                            # Extract and analyze skill region for individual display
                            if roi_y >= 0 and roi_x >= 0 and roi_y + h <= frame.shape[0] and roi_x + w <= frame.shape[1]:
                                skill_area = frame[roi_y:roi_y+h, roi_x:roi_x+w]
                                skill_color, color_area = analyze_skill_color_with_area(skill_area)
                                
                                # Display individual skill info with area
                                cv2.putText(display_frame, f"SKILL {i+1}: {skill_color} ({color_area}px)", 
                                           (roi_x, roi_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                    
                    # Display the enhanced frame
                    cv2.imshow("Archero ROI Stream", cv2.resize(display_frame, None, fx=0.8, fy=0.8))
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                        
                time.sleep(0.033)  # ~30 FPS
            
            cv2.destroyAllWindows()
        
        # Start enhanced stream display in separate thread
        stream_thread = threading.Thread(target=enhanced_stream_display)
        stream_thread.daemon = True
        stream_thread.start()
        
        last_detection_time = 0
        detection_cooldown = 1.0  # Check for start button every second
        last_click_time = 0  # Track last click to prevent spam clicking
        click_cooldown = 5.0  # Minimum time between automatic clicks
        
        # Game state tracking
        game_state = "WAITING_FOR_START"  # States: WAITING_FOR_START, WAITING_FOR_SKILL_SELECTION, WALKING_UP, CAROUSEL_CLICKING, WALKING_DOWN, DETECTING_LEVELUPS
        state_start_time = current_time if 'current_time' in locals() else time.time()
        carousel_clicks_done = 0
        walking_down_start_time = 0
        
        # Run completion detection
        main_button_detected_start = None  # Track when main button first detected in DETECTING_LEVELUPS
        main_button_detection_threshold = 1.5  # seconds
        
        # Brightness monitoring for level up detection
        brightness_history = []
        brightness_window_size = 10
        # Specific brightness ranges for level up detection
        normal_brightness_min = 120
        normal_brightness_max = 140
        skill_brightness_min = 75
        skill_brightness_max = 95
        last_brightness = None
        level_up_detected = False
        skill_regions = None  # Will store the 3 skill regions when level up detected
        
        # Main skill selection loop
        while not stop_flag['stop']:
            # Get current frame
            frame = capture.get_latest_frame()
            
            if frame is not None:
                current_time = time.time()
                
                # Calculate current brightness
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                current_brightness = np.mean(gray)
                
                # Monitor brightness for level up detection
                if last_brightness is not None:
                    # Add to brightness history
                    brightness_history.append(current_brightness)
                    if len(brightness_history) > brightness_window_size:
                        brightness_history.pop(0)
                    
                    # Check for level up: transition from normal play (120-140) to skill selection (75-95)
                    if len(brightness_history) >= 5:
                        # Get recent average brightness
                        recent_avg = np.mean(brightness_history[-3:])
                        older_avg = np.mean(brightness_history[-7:-3]) if len(brightness_history) >= 7 else last_brightness
                        
                        # Check for start buttons first - if any start button is detected, we're not in skill selection
                        main_start_button = start_detector.detect_start_button(frame)
                        carousel_start_button = carousel_detector.detect_start_button(frame)
                        any_start_button_detected = main_start_button is not None or carousel_start_button is not None
                        
                        # Check if we transitioned from normal brightness to skill selection brightness
                        was_normal_brightness = normal_brightness_min <= older_avg <= normal_brightness_max
                        is_skill_brightness = skill_brightness_min <= recent_avg <= skill_brightness_max
                        
                        # Standard transition detection (only if no start buttons detected)
                        if was_normal_brightness and is_skill_brightness and not level_up_detected and not any_start_button_detected:
                            level_up_detected = True
                            skill_regions = create_skill_regions(skillAreaTL, skillAreaBR, topLeft)
                            print(f"Level up detected! Brightness transitioned from {older_avg:.1f} to {recent_avg:.1f}")
                            print(f"Skill regions created: {skill_regions}")
                        
                        # Direct skill selection detection (when starting program in skill selection)
                        elif not level_up_detected and is_skill_brightness and len(brightness_history) >= brightness_window_size and not any_start_button_detected:
                            # Check if brightness has been consistently in skill selection range
                            all_skill_brightness = all(skill_brightness_min <= b <= skill_brightness_max for b in brightness_history[-5:])
                            if all_skill_brightness:
                                level_up_detected = True
                                skill_regions = create_skill_regions(skillAreaTL, skillAreaBR, topLeft)
                                print(f"Skill selection detected at startup! Brightness consistently at {recent_avg:.1f}")
                                print(f"Skill regions created: {skill_regions}")
                        
                        # Reset level up detection when brightness returns to normal OR start button is detected
                        elif level_up_detected and (normal_brightness_min <= recent_avg <= normal_brightness_max or any_start_button_detected):
                            level_up_detected = False
                            skill_regions = None
                            if any_start_button_detected:
                                print(f"Skill selection ended. Start button detected.")
                            else:
                                print(f"Skill selection ended. Brightness returned to normal: {recent_avg:.1f}")
                
                last_brightness = current_brightness
                
                # Handle game state transitions and actions
                game_state = handle_game_state_actions(game_state, current_time, walking_down_start_time)
                
                # Process frame for skills if level up detected
                if level_up_detected and skill_regions is not None:
                    detected_skills = process_frame_for_skills(frame, {'skill_regions': skill_regions})
                    if detected_skills:
                        print(f"Skills detected: {detected_skills}")
                        print(f"Current game state: {game_state}")
                    
                    # Auto-select skill if in waiting state
                    if game_state == "WAITING_FOR_SKILL_SELECTION":
                        print(f"In WAITING_FOR_SKILL_SELECTION: time elapsed = {current_time - state_start_time:.1f}s")
                        print(f"Skill regions available: {skill_regions is not None}, count: {len(skill_regions) if skill_regions else 0}")
                        # Wait 2 seconds after skill selection appears to ensure stability
                        if current_time - state_start_time > 2.0:
                            print(f"About to click skill with regions: {skill_regions}")
                            click_random_skill(skill_regions, topLeft)
                            game_state = "WALKING_UP"
                            state_start_time = current_time
                            print("Game state changed to WALKING_UP")
                    
                    # If we detect levelup while in DETECTING_LEVELUPS state, handle skill selection
                    elif game_state == "DETECTING_LEVELUPS":
                        print(f"In DETECTING_LEVELUPS: time elapsed = {current_time - state_start_time:.1f}s")
                        if current_time - state_start_time > 3.0:  # Wait for stability
                            print(f"About to click skill in DETECTING_LEVELUPS with regions: {skill_regions}")
                            click_random_skill(skill_regions, topLeft)
                            # Stay in DETECTING_LEVELUPS state to continue farming
                            state_start_time = current_time
                            print("Level up skill selected, continuing to detect levelups")
                    
                    # If we detect skills while in WAITING_FOR_START, the game has started but state wasn't updated
                    elif game_state == "WAITING_FOR_START":
                        print(f"Skills detected while in WAITING_FOR_START - game has started, transitioning to skill selection")
                        print(f"About to click skill with regions: {skill_regions}")
                        click_random_skill(skill_regions, topLeft)
                        # Transition to WALKING_UP to walk forward after initial skill selection
                        game_state = "WALKING_UP"
                        state_start_time = current_time
                        print("Game state changed to WALKING_UP")
                
                # Periodically check for both types of Start buttons (don't spam detection)
                if current_time - last_detection_time > detection_cooldown:
                    # Check if we're on home screen
                    is_home = start_detector.is_on_home_screen(frame)
                    
                    # Check for both button types
                    main_start_button = start_detector.detect_start_button(frame)
                    carousel_start_button = carousel_detector.detect_start_button(frame)
                    
                    if main_start_button:
                        print(f"Main start button detected at: {main_start_button}")
                        # Auto-click main start button with Gaussian noise
                        if current_time - last_click_time > click_cooldown and game_state == "WAITING_FOR_START":
                            # Generate Gaussian noise for position (25 pixels standard deviation)
                            noise_x = np.random.normal(0, 25)
                            noise_y = np.random.normal(0, 15)
                            
                            # Generate Gaussian delay (minimum 1 second, std dev 0.5 seconds)
                            delay = max(1.0, np.random.normal(1.5, 0.5))
                            
                            print(f"Auto-clicking main start button in {delay:.1f}s with noise ({noise_x:.1f}, {noise_y:.1f})")
                            
                            # Schedule the click in a separate thread
                            def delayed_click():
                                time.sleep(delay)
                                click_start_button_with_noise(capture.window, main_start_button, topLeft, noise_x, noise_y)
                                nonlocal game_state, state_start_time
                                game_state = "WAITING_FOR_SKILL_SELECTION"
                                state_start_time = time.time()
                                print("Game state changed to WAITING_FOR_SKILL_SELECTION")
                            
                            click_thread = threading.Thread(target=delayed_click)
                            click_thread.daemon = True
                            click_thread.start()
                            
                            last_click_time = current_time
                    if carousel_start_button:
                        print(f"Carousel start button detected at: {carousel_start_button}")
                        
                        # If walking up and found carousel, start clicking sequence
                        if game_state == "WALKING_UP":
                            print("Starting carousel clicking sequence - button detected and in WALKING_UP state")
                            game_state = "CAROUSEL_CLICKING"
                            state_start_time = current_time
                            carousel_clicks_done = 0
                            print("Game state changed to CAROUSEL_CLICKING")
                            
                            # Capture the button coordinates before threading
                            captured_button = carousel_start_button
                            
                            # Start carousel clicking sequence
                            def carousel_click_sequence():
                                nonlocal carousel_clicks_done
                                # Random number of clicks between 4-6
                                num_clicks = np.random.randint(4, 7)  # 4, 5, or 6
                                print(f"Carousel clicking sequence starting with {num_clicks} clicks")
                                
                                for i in range(num_clicks):
                                    if carousel_clicks_done < num_clicks:
                                        # Generate noise for each click
                                        noise_x = np.random.normal(0, 25)
                                        noise_y = np.random.normal(0, 25)
                                        
                                        click_start_button_with_noise(capture.window, captured_button, topLeft, noise_x, noise_y)
                                        carousel_clicks_done += 1
                                        print(f"Carousel click {carousel_clicks_done}/{num_clicks} completed")
                                        
                                        if i < num_clicks - 1:  # Don't wait after the last click
                                            # Random delay between 500-700ms
                                            delay = np.random.uniform(0.8, 1.2)
                                            print(f"Waiting {delay*1000:.0f}ms before next carousel click")
                                            time.sleep(delay)
                                
                                print("Carousel clicking sequence completed")
                            
                            click_thread = threading.Thread(target=carousel_click_sequence)
                            click_thread.daemon = True
                            click_thread.start()
                
                # Check if carousel clicking is complete and transition to walking down
                if game_state == "CAROUSEL_CLICKING" and carousel_clicks_done >= 4:
                    game_state = "WALKING_DOWN"
                    walking_down_start_time = current_time
                    print("Game state changed to WALKING_DOWN")
                
                # Check for run completion: main start button detected for 1.5+ seconds in DETECTING_LEVELUPS
                if game_state == "DETECTING_LEVELUPS":
                    main_start_button = start_detector.detect_start_button(frame)
                    
                    if main_start_button:
                        # Start tracking if we just detected the button
                        if main_button_detected_start is None:
                            main_button_detected_start = current_time
                            print("Main start button detected during farming - tracking for run completion")
                        
                        # Check if button has been detected for long enough
                        elif current_time - main_button_detected_start >= main_button_detection_threshold:
                            print(f"Run completed! Main start button detected for {current_time - main_button_detected_start:.1f}s")
                            game_state = "WAITING_FOR_START"
                            state_start_time = current_time
                            main_button_detected_start = None
                            level_up_detected = False
                            skill_regions = None
                            print("Game state changed to WAITING_FOR_START")
                    else:
                        # Reset tracking if button is no longer detected
                        if main_button_detected_start is not None:
                            print("Main start button no longer detected - resetting run completion tracking")
                            main_button_detected_start = None
                    
                    if is_home and not main_start_button and not carousel_start_button:
                        print("On home screen but no start buttons clearly detected")
                    
                    last_detection_time = current_time
                
                # Process frame for skills (your existing logic)
                process_frame_for_skills(frame, positions)
            
            # Check for user input
            if keyboard.is_pressed('c'):
                capture.save_frame()
                time.sleep(0.5)  # Prevent multiple saves
                
            if keyboard.is_pressed('h'):
                # Manual home screen check
                if frame is not None:
                    is_home = start_detector.is_on_home_screen(frame)
                    main_start_button = start_detector.detect_start_button(frame)
                    carousel_start_button = carousel_detector.detect_start_button(frame)
                    print(f"Home screen check - Is home: {is_home}")
                    print(f"Main start button: {main_start_button}")
                    print(f"Carousel start button: {carousel_start_button}")
                time.sleep(0.5)
                
            if keyboard.is_pressed('enter'):
                # Manual start button click - prioritize based on context
                if frame is not None:
                    main_start_button = start_detector.detect_start_button(frame)
                    carousel_start_button = carousel_detector.detect_start_button(frame)
                    
                    # Determine which button to click based on priority
                    button_to_click = None
                    button_type = None
                    
                    if carousel_start_button:
                        # Prioritize carousel button if available (game already started)
                        button_to_click = carousel_start_button
                        button_type = "carousel"
                    elif main_start_button:
                        # Use main start button if no carousel (home screen)
                        button_to_click = main_start_button
                        button_type = "main"
                    
                    if button_to_click:
                        print(f"Clicking {button_type} start button")
                        click_start_button(capture.window, button_to_click, topLeft)
                    else:
                        print("No start buttons detected for clicking")
                time.sleep(0.5)
                
            time.sleep(0.1)  # Reduce CPU usage
            
    except Exception as e:
        print(f"Error in skill selection: {e}")
    finally:
        # Clean up
        capture.stop_capture()


def click_start_button(window, start_button_bbox, roi_top_left):
    """
    Click the detected start button
    """
    x, y, w, h = start_button_bbox
    
    # Calculate center of button relative to ROI
    button_center_x = x + w // 2
    button_center_y = y + h // 2
    
    # Convert ROI coordinates to absolute screen coordinates
    absolute_x = roi_top_left[0] + button_center_x
    absolute_y = roi_top_left[1] + button_center_y
    
    print(f"Clicking Start button at ({absolute_x}, {absolute_y})")
    
    try:
        # Click the button
        pyautogui.click(absolute_x, absolute_y)
        print("Start button clicked successfully")
    except Exception as e:
        print(f"Error clicking start button: {e}")


def click_start_button_with_noise(window, start_button_bbox, roi_top_left, noise_x, noise_y):
    """
    Click the detected start button with Gaussian noise applied to position
    """
    x, y, w, h = start_button_bbox
    
    # Calculate center of button relative to ROI
    button_center_x = x + w // 2
    button_center_y = y + h // 2
    
    # Apply Gaussian noise to the center position
    noisy_center_x = button_center_x + noise_x
    noisy_center_y = button_center_y + noise_y
    
    # Convert ROI coordinates to absolute screen coordinates
    absolute_x = roi_top_left[0] + noisy_center_x
    absolute_y = roi_top_left[1] + noisy_center_y
    
    print(f"Auto-clicking Start button at ({absolute_x:.1f}, {absolute_y:.1f}) with noise ({noise_x:.1f}, {noise_y:.1f})")
    
    try:
        # Click the button with noise
        pyautogui.click(int(absolute_x), int(absolute_y))
        print("Start button auto-clicked successfully")
    except Exception as e:
        print(f"Error auto-clicking start button: {e}")


def click_random_skill(skill_regions, roi_top_left):
    """
    Click one of the 3 skill regions randomly with Gaussian noise
    """
    print(f"click_random_skill called with regions: {skill_regions}")
    print(f"roi_top_left: {roi_top_left}")
    
    if not skill_regions or len(skill_regions) < 3:
        print(f"Not enough skill regions to click. Regions: {skill_regions}, Count: {len(skill_regions) if skill_regions else 0}")
        return
    
    # Choose random skill (0, 1, or 2)
    random_skill_index = np.random.randint(0, 3)
    selected_region = skill_regions[random_skill_index]
    
    x, y, w, h = selected_region
    
    # Calculate center of skill region
    center_x = x + w // 2
    center_y = y + h // 2
    
    # Add Gaussian noise
    noise_x = np.random.normal(0, 25)
    noise_y = np.random.normal(0, 25)
    
    noisy_x = center_x + noise_x
    noisy_y = center_y + noise_y
    
    # Convert to absolute coordinates
    absolute_x = roi_top_left[0] + noisy_x
    absolute_y = roi_top_left[1] + noisy_y
    
    print(f"Clicking skill {random_skill_index + 1} at ({absolute_x:.1f}, {absolute_y:.1f}) with noise ({noise_x:.1f}, {noise_y:.1f})")
    
    try:
        pyautogui.click(int(absolute_x), int(absolute_y))
        print(f"Skill {random_skill_index + 1} clicked successfully")
    except Exception as e:
        print(f"Error clicking skill: {e}")


def handle_game_state_actions(game_state, current_time, walking_down_start_time):
    """
    Handle continuous actions based on current game state
    Returns updated game state
    """
    if game_state == "WALKING_UP":
        # Press W to walk up
        pyautogui.keyDown('w')
    elif game_state == "WALKING_DOWN":
        # Press S for 2 seconds
        if current_time - walking_down_start_time < np.random.uniform(0.5, 0.7):
            pyautogui.keyDown('s')
        else:
            pyautogui.keyUp('s')
            # Transition to detecting levelups
            game_state = "DETECTING_LEVELUPS"
            print("Game state changed to DETECTING_LEVELUPS")
    elif game_state == "DETECTING_LEVELUPS":
        # Release all movement keys and stay still
        pyautogui.keyUp('w')
        pyautogui.keyUp('s')
    else:
        # Make sure no movement keys are pressed in other states
        pyautogui.keyUp('w')
        pyautogui.keyUp('s')
    
    return game_state


def process_frame_for_skills(frame, positions):
    """
    Process the captured frame to detect skill options in the defined regions
    """
    detected_skills = []
    
    if 'skill_regions' in positions and positions['skill_regions'] is not None:
        for i, (x, y, w, h) in enumerate(positions['skill_regions']):
            # Extract skill region from frame
            # Note: coordinates are absolute, need to convert to frame coordinates if needed
            skill_region = frame[y:y+h, x:x+w] if y >= 0 and x >= 0 and y+h <= frame.shape[0] and x+w <= frame.shape[1] else None
            
            if skill_region is not None and skill_region.size > 0:
                skill_color = analyze_skill_color(skill_region)
                if skill_color != "none":
                    detected_skills.append({
                        'region': i + 1,
                        'color': skill_color,
                        'bbox': (x, y, w, h)
                    })
    
    return detected_skills


def create_skill_regions(skill_area_tl, skill_area_br, roi_top_left):
    """
    Create 3 equal regions from the skill area divided by vertical lines at 1/3 and 2/3 width
    """
    # Convert absolute coordinates to relative coordinates
    area_x = skill_area_tl[0] - roi_top_left[0]
    area_y = skill_area_tl[1] - roi_top_left[1]
    area_w = skill_area_br[0] - skill_area_tl[0]
    area_h = skill_area_br[1] - skill_area_tl[1]
    
    # Calculate precise division points at 1/3 and 2/3
    one_third = area_w / 3.0
    two_thirds = area_w * 2.0 / 3.0
    
    regions = []
    
    # Region 1: 0 to 1/3
    regions.append((area_x, area_y, int(one_third), area_h))
    
    # Region 2: 1/3 to 2/3
    regions.append((area_x + int(one_third), area_y, int(one_third), area_h))
    
    # Region 3: 2/3 to end (captures any remaining pixels)
    region3_start = area_x + int(two_thirds)
    region3_width = area_w - int(two_thirds)
    regions.append((region3_start, area_y, region3_width, area_h))
    
    print(f"Skill area divided: Total width={area_w}, Region widths=[{int(one_third)}, {int(one_third)}, {region3_width}]")
    
    return regions


def analyze_skill_color(skill_region):
    """
    Analyze the skill region to determine its predominant color
    Returns: 'green', 'blue', 'purple', 'gold', or 'none'
    """
    color, _ = analyze_skill_color_with_area(skill_region)
    return color


def analyze_skill_color_with_area(skill_region):
    """
    Analyze the skill region to determine its predominant color and calculate area
    Returns: (color_name, area_in_pixels)
    """
    if skill_region.size == 0:
        return "none", 0
    
    # Convert to HSV for better color analysis
    hsv = cv2.cvtColor(skill_region, cv2.COLOR_BGR2HSV)
    
    height, width = skill_region.shape[:2]
    total_pixels = height * width
    
    # Create masks for each color and count pixels
    # More permissive ranges for better detection
    
    # Green mask: broader range
    green_mask = cv2.inRange(hsv, (35, 40, 40), (85, 255, 255))
    green_area = cv2.countNonZero(green_mask)
    
    # Blue mask: broader range  
    blue_mask = cv2.inRange(hsv, (95, 40, 40), (135, 255, 255))
    blue_area = cv2.countNonZero(blue_mask)
    
    # Purple mask: broader range
    purple_mask = cv2.inRange(hsv, (125, 40, 40), (165, 255, 255))
    purple_area = cv2.countNonZero(purple_mask)
    
    # Gold/Yellow mask: broader range
    gold_mask = cv2.inRange(hsv, (10, 40, 100), (40, 255, 255))
    gold_area = cv2.countNonZero(gold_mask)
    
    # Find the color with the largest area (if any significant area)
    color_areas = {
        "green": green_area,
        "blue": blue_area, 
        "purple": purple_area,
        "gold": gold_area
    }
    
    # Find the color with maximum area
    max_color = max(color_areas.items(), key=lambda x: x[1])
    max_area = max_color[1]
    
    # Require at least 5% of the region to be a color for detection
    threshold = total_pixels * 0.05
    
    if max_area > threshold:
        return max_color[0], max_area
    else:
        return "none", total_pixels


def analyze_energy_level(frame, energy_tl, energy_br):
    """
    Analyze the energy bar area to determine current energy level
    """
    # Extract energy bar region (you'd need to convert coordinates)
    # energy_region = frame[energy_tl[1]:energy_br[1], energy_tl[0]:energy_br[0]]
    
    # Analyze the energy bar (look for specific colors, patterns, etc.)
    # Return energy level percentage or boolean if ready
    
    return True  # Placeholder


def detect_skill_options(frame, skill_positions):
    """
    Detect what skill options are available on screen
    """
    available_skills = []
    
    # For each skill position, analyze the area around it
    for i, skill_pos in enumerate(skill_positions, 1):
        # Extract small region around skill position
        # skill_region = extract_skill_region(frame, skill_pos)
        
        # Analyze if a skill option is present
        # skill_present = is_skill_available(skill_region)
        
        # For now, assume skills are available
        available_skills.append(f"skill{i}")
    
    return available_skills
