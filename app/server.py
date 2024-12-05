import sys
import socket
import threading
import tkinter as tk
from tkinter import ttk
import numpy as np
import cv2

class ClientScreenController:
    """Class for managing individual client controls using Tkinter."""
    def __init__(self, conn, address, root, disconnect_callback):
        self.conn = conn
        self.address = address
        self.root = root
        self.disconnect_callback = disconnect_callback
        self.message_box_active = False

        # Create a frame for this client in the main window
        self.frame = ttk.Frame(root)
        self.frame.pack(fill="x", padx=5, pady=5)

        # Add controls
        ttk.Label(self.frame, text=f"Client: {self.address}").pack(side="left")
        self.toggle_button = ttk.Button(
            self.frame, text="Toggle Message Boxes", command=self.toggle_message_boxes
        )
        self.toggle_button.pack(side="right")

        # Start screen receiver thread
        self.receive_thread = threading.Thread(target=self.receive_screen)
        self.receive_thread.daemon = True
        self.receive_thread.start()

    def toggle_message_boxes(self):
        """Send a command to toggle message boxes on the client."""
        self.message_box_active = not self.message_box_active
        command = b"START_MESSAGE" if self.message_box_active else b"STOP_MESSAGE"
        try:
            self.conn.send(command)
        except Exception as e:
            print(f"[!] Error sending command to {self.address}: {e}")

    def receive_screen(self):
        """Receives the screen data and displays it dynamically resizable using OpenCV."""
        try:
            window_name = f"Client Screen - {self.address}"

            while True:
                # Check if the window needs to be recreated
                if not cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) >= 1:
                    # Recreate the resizable window
                    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                    cv2.resizeWindow(window_name, 640, 480)  # Reset to default size

                img_len_bytes = self.conn.recv(4)
                if not img_len_bytes:
                    break

                img_len = int.from_bytes(img_len_bytes, 'big')
                img_data = b""

                while len(img_data) < img_len:
                    packet = self.conn.recv(img_len - len(img_data))
                    if not packet:
                        break
                    img_data += packet

                if not img_data:
                    break

                # Decode the image
                img_array = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                if img is not None:
                    # Display the image
                    cv2.imshow(window_name, img)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print(f"[-] Closed screen for {self.address}")
                        break

        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
            print(f"[!] Connection lost with {self.address}.")
        finally:
            self.disconnect_callback(self.conn)
            cv2.destroyWindow(window_name)

    def stop(self):
        """Stops the screen and cleans up resources."""
        cv2.destroyWindow(f"Client Screen - {self.address}")
        self.conn.close()
        self.frame.destroy()


class ServerController:
    """Main server controller to manage clients."""
    def __init__(self, root, host="0.0.0.0", port=9999, max_clients=10):
        self.root = root
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen(max_clients)
        print(f"[*] Listening on {self.host}:{self.port}")

        # Dictionary to keep track of connected clients
        self.client_controllers = {}

        # Start a thread to accept new connections
        self.accept_thread = threading.Thread(target=self.accept_connections)
        self.accept_thread.daemon = True
        self.accept_thread.start()

    def accept_connections(self):
        """Accepts new client connections."""
        while True:
            if len(self.client_controllers) < self.max_clients:
                try:
                    conn, addr = self.sock.accept()
                    print(f"[+] Connection established with {addr}")

                    # Create a new client controller
                    controller = ClientScreenController(
                        conn, addr, self.root, self.remove_client
                    )
                    self.client_controllers[conn] = controller
                except Exception as e:
                    print(f"[!] Error accepting connection: {e}")

    def remove_client(self, conn):
        """Removes a client when it disconnects."""
        if conn in self.client_controllers:
            self.client_controllers[conn].stop()
            del self.client_controllers[conn]
            print(f"[-] Client disconnected and removed.")

    def stop_server(self):
        """Stops the server and cleans up all resources."""
        print("[*] Stopping server...")
        for conn in list(self.client_controllers.keys()):
            self.remove_client(conn)
        self.sock.close()
        print("[*] Server stopped.")

class ServerController:
    """Main server controller to manage clients."""
    def __init__(self, root, host="0.0.0.0", port=9999, max_clients=10):
        self.root = root
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen(max_clients)
        print(f"[*] Listening on {self.host}:{self.port}")

        # Dictionary to keep track of connected clients
        self.client_controllers = {}

        # Start a thread to accept new connections
        self.accept_thread = threading.Thread(target=self.accept_connections)
        self.accept_thread.daemon = True
        self.accept_thread.start()

    def accept_connections(self):
        """Accepts new client connections."""
        while True:
            if len(self.client_controllers) < self.max_clients:
                try:
                    conn, addr = self.sock.accept()
                    print(f"[+] Connection established with {addr}")

                    # Create a new client controller
                    controller = ClientScreenController(
                        conn, addr, self.root, self.remove_client
                    )
                    self.client_controllers[conn] = controller
                except Exception as e:
                    print(f"[!] Error accepting connection: {e}")

    def remove_client(self, conn):
        """Removes a client when it disconnects."""
        if conn in self.client_controllers:
            self.client_controllers[conn].stop()
            del self.client_controllers[conn]
            print(f"[-] Client disconnected and removed.")

    def stop_server(self):
        """Stops the server and cleans up all resources."""
        print("[*] Stopping server...")
        for conn in list(self.client_controllers.keys()):
            self.remove_client(conn)
        self.sock.close()
        print("[*] Server stopped.")


if __name__ == "__main__":
    try:
        # Create Tkinter main window
        root = tk.Tk()
        root.title("Server Controller")

        # Start the server
        server = ServerController(root)

        # Run Tkinter main loop
        root.protocol("WM_DELETE_WINDOW", lambda: (server.stop_server(), root.destroy()))
        root.mainloop()
    except KeyboardInterrupt:
        print("\n[*] Shutting down server...")
        server.stop_server()
        sys.exit(0)
