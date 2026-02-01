from time import sleep
import os
from calibration_tool import runCalibration
import yaml
from skillSelection import skillSelection
import threading
import keyboard
import time

def optionsMenu():
    print("Starting skill selection menu...")
    print("Press 1 - to callibrate positions")
    print("Press 2 - to run auto skill detection")

    choice = input("Enter your choice: ")
    return choice



if __name__ == "__main__":
    stop_flag = {'stop': False}
    user_choice = optionsMenu()
    if user_choice == '1':
        print("You selected callibration.\n")
        runCalibration()
    elif user_choice == '2':
        if not os.path.exists('C:\\Users\\dylan\\Archero2\\FarmingMacro\\positions.json'):
            print("You must run calibration first before auto skill detection.")
            print("Running callibration")
            runCalibration()
        positions = yaml.safe_load(open("C:\\Users\\dylan\\Archero2\\FarmingMacro\\positions.json"))

        t = threading.Thread(target=skillSelection, args=(positions, stop_flag))
        t.start()

        print("Press 'q' to stop skill selection.")

        while True:
            if keyboard.is_pressed('q'):
                print("Stopping skill selection...")
                stop_flag['stop'] = True
                break
            time.sleep(0.1)

        t.join()
        print("Skill selection stopped.")

    else:
        print("Invalid choice. Exiting.")
