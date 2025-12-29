import socket
import os
import time
import threading
import customtkinter as ctk 
from constants import IP, PORT
from encrypt import Encryption

# --- הגדרות עיצוב ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class ClientNetworking:
    def __init__(self):
        self.sock = None
        self.encryptor = Encryption(rsa_public_key_path="server_public.pem")

    def connect(self):
        try:
            self.sock = socket.socket()
            self.sock.connect((IP, PORT))
            self.encryptor.send_aes_key(self.sock)
            return True
        except Exception as e:
            print(f"Connection Failed: {e}")
            return False

    def send_auth(self, command, username, password):
        if not self.sock: return "ERROR: No Connection"
        try:
            msg = f"{command}|{username}|{password}"
            self.encryptor.send_encrypted_message(self.sock, msg)
            response = self.encryptor.receive_encrypted_message(self.sock)
            return response
        except Exception as e:
            return f"ERROR: {e}"

    def close(self):
        if self.sock:
            self.sock.close()

class AuthGUI(ctk.CTk):
    def __init__(self, networking_instance):
        super().__init__()
        self.title("MUSICER | ACCESS TERMINAL")
        self.geometry("400x500")
        self.resizable(False, False)
        
        self.client_net = networking_instance
        
        # --- UI Layout ---
        self.lbl_title = ctk.CTkLabel(self, text="MUSICER", font=("Orbitron", 30, "bold"), text_color="#1DB954")
        self.lbl_title.pack(pady=(40, 10))
        
        self.auth_mode = ctk.StringVar(value="LOGIN")
        self.seg_ctrl = ctk.CTkSegmentedButton(self, values=["LOGIN", "SIGN UP"], 
                                               command=self.on_mode_change,
                                               variable=self.auth_mode)
        self.seg_ctrl.pack(pady=10)

        self.entry_user = ctk.CTkEntry(self, placeholder_text="Username", width=250)
        self.entry_user.pack(pady=10)
        
        self.entry_pass = ctk.CTkEntry(self, placeholder_text="Password", width=250, show="*")
        self.entry_pass.pack(pady=10)

        self.btn_action = ctk.CTkButton(self, text="AUTHENTICATE", command=self.run_auth_process)
        self.btn_action.pack(pady=30)

        self.lbl_status = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.lbl_status.pack(pady=10)

    def on_mode_change(self, value):
        self.btn_action.configure(text="AUTHENTICATE" if value == "LOGIN" else "CREATE ID")

    def run_auth_process(self):
        user = self.entry_user.get()
        pwd = self.entry_pass.get()
        mode = self.auth_mode.get().replace(" ", "")
        
        threading.Thread(target=self._thread_auth, args=(mode, user, pwd)).start()

    def _thread_auth(self, mode, user, pwd):
        if not self.client_net.connect():
            self.lbl_status.configure(text="Error: Server unreachable", text_color="red")
            return

        response = self.client_net.send_auth(mode, user, pwd)
        
        if "SUCCESS" in response:
            print(f"LOGGED IN AS {user}")
            self.destroy() # סגירת החלון ויציאה מה-mainloop
        else:
            self.client_net.close()
            self.lbl_status.configure(text=f"Failed: {response}", text_color="red")

def main_application_loop(net_obj):
    """כאן נכנסת הלוגיקה של הלקוח לאחר שהתחבר בהצלחה"""
    print("\n--- ENTERING MAIN SYSTEM ---")
    # כאן תוכל לפתוח את החלון הראשי של הלקוח או להריץ פקודות
    while True:
        # לדוגמה: בדיקת חיבור כל 5 שניות
        time.sleep(5)
        print("Client is active and connected...")

if __name__ == "__main__":
    net = ClientNetworking()
    logged_in = False

    # 1. בדיקת LOGIN אוטומטי
    if os.path.exists("info.txt"):
        print("[AUTO] info.txt detected. Attempting bypass...")
        try:
            with open("info.txt", "r") as f:
                lines = f.read().splitlines()
                if len(lines) >= 2:
                    u, p = lines[0], lines[1]
                    if net.connect():
                        resp = net.send_auth("LOGIN", u, p)
                        if "SUCCESS" in resp:
                            print(f"[AUTO] Success! Welcome {u}")
                            logged_in = True
                        else:
                            print(f"[AUTO] Login failed: {resp}")
                            net.close()
        except Exception as e:
            print(f"[AUTO] Error: {e}")

    # 2. אם לא הצליח אוטומטית - פתח ממשק גרפי
    if not logged_in:
        print("[UI] Starting Login Window...")
        app = AuthGUI(net)
        app.mainloop()
        # אם המשתמש סגר את החלון בלי להתחבר, נבדוק אם הסוקט פתוח
        if net.sock:
            logged_in = True

    # 3. מעבר ללוגיקה המרכזית (רק אם מחובר)
    if logged_in:
        main_application_loop(net)
    else:
        print("Application closed without login.")