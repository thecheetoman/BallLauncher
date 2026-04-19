#!/usr/bin/env python3
"""
ROCK 4C+ RC Car Server
Receives commands via HTTP and sends to Arduino via serial
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import serial
import time
import json
import threading

# Arduino connection settings
ARDUINO_PORTS = ['/dev/ttyUSB0', '/dev/ttyACM0', '/dev/ttyUSB1', '/dev/ttyACM1']
BAUD_RATE = 9600

# Global Arduino connection
arduino = None
arduino_lock = threading.Lock()

def connect_arduino():
    """Find and connect to Arduino"""
    global arduino
    
    for port in ARDUINO_PORTS:
        try:
            print(f"Trying to connect to Arduino on {port}...")
            arduino = serial.Serial(port, BAUD_RATE, timeout=1)
            time.sleep(2)  # Wait for Arduino reset
            
            # Read startup message
            while arduino.in_waiting > 0:
                msg = arduino.readline().decode().strip()
                print(f"Arduino: {msg}")
            
            print(f"✓ Connected to Arduino on {port}")
            return True
        except Exception as e:
            continue
    
    print("✗ Could not connect to Arduino")
    return False

def send_to_arduino(command):
    """Send command to Arduino"""
    global arduino
    
    if not arduino or not arduino.is_open:
        print(f"✗ Arduino not connected, cannot send: {command}")
        return False
    
    try:
        with arduino_lock:
            print(f"→ Sending to Arduino: {command}")
            arduino.write(f"{command}\n".encode())
            time.sleep(0.05)
            
            # Read response if available
            if arduino.in_waiting > 0:
                response = arduino.readline().decode().strip()
                print(f"← Arduino: {response}")
        
        return True
    except Exception as e:
        print(f"✗ Error sending to Arduino: {e}")
        return False

class RCCarHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            'status': 'online',
            'message': 'RC Car Server Running',
            'arduino_connected': arduino is not None and arduino.is_open
        }
        
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        """Handle POST requests with commands"""
        content_length = int(self.headers.get('Content-Length', 0))
        
        if content_length > 0:
            body = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(body)
                command = data.get('command', '')
                
                if command:
                    print(f"Received command from PC: {command}")
                    success = send_to_arduino(command)
                    
                    self.send_response(200 if success else 500)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    response = {
                        'status': 'success' if success else 'error',
                        'command': command,
                        'sent_to_arduino': success
                    }
                    
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self.send_error(400, "No command provided")
            
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
        else:
            self.send_error(400, "Empty request body")
    
    def log_message(self, format, *args):
        """Customize logging to be less verbose"""
        pass

def main():
    HOST = '0.0.0.0'
    PORT = 8000
    
    print("=" * 60)
    print("RC Car Server for ROCK 4C+")
    print("=" * 60)
    
    # Connect to Arduino
    if not connect_arduino():
        print("\n⚠️  WARNING: Arduino not connected!")
        print("Server will start but commands won't work until Arduino is connected.")
        print("Plug in Arduino and restart this script.\n")
    
    # Start HTTP server
    server = HTTPServer((HOST, PORT), RCCarHandler)
    
    print(f"\n✓ Server running on {HOST}:{PORT}")
    print(f"PC should connect to: http://192.168.4.1:{PORT}")
    print("Press Ctrl+C to stop\n")
    print("=" * 60)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        if arduino and arduino.is_open:
            arduino.close()
        server.shutdown()
        print("Server stopped")

if __name__ == '__main__':
    main()