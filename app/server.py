import sys
import socket
import threading
import numpy as np
import cv2
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap

# Server to view client's screen
class ScreenServer(QWidget):
    def __init__(self, host='0.0.0.0', port=9999):
        super().__init__()
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        print(f"[*] Listening on {self.host}:{self.port}")
        
        self.init_ui()
        self.show()

        self.accept_thread = threading.Thread(target=self.accept_connections)
        self.accept_thread.start()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.label = QLabel()
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        self.setWindowTitle("Client Screen Viewer")

    def accept_connections(self):
        while True:
            conn, addr = self.sock.accept()
            print(f"[+] Connection established with {addr}")
            self.receive_screen_thread = threading.Thread(target=self.receive_screen, args=(conn,))
            self.receive_screen_thread.start()

    def receive_screen(self, conn):
        while True:
            # Receive the length of the image
            img_len = int.from_bytes(conn.recv(4), 'big')
            img_data = b''

            # Receive the image
            while len(img_data) < img_len:
                img_data += conn.recv(img_len - len(img_data))

            # Decode image
            img_array = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Convert to QImage and display
            qimg = QImage(img, img.shape[1], img.shape[0], img.shape[1] * 3, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            self.label.setPixmap(pixmap)

if __name__ == '__main__':
    # Start Qt app for server
    app = QApplication(sys.argv)
    server = ScreenServer()
    sys.exit(app.exec_())
