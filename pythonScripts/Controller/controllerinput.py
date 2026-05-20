import pygame
import threading
from pynput import keyboard

# State variables
button0 = False
button1 = False
button2 = False
button3 = False
button4 = False
button5 = False
button6 = False
button7 = False
button8 = False
button9 = False
button10 = False
button11 = False
buttonQ = False

axis0 = 0.0  # X-axis (Roll)
axis1 = 0.0  # Y-axis (Pitch)
axis2 = 0.0  # Z-axis (Twist/Rudder)
axis3 = 0.0  # Throttle (Slider)

hat0 = (0, 0)

keyQ = False
keyR = False

joystick = None
running = False
_thread_started = False

def init_joystick():
    """Initialize joystick and start input thread. Safe to call multiple times."""
    global joystick, running, _thread_started
    
    pygame.init()
    pygame.joystick.init()
    
    if pygame.joystick.get_count() == 0:
        print("No joysticks found. Please connect your Logitech Extreme 3D Pro.")
        return False
    
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Connected to: {joystick.get_name()}")
    
    running = True
    
    # Only start threads once
    if not _thread_started:
        _thread_started = True
        thread = threading.Thread(target=_input_loop, daemon=True)
        thread.start()
        
        # Start keyboard listener
        listener = keyboard.Listener(on_press=_on_press, on_release=_on_release)
        listener.start()
    
    return True

def _on_press(key):
    """Handle keyboard press"""
    global keyQ, keyR
    try:
        if key.char == 'q' or key.char == 'Q':
            keyQ = True
        elif key.char == 'r' or key.char == 'R':
            keyR = True
    except AttributeError:
        pass

def _on_release(key):
    """Handle keyboard release"""
    global keyQ, keyR
    try:
        if key.char == 'q' or key.char == 'Q':
            keyQ = False
        elif key.char == 'r' or key.char == 'R':
            keyR = False
    except AttributeError:
        pass

def _input_loop():
    """Internal loop to update button/axis states"""
    global button0, button1, button2, button3, button4, button5, button6, button7
    global button8, button9, button10, button11, buttonQ
    global axis0, axis1, axis2, axis3, hat0, running
    
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            # Update axes
            if joystick:
                axis0 = joystick.get_axis(0)
                axis1 = joystick.get_axis(1)
                axis2 = joystick.get_axis(2)
                axis3 = joystick.get_axis(3)
                
                # Update buttons (12 buttons for Logitech Extreme 3D Pro)
                button0 = bool(joystick.get_button(0))
                button1 = bool(joystick.get_button(1))
                button2 = bool(joystick.get_button(2))
                button3 = bool(joystick.get_button(3))
                button4 = bool(joystick.get_button(4))
                button5 = bool(joystick.get_button(5))
                button6 = bool(joystick.get_button(6))
                button7 = bool(joystick.get_button(7))
                button8 = bool(joystick.get_button(8))
                button9 = bool(joystick.get_button(9))
                button10 = bool(joystick.get_button(10))
                button11 = bool(joystick.get_button(11))                
                # Update hat
                hat0 = joystick.get_hat(0)
            
            pygame.time.wait(50)
    
    except KeyboardInterrupt:
        pass
    finally:
        running = False
        pygame.quit()

def shutdown():
    """Stop the joystick input thread"""
    global running
    running = False