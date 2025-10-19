# -*- coding: utf-8 -*-
import random
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from ciphers import scytale, cardan_grille

class CipherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Исторические шифры")
        self.geometry("800x600")
        self._create_widgets()
        self._create_context_menu()
    def _create_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Копировать", command=lambda: self.focus_get().event_generate('<<Copy>>'))
        self.context_menu.add_command(label="Вставить", command=lambda: self.focus_get().event_generate('<<Paste>>'))
        self.context_menu.add_command(label="Вырезать", command=lambda: self.focus_get().event_generate('<<Cut>>'))
        self.input_text.bind("<Button-3>", self._show_context_menu)
        self.output_text.bind("<Button-3>", self._show_context_menu)
    def _show_context_menu(self, event):
        self.context_menu.tk_popup(event.x_root, event.y_root)
    def _create_widgets(self):
        self.selected_cipher = tk.StringVar(value="scytale")
        control_frame = ttk.LabelFrame(self, text="Управление", padding="10")
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Radiobutton(control_frame, text="Скитала", variable=self.selected_cipher, value="scytale", command=self._update_ui).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(control_frame, text="Решётка Кардано", variable=self.selected_cipher, value="cardan", command=self._update_ui).pack(side=tk.LEFT, padx=5)
        input_frame = ttk.LabelFrame(self, text="Исходный текст", padding="10")
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.input_text = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, height=10)
        self.input_text.pack(fill=tk.BOTH, expand=True)
        action_frame = ttk.Frame(self, padding="10"); action_frame.pack(fill=tk.X, padx=10)
        ttk.Button(action_frame, text="Шифровать", command=self._process_encrypt).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Дешифровать", command=self._process_decrypt).pack(side=tk.LEFT, padx=5)
        self.key_label = ttk.Label(action_frame, text="Ключ (число):"); self.key_entry = ttk.Entry(action_frame, width=10)
        self.cardan_key_label = ttk.Label(action_frame, text="Ключ (слово):"); self.cardan_key_entry = ttk.Entry(action_frame, width=15)
        self.grille_size_label = ttk.Label(action_frame, text="Размер:"); self.grille_size_var = tk.IntVar(value=6)
        self.grille_size_spinbox = ttk.Spinbox(action_frame, from_=4, to=20, increment=2, width=5, textvariable=self.grille_size_var)
        self._update_ui()
        output_frame = ttk.LabelFrame(self, text="Результат", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, height=10, state="disabled")
        self.output_text.pack(fill=tk.BOTH, expand=True)
    def _update_ui(self):
        is_scytale = self.selected_cipher.get() == "scytale"
        widgets_scytale = [self.key_label, self.key_entry]
        widgets_cardan = [self.cardan_key_label, self.cardan_key_entry, self.grille_size_label, self.grille_size_spinbox]
        for w in (widgets_cardan if is_scytale else widgets_scytale): w.pack_forget()
        for w in (widgets_scytale if is_scytale else widgets_cardan): w.pack(side=tk.LEFT, padx=5)
    def _display_result(self, text):
        self.output_text.config(state="normal"); self.output_text.delete("1.0", tk.END); self.output_text.insert("1.0", text); self.output_text.config(state="disabled")
    def _process_encrypt(self):
        # ИСПРАВЛЕНИЕ: Заменяем .strip() на .rstrip('\n')
        text = self.input_text.get("1.0", tk.END).rstrip('\n')
        if not text: messagebox.showerror("Ошибка", "Исходный текст пуст."); return
        try:
            if self.selected_cipher.get() == "scytale":
                key = int(self.key_entry.get())
                result = scytale.encrypt(text, key)
            else:
                key_phrase = self.cardan_key_entry.get()
                if not key_phrase: messagebox.showerror("Ошибка", "Введите ключевое слово."); return
                random.seed(key_phrase)
                size = self.grille_size_var.get()
                grille = cardan_grille.generate_grille(size)
                padded = text.ljust(size*size, '_')[:size*size]
                result = cardan_grille.encrypt(padded, grille)
            self._display_result(result)
        except Exception as e: messagebox.showerror("Ошибка ввода", str(e))
    def _process_decrypt(self):
        # ИСПРАВЛЕНИЕ: Заменяем .strip() на .rstrip('\n')
        text = self.input_text.get("1.0", tk.END).rstrip('\n')
        if not text: messagebox.showerror("Ошибка", "Исходный текст пуст."); return
        try:
            if self.selected_cipher.get() == "scytale":
                key = int(self.key_entry.get())
                result = scytale.decrypt(text, key)
            else:
                key_phrase = self.cardan_key_entry.get()
                if not key_phrase: messagebox.showerror("Ошибка", "Введите ключ."); return
                random.seed(key_phrase)
                size = self.grille_size_var.get()
                grille = cardan_grille.generate_grille(size)
                if len(text) != size*size: messagebox.showerror("Ошибка", f"Длина текста ({len(text)}) должна быть {size*size}."); return
                result = cardan_grille.decrypt(text, grille).rstrip('_')
            self._display_result(result)
        except Exception as e: messagebox.showerror("Ошибка ввода", str(e))

def start_ui():
    app = CipherApp(); app.mainloop()