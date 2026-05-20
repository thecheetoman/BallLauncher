import controllerinput
import comsToRock
import sys
import time

# Initialize
controllerinput.init_joystick()
print("Joystick initialized, connect to tuffCar. PSWD: superfastcar")


# Track previous button states
prev_button0 = False
prev_button1 = False
mEnable = False
try:
    while True:
        # Only send on state change
        if controllerinput.button1 != prev_button1:
            if controllerinput.button1:
                mEnable = True
                comsToRock.send_command("MEnable")
            else:
                mEnable = False
                comsToRock.send_command("MDisable")
            prev_button1 = controllerinput.button1
        
        if controllerinput.button0 != prev_button0:
            if controllerinput.button0:
                if mEnable == True:
                    comsToRock.send_command("MHigh")
                else:
                    print("Motor disabled, try enabling it before doing stuff")
            else:
                comsToRock.send_command("MLow")
            prev_button0 = controllerinput.button0
        if controllerinput.keyR:
            print("Reconnecting")
            comsToRock.check_connection()
            time.sleep(1)
            comsToRock.send_command("C_ON")
        if controllerinput.keyQ:
            comsToRock.send_command("C_OFF")
            print("Shutting Down")
            controllerinput.shutdown()
            sys.exit()

except KeyboardInterrupt:
    print("\nExiting...")
    controllerinput.shutdown()