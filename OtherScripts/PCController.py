#!/usr/bin/env python3
"""
Xbox 360 Controller to RC Car Bridge
Reads Xbox controller and sends commands to ROCK 4C+ over Wi-Fi
"""

import sys
import time
import requests

try:
    import inputs
except ImportError:
    print("Error: inputs library is not installed.")
    print("Install it with: pip install inputs")
    sys.exit(1)

# ROCK 4C+ server configuration
ROCK_IP = "192.168.4.1"
ROCK_PORT = 8000
ROCK_URL = f"http://{ROCK_IP}:{ROCK_PORT}"

# Right trigger threshold (when to consider it "pressed")
RZ_THRESHOLD = 50  # Values 0-255, 50 is ~20% pressed

# Track trigger state
rz_is_pressed = False

def send_command(command):
    """Send command to ROCK 4C+ server"""
    try:
        response = requests.post(
            ROCK_URL,
            json={'command': command},
            timeout=0.5
        )
        
        if response.status_code == 200:
            print(f"✓ Sent: {command}")
            return True
        else:
            print(f"✗ Failed to send {command}: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"✗ Timeout sending {command}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"✗ Cannot connect to ROCK at {ROCK_URL}")
        print("   Make sure you're connected to RC_CAR_WIFI")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def check_connection():
    """Check if ROCK server is reachable"""
    try:
        response = requests.get(ROCK_URL, timeout=2)
        if response.status_code == 200:
            print(f"✓ Connected to RC Car server at {ROCK_URL}")
            return True
    except:
        pass
    
    print(f"✗ Cannot reach RC Car server at {ROCK_URL}")
    print("   Make sure:")
    print("   1. You're connected to RC_CAR_WIFI")
    print("   2. ROCK server is running (python3 rc_server.py)")
    return False

def scan_controllers():
    """Scan for connected Xbox 360 controllers"""
    try:
        devices = inputs.devices.gamepads
        if devices:
            print(f"✓ Found {len(devices)} controller(s)")
            return True
        else:
            print("✗ No controllers detected")
            return False
    except Exception as e:
        print(f"Error scanning controllers: {e}")
        return False

def run_controller():
    """Main controller loop - read input and send to ROCK"""
    global rz_is_pressed
    
    print("\n" + "="*60)
    print("RC Car Controller Active")
    print("="*60)
    print("Right Trigger (RZ) controls motor:")
    print("  Press   → MHigh")
    print("  Release → MLow")
    print("\nPress Ctrl+C to stop")
    print("="*60 + "\n")
    
    last_rz_value = 0
    
    try:
        while True:
            try:
                events = inputs.get_gamepad()
                
                for event in events:
                    # Only process RZ (Right Trigger) events
                    if event.code == 'ABS_RZ':
                        rz_value = event.state
                        
                        # Print value for debugging
                        if abs(rz_value - last_rz_value) > 10:  # Only print significant changes
                            print(f"RZ value: {rz_value}")
                            last_rz_value = rz_value
                        
                        # Check if trigger crossed threshold
                        if rz_value >= RZ_THRESHOLD and not rz_is_pressed:
                            # Trigger pressed
                            rz_is_pressed = True
                            send_command("MHigh")
                        
                        elif rz_value < RZ_THRESHOLD and rz_is_pressed:
                            # Trigger released
                            rz_is_pressed = False
                            send_command("MLow")
                
            except inputs.UnpluggedError:
                print("\n✗ Controller unplugged!")
                break
            except inputs.TimeoutError:
                # No input this cycle, that's normal
                time.sleep(0.001)
                
    except KeyboardInterrupt:
        print("\n\nStopping...")
        # Make sure motor is off when exiting
        if rz_is_pressed:
            send_command("MLow")

def main():
    """Main function"""
    print("Xbox 360 Controller → RC Car Bridge")
    print("="*60)
    
    # Check for controller
    print("\nScanning for controllers...")
    if not scan_controllers():
        print("\nPlease connect an Xbox 360 controller and try again.")
        sys.exit(1)
    
    # Check connection to ROCK
    print("\nChecking connection to ROCK 4C+...")
    if not check_connection():
        print("\nPlease check your connection and try again.")
        sys.exit(1)
    
    # Run the controller
    run_controller()

if __name__ == "__main__":
    main()