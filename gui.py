import customtkinter as ctk
from tkinter import Listbox
from datetime import datetime
import os
import random

ctk.set_appearance_mode("dark")

class ServerGUI:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.root = ctk.CTk()
        self.root.title("MUSICER | Advanced Audio Control")
        self.root.geometry("1100x700")
        
        self.font_name = "Orbitron" if os.path.exists("Orbitron-Bold.ttf") else "Arial"

        # ניהול גבהים - הפעם נוריד את קצב השינוי
        self.current_heights = [20] * 10
        self.target_heights = [20] * 10

        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self.root, width=220, corner_radius=0, fg_color="#0a0a0a")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo = ctk.CTkLabel(self.sidebar, text="MUSICER", font=(self.font_name, 32, "bold"), text_color="#1DB954")
        self.logo.pack(pady=(30, 5))
        
        self.status_tag = ctk.CTkLabel(self.sidebar, text="● SYSTEM ACTIVE", text_color="#1DB954", font=("Consolas", 12))
        self.status_tag.pack(pady=(0, 20))

        # --- Visualizer Area ---
        # הגדרנו גובה קבוע ל-Container כדי למנוע קפיצות של שאר האלמנטים
        self.viz_container = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=120)
        self.viz_container.pack(pady=20, padx=10, fill="x")
        self.viz_container.pack_propagate(False) # מונע מה-Frame להתכווץ לפי התוכן

        self.bars = []
        for i in range(10):
            # יצירת "עמוד" לכל בר כדי שהבסיס שלו יהיה מקובע לתחתית
            bar = ctk.CTkFrame(self.viz_container, width=12, height=20, fg_color="#1DB954", corner_radius=1)
            # anchor="s" מצמיד את העמודה לדרום (תחתית)
            bar.pack(side="left", padx=3, anchor="s") 
            self.bars.append(bar)

        self.mute_btn = ctk.CTkButton(self.sidebar, text="MUTE / UNMUTE", fg_color="#1f1f1f", hover_color="#333", 
                                      command=self.on_mute_click)
        self.mute_btn.pack(pady=10, padx=20)

        # --- Main Content ---
        self.main_view = ctk.CTkFrame(self.root, corner_radius=15, fg_color="transparent")
        self.main_view.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.log_box = ctk.CTkTextbox(self.main_view, corner_radius=10, border_width=1, border_color="#1DB954", 
                                      font=("Consolas", 13), fg_color="#000", text_color="#00ff00")
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_box.configure(state="disabled")

        self.client_frame = ctk.CTkFrame(self.main_view, fg_color="#0a0a0a", border_width=1, border_color="#333")
        self.client_frame.pack(fill="x", padx=10, pady=10)
        
        self.client_list = Listbox(self.client_frame, bg="#0a0a0a", fg="#1DB954", borderwidth=0, 
                                   highlightthickness=0, font=("Consolas", 12), selectbackground="#1DB954", selectforeground="black")
        self.client_list.pack(fill="both", expand=True, padx=10, pady=10)

        self.toggle_audio_callback = None

    def on_mute_click(self):
        if self.toggle_audio_callback:
            self.toggle_audio_callback()

    def update_visualizer(self):
        """אנימציה איטית, חלקה וירוקה בלבד"""
        for i, bar in enumerate(self.bars):
            # בחירת יעד חדש בתדירות נמוכה יותר
            if abs(self.current_heights[i] - self.target_heights[i]) < 2:
                self.target_heights[i] = random.randint(10, 80)

            # תנועה איטית יותר (שינוי של 1-2 פיקסלים בכל פעם במקום 4)
            if self.current_heights[i] < self.target_heights[i]:
                self.current_heights[i] += 1 
            else:
                self.current_heights[i] -= 1

            # עדכון הגובה בלבד (הצבע נשאר ירוק)
            bar.configure(height=self.current_heights[i])

        # הגדלנו את זמן ההמתנה ל-40ms כדי שהתנועה תהיה רגועה יותר
        self.root.after(40, self.update_visualizer)

    def log(self, message):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{ts}] MUSICER > {message}\n")
        self.log_box.configure(state="disabled")
        self.log_box.see("end")

    def refresh_clients(self):
        self.client_list.delete(0, 'end')
        try:
            clients = self.db_manager.get_rows_with_value("clients", "1", "1")
            for c in clients:
                self.client_list.insert('end', f" TARGET: {c[0]} | IP: {c[1]}")
        except: pass

    def start(self):
        self.update_visualizer()
        self.root.mainloop()