import controllerinput
import sys
import time

# Initialize
controllerinput.init_joystick()
print("Joystick initialized. Press inputs to see values...\n")

try:
    while True:
        # Buttons
        buttons = [
            controllerinput.button0, controllerinput.button1, controllerinput.button2,
            controllerinput.button3, controllerinput.button4, controllerinput.button5,
            controllerinput.button6, controllerinput.button7, controllerinput.button8,
            controllerinput.button9, controllerinput.button10
        ]
        
        # Axes
        axes = [
            controllerinput.axis0, controllerinput.axis1,
            controllerinput.axis2, controllerinput.axis3
        ]
        if controllerinput.keyQ:
            print("Shutting Down")
            controllerinput.shutdown()
            sys.exit()
        

except KeyboardInterrupt:
    print("\nExiting...")
    controllerinput.shutdown()