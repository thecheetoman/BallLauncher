#!/usr/bin/env python3
"""
Simple script - Send C_ON to Arduino
"""

import serial
import time

# Try common Arduino ports
PORTS = ['/dev/ttyUSB0', '/dev/ttyACM0', '/dev/ttyUSB1', '/dev/ttyACM1']

def send_c_on():
    """Find Arduino and send C_ON command"""
    
    # Try each port
    for port in PORTS:
        try:
            print(f"Trying {port}...")
            ser = serial.Serial(port, 9600, timeout=1)
            print(f"✓ Connected to {port}")
            
            # Wait for Arduino to reset
            time.sleep(2)
            
            # Send C_ON
            print("Sending C_ON...")
            ser.write(b'C_ON\n')
            
            # Close connection
            ser.close()
            print("✓ Done!")
            return True
            
        except Exception as e:
            print(f"  Failed: {e}")
            continue
    
    print("✗ Could not find Arduino on any port")
    return False

if __name__ == '__main__':
    send_c_on()