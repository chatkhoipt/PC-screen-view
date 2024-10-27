import base64
import socket
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO
import cv2
import numpy as np

app = Flask(__name__)
socketio = SocketIO(app)

# Global variable to hold the most recent screen frame
latest_frame = None

# Route to serve the HTML page
@app.route('/')
def index():
    return render_template('index.html')

# WebSocket connection handler for sending frames to the web client
@socketio.on('connect')
def handle_connect():
    print("[+] Web client connected")
    def send_frame():
        global latest_frame
        while True:
            if latest_frame is not None:
                # Emit frame to the connected client
                socketio.emit('frame', latest_frame)
            socketio.sleep(0.033)  # Send frames at roughly 30 fps

    threading.Thread(target=send_frame).start()

# Server to receive screen data from client
def start_server(host='0.0.0.0', port=9999):
    global latest_frame
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    sock.listen(5)
    print(f"[*] Listening on {host}:{port}")

    while True:
        conn, addr = sock.accept()
        print(f"[+] Connection established with {addr}")
        threading.Thread(target=receive_screen, args=(conn,)).start()

def receive_screen(conn):
    global latest_frame
    while True:
        # Receive the length of the image
        img_len_bytes = conn.recv(4)
        if not img_len_bytes:
            break

        img_len = int.from_bytes(img_len_bytes, 'big')
        img_data = b''

        # Receive image data
        while len(img_data) < img_len:
            packet = conn.recv(img_len - len(img_data))
            if not packet:
                break
            img_data += packet

        # Decode image and convert to base64
        if img_data:
            img_array = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 50])
            latest_frame = base64.b64encode(buffer).decode('utf-8')

        else:
            break

    conn.close()

if __name__ == '__main__':
    # Start the Flask app in a separate thread
    threading.Thread(target=socketio.run, args=(app,), kwargs={'host': '0.0.0.0', 'port': 5000}).start()
    # Start the screen receiver server
    start_server()
