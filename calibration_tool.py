import pyautogui
import keyboard
import json
import time

def runCalibration():
    positions = {}

    print("Calibration tool")
    print("Move mouse and press SPACE to save position")
    print("Press ESC to finish\n")

    possiblePos = ["top-left", "bottom-right", "start-tl", "start-br", "skill-area-tl", "skill-area-br", "carousel-tl", "carousel-br"]
    index = 0

    space_was_down = False


    print("Starting calibration...")
    print("     1. Top Left of Game Area")
    print("     2. Bottom Right of Game Area")
    print("     3. Start Area Top Left")
    print("     4. Start Area Bottom Right")
    print("     5. Skill Area Top Left")
    print("     6. Skill Area Bottom Right")
    print("     7. Carousel Top Left")
    print("     8. Carousel Bottom Right")

    while True:
        # ESC quits immediately
        if keyboard.is_pressed("esc"):
            print("\nESC pressed — finishing calibration")
            break

        # Detect SPACE press (edge detection)
        space_down = keyboard.is_pressed("space")
        if space_down and not space_was_down:
            try:
                x, y = pyautogui.position()
                positions[possiblePos[index]] = [x, y]
                print(f"Saved {possiblePos[index]}: x={x}, y={y}")
                index += 1
                if len(positions) == len(possiblePos):
                    print("\nAll positions calibrated.")
                    print("     Press ESC to finish calibration.")
                    print("     Press space to restart the calibration process.")
            except IndexError:
                print("⚠️ Surpassed expected positions — restarting calibration")
                positions.clear()
                index = 0

        space_was_down = space_down
        time.sleep(0.05)  # prevents CPU burn

    if len(positions) < len(possiblePos):
        print("Calibration incomplete. Exiting without saving.")
        exit()

    with open("positions.json", "w", encoding="utf-8") as f:
        json.dump(positions, f, indent=4)

    print("Calibration saved to positions.json")
