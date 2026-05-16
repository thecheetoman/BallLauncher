import sys
import time
import requests

# ROCK 4C+ server configuration
ROCK_IP = "192.168.4.1"
ROCK_PORT = 8000
ROCK_URL = f"http://{ROCK_IP}:{ROCK_PORT}"

def send_command(command):
    #send command to the rock4's server
    try:
        response = requests.post(
            ROCK_URL,
            json={'command': command},
            timeout=0.5
        )
        
        if response.status_code == 200:
            print(f"Sent: {command}")
            return True
        else:
            print(f"Failed to send {command}: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"Timeout sending {command}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"Cannot connect to ROCK at {ROCK_URL}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    
def check_connection():
    #check if server responjds
    try:
        response = requests.get(ROCK_URL, timeout=2)
        if response.status_code == 200:
            print(f"✓ Connected to RC Car server at {ROCK_URL}")
            return True
    except:
        pass
    
    print(f"Cannot reach RC Car server at {ROCK_URL}")
    print("   Make sure:")
    print("   1. You're connected to its hotspot")
    print("   2. ROCK server is running (python3 rc_server.py)")
    return False
