import socket
import os
import random
from PIL import Image
from constants import IP, PORT, CHUNK_SIZE
from encrypt import Encryption

# -------------------------
# Client (core, non-GUI)
# -------------------------
class Client:
    def __init__(self):
        self.client_socket = None
        # IMPORTANT: load server public key so we can encrypt the AES key
        self.encryptor = Encryption(rsa_public_key_path="public.pem")

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket()
            self.client_socket.connect((IP, PORT))
            print("Connected to server")

            # Send AES key (encrypted with server's RSA public key)
            self.encryptor.send_aes_key(self.client_socket)

        except Exception as e:
            print(f"Error connecting to server: {e}")
            self.client_socket = None

    def send_client_id(self):
        client_id = str(random.randint(1, 6))
        print("The client id ", client_id)
        try:
            self.encryptor.send_encrypted_message(self.client_socket, client_id)
            server_response = self.encryptor.receive_encrypted_message(self.client_socket)
            print("Server response:", server_response)
        except Exception as e:
            print("Send/receive failed:", e)

    def run(self):
        self.connect_to_server()
        if not self.client_socket:
            return

        self.send_client_id()

        self.client_socket.close()

# -------------------------------
# Tkinter Login GUI Integration
# -------------------------------
import tkinter as tk
from tkinter import ttk, messagebox

class LoginGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Login")
        self.geometry("360x220")
        self.resizable(False, False)
        self.configure(padx=16, pady=16)

        self.style = ttk.Style(self)
        try:
            self.style.theme_use('clam')
        except Exception:
            pass

        self._create_widgets()
        self.client = None

    def _create_widgets(self):
        header = ttk.Label(self, text="Sign in", font=("Segoe UI", 16, "bold"))
        header.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0,10))

        ttk.Label(self, text="Username:").grid(row=1, column=0, sticky="w")
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(self, textvariable=self.username_var, width=30)
        self.username_entry.grid(row=1, column=1, columnspan=2, sticky="w", pady=4)
        self.username_entry.focus()

        ttk.Label(self, text="Password:").grid(row=2, column=0, sticky="w")
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(self, textvariable=self.password_var, width=30, show="*")
        self.password_entry.grid(row=2, column=1, sticky="w", pady=4)

        self.show_var = tk.BooleanVar(value=False)
        show_cb = ttk.Checkbutton(self, text="Show", variable=self.show_var, command=self._toggle_password)
        show_cb.grid(row=2, column=2, sticky="w")

        self.login_btn = ttk.Button(self, text="Login", command=self._on_login)
        self.login_btn.grid(row=4, column=1, sticky="e", pady=(12,0), padx=(0,8))

        self.quit_btn = ttk.Button(self, text="Quit", command=self.destroy)
        self.quit_btn.grid(row=4, column=2, sticky="w", pady=(12,0))

        self.note_label = ttk.Label(self, text="(integrated with cyber_client)", font=("Segoe UI", 8), foreground="gray")
        self.note_label.grid(row=5, column=0, columnspan=3, sticky="w", pady=(12,0))

        self.bind("<Return>", lambda event: self._on_login())

    def _toggle_password(self):
        self.password_entry.config(show="" if self.show_var.get() else "*")

    def _validate(self, username: str, password: str) -> bool:
        if not username.strip():
            messagebox.showwarning("Validation", "Username cannot be empty.")
            return False
        if not password:
            messagebox.showwarning("Validation", "Password cannot be empty.")
            return False
        return True

    def _on_login(self):
        username = self.username_var.get()
        password = self.password_var.get()

        if not self._validate(username, password):
            return

        self.login_btn.config(state="disabled")
        self.update_idletasks()

        try:
            # יצירת Client חדש
            self.client = Client()
            self.client.connect_to_server()

            sock = getattr(self.client, "client_socket", None)
            enc = getattr(self.client, "encryptor", None)

            if not sock or not enc:
                messagebox.showerror("Connection", "Failed to connect to server or encryption setup.")
                return

            # -------------------------
            # שליחת הודעת LOGIN מוצפנת
            # -------------------------
            login_msg = f"LOGIN|{username}|{password}"
            try:
                enc.send_encrypted_message(sock, login_msg)
                # המתן לתגובה מהשרת
                server_response = enc.receive_encrypted_message(sock)
                messagebox.showinfo("Server response", server_response)
            except Exception as e:
                messagebox.showerror("Encryption Error", f"Failed to send or receive encrypted message: {e}")

        finally:
            self.login_btn.config(state="normal")
            if sock:
                sock.close()


# -------------------------
# Auto-login / CLI flow
# -------------------------
if __name__ == "__main__":
    if os.path.exists("info.txt"):
        # Auto-login mode
        try:
            with open("info.txt", "r", encoding="utf-8") as f:
                lines = f.read().strip().splitlines()
                if len(lines) >= 2:
                    username, password = lines[0], lines[1]
                else:
                    print("info.txt must have username on first line and password on second line.")
                    exit(1)

            client = Client()
            client.connect_to_server()

            if not getattr(client, "client_socket", None):
                print("Failed to connect to server.")
                exit(1)

            enc = getattr(client, "encryptor", None)
            sock = getattr(client, "client_socket", None)

            if enc and sock:
                msg = f"LOGIN|{username}|{password}"
                enc.send_encrypted_message(sock, msg)
                try:
                    resp = enc.receive_encrypted_message(sock)
                except Exception:
                    resp = "<no response>"
                print("Server response:", resp)
            else:
                payload = f"LOGIN|{username}|{password}".encode("utf-8")
                sock.sendall(payload)
                print("Credentials sent (raw). Server may not understand format.")

        except Exception as e:
            print("Auto-login failed:", e)

    else:
        # Normal GUI mode
        app = LoginGUI()
        app.mainloop()


