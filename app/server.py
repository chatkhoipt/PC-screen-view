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

        # Thread to handle new connections
        self.accept_thread = threading.Thread(target=self.accept_connections)
        self.accept_thread.daemon = True
        self.accept_thread.start()

    # Initialize UI layout
    def init_ui(self):
        self.layout = QVBoxLayout()
        self.label = QLabel()
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        self.setWindowTitle("Client Screen Viewer")

    # Accept connections from clients
    def accept_connections(self):
        while True:
            conn, addr = self.sock.accept()
            print(f"[+] Connection established with {addr}")
            # Create a thread for each client connection
            receive_thread = threading.Thread(target=self.receive_screen, args=(conn,))
            receive_thread.daemon = True
            receive_thread.start()

    # Receive and display the screen from the client
    def receive_screen(self, conn):
        try:
            while True:
                # Receive the length of the image
                img_len_bytes = conn.recv(4)
                if not img_len_bytes:
                    break  # Client has closed the connection

                img_len = int.from_bytes(img_len_bytes, 'big')
                img_data = b''

                # Receive the image data
                while len(img_data) < img_len:
                    packet = conn.recv(img_len - len(img_data))
                    if not packet:
                        break  # Connection closed by the client
                    img_data += packet

                if not img_data:
                    break  # No image data, client has disconnected

                # Decode image and convert to displayable format
                img_array = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                # Convert to QImage and display on QLabel
                qimg = QImage(img, img.shape[1], img.shape[0], img.shape[1] * 3, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimg)
                self.label.setPixmap(pixmap)

        except (ConnectionResetError, BrokenPipeError):
            pass  # Gracefully handle client disconnection
        finally:
            print(f"[-] Client disconnected, clearing screen data...")
            self.clear_screen()  # Clear the QLabel when client disconnects
            conn.close()

    # Clear the QLabel (reset the screen display)
    def clear_screen(self):
        self.label.clear()  # Clear the QLabel content

if __name__ == '__main__':
    # Start Qt application for server
    app = QApplication(sys.argv)
    server = ScreenServer()
    sys.exit(app.exec_())
