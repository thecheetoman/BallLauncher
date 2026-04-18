#!/usr/bin/env python3
"""
Xbox 360 Controller Scanner and Value Dumper for Windows
Uses the 'inputs' library for reliable controller input
"""

import sys
import time

try:
    import inputs
except ImportError:
    print("Error: inputs library is not installed.")
    print("Install it with: pip install inputs")
    sys.exit(1)


def print_xbox360_mapping():
    """Print standard Xbox 360 controller mapping"""
    print("\n=== Standard Xbox 360 Controller Mapping ===")
    print("\nButtons:")
    print("  BTN_A       = A button")
    print("  BTN_B       = B button")
    print("  BTN_X       = X button")
    print("  BTN_Y       = Y button")
    print("  BTN_LB      = LB (Left Bumper)")
    print("  BTN_RB      = RB (Right Bumper)")
    print("  BTN_BACK    = Back button")
    print("  BTN_START   = Start button")
    print("  BTN_THUMBL  = Left Stick Click")
    print("  BTN_THUMBR  = Right Stick Click")
    
    print("\nAxes:")
    print("  ABS_X       = Left Stick X (-32768 left, 32767 right)")
    print("  ABS_Y       = Left Stick Y (-32768 up, 32767 down)")
    print("  ABS_Z       = Left Trigger (0 to 255)")
    print("  ABS_RX      = Right Stick X (-32768 left, 32767 right)")
    print("  ABS_RY      = Right Stick Y (-32768 up, 32767 down)")
    print("  ABS_RZ      = Right Trigger (0 to 255)")
    
    print("\nD-Pad:")
    print("  ABS_HAT0X   = D-Pad X (-1 left, 0 neutral, 1 right)")
    print("  ABS_HAT0Y   = D-Pad Y (-1 down, 0 neutral, 1 up)")
    print()


def scan_controllers():
    """Scan for connected Xbox 360 controllers"""
    try:
        devices = inputs.get_gamepad()
        if devices:
            print("\nController(s) detected and ready!")
            return True
        else:
            print("No controllers detected.")
            return False
    except Exception as e:
        print(f"Error scanning controllers: {e}")
        return False


def dump_controller_values():
    """
    Continuously dump Xbox 360 controller values
    """
    print("\n=== Reading Controller Input ===")
    print("Press Ctrl+C to stop\n")
    
    # Store previous values to avoid redundant output
    last_values = {}
    
    try:
        while True:
            try:
                # Get the next event with a timeout
                events = inputs.get_gamepad()
                
                if events:
                    for event in events:
                        # Build event string
                        event_str = f"{event.ev_type}: {event.state:7} ({event.code})"
                        
                        # Only print if value changed
                        if event.code not in last_values or last_values[event.code] != event.state:
                            print(event_str)
                            last_values[event.code] = event.state
                else:
                    # No events, check if we should print idle status occasionally
                    pass
                    
            except inputs.UnpluggedError:
                print("\nController unplugged!")
                break
            except inputs.TimeoutError:
                # No input this iteration, that's normal
                pass
            except Exception as e:
                print(f"Error reading input: {e}")
                break
                
    except KeyboardInterrupt:
        print("\n\nStopped.")


def dump_controller_values_continuous():
    """
    Alternative mode: continuously dump all controller values (polling)
    """
    print("\n=== Reading Controller Input (Continuous Mode) ===")
    print("Press Ctrl+C to stop\n")
    
    # Initialize state tracking
    controller_state = {
        'buttons': {},
        'axes': {}
    }
    
    try:
        while True:
            try:
                # Get all current events
                events = inputs.get_gamepad()
                
                for event in events:
                    if event.ev_type == 'Key':
                        controller_state['buttons'][event.code] = event.state
                    elif event.ev_type == 'Absolute':
                        controller_state['axes'][event.code] = event.state
                    
                    # Print each event
                    print(f"{event.ev_type:10} | {event.code:15} = {event.state:7}")
                
            except inputs.UnpluggedError:
                print("\nController unplugged!")
                break
            except inputs.TimeoutError:
                # No input received, that's okay
                time.sleep(0.001)
            except Exception as e:
                print(f"Error: {e}")
                break
                
    except KeyboardInterrupt:
        print("\n\nStopped.")


def main():
    """Main function"""
    print("Xbox 360 Controller Scanner for Windows")
    print("=" * 50)
    print("\nScanning for controllers...")
    
    if not scan_controllers():
        print("\nNo Xbox 360 controllers found.")
        print("Please connect a controller and try again.")
        sys.exit(0)
    
    print_xbox360_mapping()
    
    # Choose mode
    print("Select mode:")
    print("1. Event-based (shows only changes)")
    print("2. Continuous polling (shows all inputs)")
    
    while True:
        try:
            choice = input("\nEnter 1 or 2: ").strip()
            if choice == '1':
                dump_controller_values()
                break
            elif choice == '2':
                dump_controller_values_continuous()
                break
            else:
                print("Invalid choice. Please enter 1 or 2.")
        except ValueError:
            print("Invalid input.")


if __name__ == "__main__":
    main()