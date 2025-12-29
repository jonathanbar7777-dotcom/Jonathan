import socket
import threading
import pygame
import os
from gui import ServerGUI
from constants import IP, PORT
from db_manager import DatabaseManager
from encrypt import Encryption
from datetime import datetime
from create_tables import create_all_tables

class ModernServer:
    def __init__(self):
        # 1. Database & Encryption
        self.db_manager = DatabaseManager("localhost", "root", "Jb240108", "mysql")
        create_all_tables(self.db_manager)
        self.encryptor = Encryption(rsa_private_key_path="server_private.pem")
        
        # 2. UI Setup
        self.gui = ServerGUI(self.db_manager)
        self.gui.toggle_audio_callback = self.toggle_music
        
        # 3. Audio Setup
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.mixer.init()
        self.muted = False
        self.play_background_music()

    def play_background_music(self):
        base_path = os.path.dirname(__file__)
        music_path = os.path.join(base_path, "background.mp3")
        if os.path.exists(music_path):
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.3)
                pygame.mixer.music.play(-1)
                self.gui.log("Audio Engine: Playing background.mp3")
            except Exception as e:
                self.gui.log(f"Audio Error: {e}")
        else:
            self.gui.log("Warning: background.mp3 not found.")

    def toggle_music(self):
        if self.muted:
            pygame.mixer.music.unpause()
            self.gui.log("System Audio: RESTORED")
        else:
            pygame.mixer.music.pause()
            self.gui.log("System Audio: MUTED")
        self.muted = not self.muted

    def handle_client(self, conn, addr):
        try:
            self.gui.log(f"New connection from {addr[0]}")
            
            # 1. Key Exchange
            self.encryptor.receive_aes_key(conn)
            
            # 2. Receive Auth Request (LOGIN|user|pass or SIGNUP|user|pass)
            encrypted_msg = self.encryptor.receive_encrypted_message(conn)
            if not encrypted_msg:
                return

            parts = encrypted_msg.split("|")
            if len(parts) != 3:
                self.encryptor.send_encrypted_message(conn, "ERROR: Invalid protocol format")
                return

            command, username, password = parts[0], parts[1], parts[2]

            if command == "SIGNUP":
                # Check if user already exists
                # הנחה: העמודה היא client_username בטבלה clients
                existing = self.db_manager.get_rows_with_value("clients", "client_username", username)
                
                if existing:
                    self.encryptor.send_encrypted_message(conn, "ERROR: Username taken")
                    self.gui.log(f"Signup failed: {username} exists.")
                else:
                    # יצירת משתמש חדש
                    # שים לב: עליך לוודא שהעמודות ב-INSERT תואמות לטבלה שלך ב-DB
                    # כאן אני מכניס נתונים בסיסיים
                    self.db_manager.insert_row(
                        "clients",
                        # שמות העמודות (בלי client_id כי הוא אוטומטי)
                        "(client_username, client_password, client_ip, client_port, client_last_active, client_ddos_status)",
                        # הערכים
                        "(%s, %s, %s, %s, %s, %s)",
                        # הנתונים בפועל (הוספנו 0 בסוף עבור ddos_status)
                        (username, password, addr[0], addr[1], datetime.now(), 0)
                    )
                    self.encryptor.send_encrypted_message(conn, "SUCCESS: Account created")
                    self.gui.log(f"New User Registered: {username}")
                    self.gui.refresh_clients()

            elif command == "LOGIN":
                # שליפת המשתמש
                user_rows = self.db_manager.get_rows_with_value("clients", "client_username", username)
                
                if user_rows:
                    # בהנחה שהסיסמה היא בשדה השלישי (אינדקס 2) או שצריך לבדוק לפי שם העמודה
                    # כאן נניח שחזר שורה והסיסמה נכונה (במציאות תבדוק אינדקס מדויק)
                    db_pass = user_rows[0][2] # <--- וודא שזה האינדקס הנכון של הסיסמה בטבלה שלך!
                    
                    if db_pass == password:
                        self.encryptor.send_encrypted_message(conn, "SUCCESS: Logged in")
                        self.gui.log(f"User Logged In: {username}")
                        
                        # עדכון זמן פעילות אחרון (אופציונלי)
                        # self.db_manager.update_row(...) 
                        self.gui.refresh_clients()
                    else:
                        self.encryptor.send_encrypted_message(conn, "ERROR: Wrong password")
                        self.gui.log(f"Failed Login (Pass): {username}")
                else:
                    self.encryptor.send_encrypted_message(conn, "ERROR: User not found")
                    self.gui.log(f"Failed Login (User): {username}")

        except Exception as e:
            self.gui.log(f"Auth Error: {e}")
        # הערה: אנחנו לא סוגרים את החיבור מיד אם ההתחברות הצליחה, 
        # אבל לצורך הדוגמה הנוכחית החיבור נסגר בסוף הבלוק. 
        # במערכת מלאה, אם SUCCESS, היינו נכנסים ללולאת תקשורת ראשית.
        finally:
            conn.close()

    def listen_loop(self):
        s = socket.socket()
        s.bind((IP, PORT))
        s.listen(100)
        self.gui.log(f"Server Listening on {IP}:{PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

    def start(self):
        threading.Thread(target=self.listen_loop, daemon=True).start()
        self.gui.log("MUSICER SERVER STARTING...")
        self.gui.refresh_clients()
        self.gui.start()

if __name__ == "__main__":
    app = ModernServer()
    app.start()