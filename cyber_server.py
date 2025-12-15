import socket
import threading
import tkinter as tk
from tkinter import Label, scrolledtext, Toplevel, Listbox, Button
from constants import IP, PORT
from db_manager import DatabaseManager
from create_tables import create_all_tables
from datetime import datetime
from PIL import Image, ImageTk
import os
import pygame
import time
from encrypt import Encryption

class Server:
    def __init__(self):
        # Initialize database connection
        self.db_manager = DatabaseManager("localhost", "root", "Jb240108", "mysql")
        create_all_tables(self.db_manager)
        
        # IMPORTANT: load server private key to decrypt incoming AES keys
        self.encryptor = Encryption(rsa_private_key_path="server_private.pem")
        # Initialize GUI components
        self.root = tk.Tk()
        self.root.withdraw()
        self.log_text = None
        self.client_listbox = None
        self.bg_image = None
        self.client_details_images = {}

    def play_audio(self):
        pygame.mixer.init()
        pygame.mixer.music.load(r"C:\\Users\\jonat\\Desktop\\מדעי המחשב\\סייבר עם מריה\\Jonathan\\intro.mp3")
        pygame.mixer.music.play()
        pygame.mixer.music.queue(r"C:\\Users\\jonat\\Desktop\\מדעי המחשב\\סייבר עם מריה\\Jonathan\\montana skies.mp3")

    def update_gui_log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.config(state=tk.DISABLED)
        self.log_text.yview(tk.END)

    def update_client_list(self):
        if not self.client_listbox:
            return
        self.client_listbox.delete(0, tk.END)
        try:
            clients = self.db_manager.get_rows_with_value("clients", "1", "1")
            for client in clients:
                self.client_listbox.insert(tk.END, client[0])
        except Exception:
            pass

    def show_client_details(self, client_id):
        client_data = self.db_manager.get_rows_with_value("clients", "client_id", client_id)
        if not client_data:
            return
        client = client_data[0]

        details_window = Toplevel()
        details_window.title(f"Client {client_id} Details")
        details_window.geometry("400x350")

        # Create and store image reference in the window itself to prevent garbage collection
        bg_image = ImageTk.PhotoImage(Image.open(r"C:\Users\maria\OneDrive\Dokumenti\סייבר חומרים\Jonathan\logo_cyber.jpeg"))
        bg_label = Label(details_window, image=bg_image)
        bg_label.image = bg_image  # Keep a reference to prevent garbage collection
        bg_label.place(relwidth=1, relheight=1)

        details = [
            f"ID: {client[0]}",
            f"IP: {client[1]}",
            f"Port: {client[2]}",
            f"Last Seen: {client[3]}",
            f"Total Actions: {client[5]}",
            f"Status: {'Existing' if client[5] > 0 else 'New'}"
        ]

        for detail in details:
            lbl = Label(details_window, text=detail, fg='white', bg='black')
            lbl.pack(anchor="w", padx=10, pady=2)

        history_button = Button(details_window, text="History", command=lambda: self.show_client_history(client_id), bg='gray', fg='white')
        history_button.pack(pady=10)

    def show_client_history(self, client_id):
        history_window = Toplevel()
        history_window.title(f"Client {client_id} - History")
        history_window.geometry("600x400")

        # Create and store image reference in the window itself
        bg_image = ImageTk.PhotoImage(Image.open(r"C:\Users\maria\OneDrive\Dokumenti\סייבר חומרים\Jonathan\logo_cyber.jpeg"))
        bg_label = Label(history_window, image=bg_image)
        bg_label.image = bg_image  # Keep a reference to prevent garbage collection
        bg_label.place(relwidth=1, relheight=1)

        history_label = Label(history_window, text=f"Client {client_id} Image History", font=("Arial", 12, "bold"), fg="white", bg="black")
        history_label.pack(pady=5)

        image_listbox = Listbox(history_window, height=15, width=80, bg="black", fg="white", selectbackground="gray")
        image_listbox.pack(padx=10, pady=5, expand=True, fill="both")

        images = self.db_manager.get_rows_with_value("decrypted_media", "user_id", client_id)

        if not images:
            image_listbox.insert(tk.END, "No images found for this client.")
        else:
            image_paths = [img[2] for img in images]
            for path in image_paths:
                image_listbox.insert(tk.END, path)

            def open_selected_image(event):
                selected_index = image_listbox.curselection()
                if selected_index:
                    selected_path = image_paths[selected_index[0]]
                    os.system(f'"{selected_path}"')

            image_listbox.bind("<Double-Button-1>", open_selected_image)

    def handle_client(self, client_socket):
        client_id = 'unknown'
        try:
            # 1) First — receive AES key (encrypted with server RSA). This sets self.encryptor.aes_key
            try:
                self.encryptor.receive_aes_key(client_socket)
            except Exception as e:
                self.update_gui_log(f"Failed to receive AES key from client: {e}")
                client_socket.close()
                return

            # 2) Now receive the next encrypted message (client id or LOGIN|user|pass)
            try:
                incoming = self.encryptor.receive_encrypted_message(client_socket)
            except Exception as e:
                self.update_gui_log(f"Failed to receive encrypted message: {e}")
                client_socket.close()
                return

            if not incoming:
                self.update_gui_log("Received empty message.")
                client_socket.close()
                return

            # Determine message type
            if incoming.startswith("LOGIN|"):
                parts = incoming.split("|", 2)
                if len(parts) == 3:
                    _, username, password = parts
                    client_id = username  # or another mapping you prefer
                    # Here you can validate the user against DB (hash compare, etc.)
                    # For now, simply acknowledge
                    self.encryptor.send_encrypted_message(client_socket, "WELCOME BACK")
                    client_status = "LOGIN_RECEIVED"
                    total_actions = 0
                else:
                    self.encryptor.send_encrypted_message(client_socket, "INVALID_LOGIN_FORMAT")
                    client_socket.close()
                    return
            else:
                # treat message as client_id
                client_id = incoming
                # check DB for client_id (optional)
                existing_client = self.db_manager.get_rows_with_value("clients", "client_id", client_id)
                if existing_client:
                    self.encryptor.send_encrypted_message(client_socket, "WELCOME BACK")
                    client_status = "EXISTING"
                else:
                    # Insert new client (limited info available)
                    try:
                        self.db_manager.insert_row(
                            "clients",
                            "(client_id, client_username, client_password, client_ip, client_port, client_last_active, client_ddos_status)",
                            "(%s, %s, %s, %s, %s, %s, %s)",
                            (client_id, "", "", client_socket.getpeername()[0], client_socket.getpeername()[1], datetime.now(), 0)
                        )
                    except Exception:
                        pass
                    self.encryptor.send_encrypted_message(client_socket, "WELCOME TO MASKER SERVER!")
                    client_status = "NEW"
                    total_actions = 0

            # Log and refresh UI
            self.update_gui_log(f"Client {client_id} connected - Status: {client_status}")
            self.update_client_list()

        finally:
            try:
                client_socket.close()
            except Exception:
                pass
            self.update_client_list()

    def start_server(self):
        server_socket = socket.socket()
        server_socket.bind((IP, PORT))
        server_socket.listen()
        self.update_gui_log("Server started...")
        while True:
            client_socket, _ = server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()

    def create_gui(self):
        self.play_audio()
        
        # Create splash screen
        splash = Toplevel()
        splash.geometry("400x400")
        splash.overrideredirect(True)

        # Load and keep reference to splash image
        logo = Image.open(r"C:\\Users\\jonat\\Desktop\\מדעי המחשב\\סייבר עם מריה\\loading.png").resize((400, 400))
        logo_photo = ImageTk.PhotoImage(logo)
        label = Label(splash, image=logo_photo)
        label.image = logo_photo  # Keep reference
        label.pack()

        splash.update()
        time.sleep(4)
        splash.destroy()

        # Destroy the initial withdrawn root and create a new one
        self.root.destroy()
        self.root = tk.Tk()
        self.root.title("Server GUI")
        self.root.geometry("500x500")

        # Load and keep reference to background image
        self.bg_image = ImageTk.PhotoImage(Image.open(r"C:\\Users\\jonat\\Desktop\\מדעי המחשב\\סייבר עם מריה\\background.webp"))
        bg_label = Label(self.root, image=self.bg_image)
        bg_label.place(relwidth=1, relheight=1)

        # Create scrolled text for logs
        self.log_text = scrolledtext.ScrolledText(self.root, state=tk.DISABLED, wrap=tk.WORD, height=10, bg='black', fg='white')
        self.log_text.pack(expand=True, fill='both', padx=10, pady=5)

        # Create clients label
        Label(self.root, text="MASKER Customers", font=("Arial", 14, "bold"), fg="white", bg="black").pack(pady=5)

        # Create client listbox
        self.client_listbox = Listbox(self.root, bg='black', fg='white')
        self.client_listbox.pack(expand=True, fill='both', padx=10, pady=5)
        self.client_listbox.bind("<Double-Button-1>", lambda event: self.show_client_details(self.client_listbox.get(self.client_listbox.curselection())))

        # Start server in a separate thread
        threading.Thread(target=self.start_server, daemon=True).start()
        self.root.mainloop()

if __name__ == "__main__":
    server = Server()
    server.create_gui()
