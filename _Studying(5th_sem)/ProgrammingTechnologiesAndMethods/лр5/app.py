"""
Главный модуль приложения для шифрования историческими алгоритмами.
Содержит всю логику графического интерфейса и является точкой входа.
"""

import math
import random
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog

import ciphers


# Класс для окна с анимацией шифра Скитала
class ScytaleAnimationWindow(tk.Toplevel):
    """Дочернее окно для визуализации процесса шифрования Скиталы."""

    def __init__(self, master, text, key, colors):
        super().__init__(master)
        self.title("Анимация шифра Скитала")
        self.transient(master)
        self.resizable(False, False)
        self.configure(bg=colors["bg"])

        self.ANIMATION_DELAY = 150
        self.HIGHLIGHT_COLOR = colors["highlight"]
        self.DEFAULT_COLOR = colors["widget_bg"]

        self.rows = key
        self.cols = math.ceil(len(text) / key)
        self.padded_text = text.ljust(self.rows * self.cols)

        self.labels = []
        self.result_text = tk.StringVar()

        style = ttk.Style(self)
        style.configure("TLabel", background=colors["bg"], foreground=colors["fg"])
        style.configure(
            "Anim.TLabel", background=self.DEFAULT_COLOR, foreground=colors["fg"]
        )

        grid_frame = ttk.Frame(self, padding=10)
        grid_frame.pack()
        for r in range(self.rows):
            row_labels = []
            for c in range(self.cols):
                label = ttk.Label(
                    grid_frame,
                    text=" ",
                    font=("Consolas", 14),
                    borderwidth=1,
                    relief="solid",
                    padding=5,
                    width=2,
                    anchor="center",
                    style="Anim.TLabel",
                )
                label.grid(row=r, column=c, padx=1, pady=1)
                row_labels.append(label)
            self.labels.append(row_labels)

        ttk.Label(self, textvariable=self.result_text, font=("Consolas", 12)).pack(
            pady=10
        )
        self.after(500, self.start_animation)

    def start_animation(self):
        self.current_pos = -1
        self.result_chars = []
        self._animate_write_step()

    def _animate_write_step(self):
        """Рекурсивный вызов с задержкой для пошаговой анимации записи."""
        if self.current_pos >= 0:
            prev_r, prev_c = divmod(self.current_pos, self.cols)
            self.labels[prev_r][prev_c].config(background=self.DEFAULT_COLOR)
        self.current_pos += 1
        if self.current_pos >= len(self.padded_text):
            self.current_pos = -1
            self.after(1000, self._animate_read_step)
            return
        r, c = divmod(self.current_pos, self.cols)
        self.labels[r][c].config(
            text=self.padded_text[self.current_pos], background=self.HIGHLIGHT_COLOR
        )
        self.after(self.ANIMATION_DELAY, self._animate_write_step)

    def _animate_read_step(self):
        """Рекурсивный вызов с задержкой для пошаговой анимации чтения."""
        if self.current_pos >= 0:
            prev_c, prev_r = divmod(self.current_pos, self.rows)
            self.labels[prev_r][prev_c].config(background=self.DEFAULT_COLOR)
        self.current_pos += 1
        if self.current_pos >= self.rows * self.cols:
            self.result_text.set(self.result_text.get() + " -> Готово!")
            return
        c, r = divmod(self.current_pos, self.rows)
        char = self.labels[r][c].cget("text")
        self.result_chars.append(char)
        self.result_text.set("".join(self.result_chars))
        self.labels[r][c].config(background=self.HIGHLIGHT_COLOR)
        self.after(self.ANIMATION_DELAY, self._animate_read_step)


class CipherApp(tk.Tk):
    """Основной класс приложения с графическим интерфейсом."""

    def __init__(self):
        super().__init__()

        # --- Настройка темной темы вручную ---
        self.COLORS = {
            "bg": "#2E2E2E",
            "fg": "#EAEAEA",
            "widget_bg": "#3C3C3C",
            "highlight": "#5A7A9A",
            "entry_bg": "#4A4A4A",
        }
        self.configure(bg=self.COLORS["bg"])
        self.setup_styles()

        self.title("Исторические шифры (Скитала, Решётка Кардано)")
        self.geometry("800x650")
        self._create_widgets()
        self._create_context_menu()
        self._create_menu_bar()

    def setup_styles(self):
        """Настраивает стиль ttk виджетов для темной темы."""
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            ".",
            background=self.COLORS["bg"],
            foreground=self.COLORS["fg"],
            fieldbackground=self.COLORS["widget_bg"],
            borderwidth=1,
        )

        style.configure(
            "TLabel", background=self.COLORS["bg"], foreground=self.COLORS["fg"]
        )
        style.configure(
            "TButton", background=self.COLORS["widget_bg"], foreground=self.COLORS["fg"]
        )
        style.map("TButton", background=[("active", self.COLORS["highlight"])])
        style.configure(
            "TRadiobutton", background=self.COLORS["bg"], foreground=self.COLORS["fg"]
        )
        style.map("TRadiobutton", background=[("active", self.COLORS["highlight"])])
        style.configure(
            "TEntry",
            fieldbackground=self.COLORS["entry_bg"],
            foreground=self.COLORS["fg"],
            insertcolor=self.COLORS["fg"],
        )
        style.configure(
            "TSpinbox",
            fieldbackground=self.COLORS["entry_bg"],
            foreground=self.COLORS["fg"],
        )
        style.configure(
            "TLabelframe", background=self.COLORS["bg"], bordercolor=self.COLORS["fg"]
        )
        style.configure(
            "TLabelframe.Label",
            background=self.COLORS["bg"],
            foreground=self.COLORS["fg"],
        )

        self.option_add("*TearOff", False)
        self.option_add("*Text*background", self.COLORS["widget_bg"])
        self.option_add("*Text*foreground", self.COLORS["fg"])
        self.option_add("*Text*insertBackground", self.COLORS["fg"])
        self.option_add("*Text*selectBackground", self.COLORS["highlight"])

    def _create_menu_bar(self):
        """Создает и настраивает верхнее меню приложения."""
        main_menu = tk.Menu(
            self, bg=self.COLORS["widget_bg"], fg=self.COLORS["fg"], bd=0
        )
        self.config(menu=main_menu)

        file_menu = tk.Menu(
            main_menu, tearoff=0, bg=self.COLORS["widget_bg"], fg=self.COLORS["fg"]
        )
        file_menu.add_command(
            label="Открыть текст из файла...", command=self._open_file
        )
        file_menu.add_command(
            label="Сохранить результат в файл...", command=self._save_file
        )
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.destroy)
        main_menu.add_cascade(label="Файл", menu=file_menu)

        examples_menu = tk.Menu(
            main_menu, tearoff=0, bg=self.COLORS["widget_bg"], fg=self.COLORS["fg"]
        )
        examples_menu.add_command(
            label="Пример для Скиталы", command=self._load_scytale_example
        )
        examples_menu.add_command(
            label="Пример для Решётки Кардано", command=self._load_cardan_example
        )
        main_menu.add_cascade(label="Примеры", menu=examples_menu)

        help_menu = tk.Menu(
            main_menu, tearoff=0, bg=self.COLORS["widget_bg"], fg=self.COLORS["fg"]
        )
        help_menu.add_command(label="О шифре Скитала", command=self._show_scytale_help)
        help_menu.add_command(label="О Решётке Кардано", command=self._show_cardan_help)
        main_menu.add_cascade(label="Справка", menu=help_menu)

    def _create_context_menu(self):
        # Привязываем меню к виджету в фокусе в момент клика.
        self.context_menu = tk.Menu(
            self, tearoff=0, bg=self.COLORS["widget_bg"], fg=self.COLORS["fg"]
        )
        self.context_menu.add_command(
            label="Копировать",
            command=lambda: self.focus_get().event_generate("<<Copy>>"),
        )
        self.context_menu.add_command(
            label="Вставить",
            command=lambda: self.focus_get().event_generate("<<Paste>>"),
        )
        self.context_menu.add_command(
            label="Вырезать", command=lambda: self.focus_get().event_generate("<<Cut>>")
        )

    def _show_context_menu(self, event):
        widget = self.focus_get()
        if isinstance(widget, (tk.Text, scrolledtext.ScrolledText, ttk.Entry)):
            widget.bind(
                "<Button-3>", self.context_menu.tk_popup(event.x_root, event.y_root)
            )

    def _create_widgets(self):
        self.selected_cipher = tk.StringVar(value="scytale")
        control_frame = ttk.LabelFrame(self, text="Управление", padding="10")
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Radiobutton(
            control_frame,
            text="Скитала",
            variable=self.selected_cipher,
            value="scytale",
            command=self._update_ui,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            control_frame,
            text="Решётка Кардано",
            variable=self.selected_cipher,
            value="cardan",
            command=self._update_ui,
        ).pack(side=tk.LEFT, padx=5)

        input_frame = ttk.LabelFrame(self, text="Исходный текст", padding="10")
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.input_text = scrolledtext.ScrolledText(
            input_frame, wrap=tk.WORD, height=10
        )
        self.input_text.pack(fill=tk.BOTH, expand=True)
        self.input_text.bind("<Button-3>", self._show_context_menu)

        action_frame = ttk.Frame(self, padding="10")
        action_frame.pack(fill=tk.X, padx=10)
        ttk.Button(action_frame, text="Шифровать", command=self._process_encrypt).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(
            action_frame, text="Дешифровать", command=self._process_decrypt
        ).pack(side=tk.LEFT, padx=5)
        self.visualize_button = ttk.Button(
            action_frame, text="Визуализировать", command=self._visualize_scytale
        )
        self.visualize_button.pack(side=tk.LEFT, padx=5)
        ttk.Separator(action_frame, orient="vertical").pack(
            side=tk.LEFT, padx=10, fill="y"
        )
        ttk.Button(action_frame, text="Очистить всё", command=self._clear_all).pack(
            side=tk.LEFT, padx=5
        )

        key_frame = ttk.Frame(self, padding="10")
        key_frame.pack(fill=tk.X, padx=10)
        self.key_label = ttk.Label(key_frame, text="Ключ (число):")
        self.key_entry = ttk.Entry(key_frame, width=10)
        self.cardan_key_label = ttk.Label(key_frame, text="Ключ (слово):")
        self.cardan_key_entry = ttk.Entry(key_frame, width=15)
        self.grille_size_label = ttk.Label(key_frame, text="Размер:")
        self.grille_size_var = tk.IntVar(value=6)
        self.grille_size_spinbox = ttk.Spinbox(
            key_frame,
            from_=4,
            to=20,
            increment=2,
            width=5,
            textvariable=self.grille_size_var,
        )
        self._update_ui()

        output_frame = ttk.LabelFrame(self, text="Результат", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.output_text = scrolledtext.ScrolledText(
            output_frame, wrap=tk.WORD, height=10, state="disabled"
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_text.bind("<Button-3>", self._show_context_menu)

    def _update_ui(self):
        is_scytale = self.selected_cipher.get() == "scytale"
        if is_scytale:
            self.visualize_button.pack(side=tk.LEFT, padx=5)
        else:
            self.visualize_button.pack_forget()
        widgets_scytale = [self.key_label, self.key_entry]
        widgets_cardan = [
            self.cardan_key_label,
            self.cardan_key_entry,
            self.grille_size_label,
            self.grille_size_spinbox,
        ]
        for w in widgets_cardan if is_scytale else widgets_scytale:
            w.pack_forget()
        for w in widgets_scytale if is_scytale else widgets_cardan:
            w.pack(side=tk.LEFT, padx=5)

    def _clear_all(self):
        self.input_text.delete("1.0", tk.END)
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state="disabled")

    def _display_result(self, text):
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", text)
        self.output_text.config(state="disabled")

    def _load_scytale_example(self):
        self.selected_cipher.set("scytale")
        self._update_ui()
        self._clear_all()
        self.input_text.insert("1.0", "ЭТО ШИФР ДРЕВНЕЙ СПАРТЫ")
        self.key_entry.delete(0, tk.END)
        self.key_entry.insert(0, "4")

    def _load_cardan_example(self):
        self.selected_cipher.set("cardan")
        self._update_ui()
        self._clear_all()
        self.input_text.insert("1.0", "Это простой текст для демонстрации")
        self.cardan_key_entry.delete(0, tk.END)
        self.cardan_key_entry.insert(0, "secret")
        self.grille_size_var.set(6)

    def _show_scytale_help(self):
        messagebox.showinfo(
            "Шифр Скитала (Scytale)",
            "Принцип: Текст записывается на ленту, намотанную на цилиндр. Затем лента разматывается.\n\nКлюч: Диаметр цилиндра (целое число).\n\nКриптостойкость: Крайне низка.",
        )

    def _show_cardan_help(self):
        messagebox.showinfo(
            "Решётка Кардано (Cardan Grille)",
            "Принцип: Текст вписывается через вырезы в решётке, которая поворачивается 4 раза. Решётка генерируется на основе ключевого слова.\n\nКлюч: Ключевое слово и размер решётки.\n\nОграничения: Текст дополняется символом '_' до размера N*N.",
        )

    def _open_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("All files", "*.*")]
        )
        if not filepath:
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert("1.0", f.read())
        except Exception as e:
            messagebox.showerror("Ошибка чтения файла", str(e))

    def _save_file(self):
        content = self.output_text.get("1.0", tk.END).rstrip("\n")
        if not content:
            messagebox.showwarning("Предупреждение", "Поле результата пусто.")
            return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All files", "*.*")],
        )
        if not filepath:
            return
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            messagebox.showerror("Ошибка сохранения файла", str(e))

    def _show_grille_visualization(self, grille):
        vis_window = tk.Toplevel(self)
        vis_window.title("Сгенерированная решётка Кардано")
        vis_window.transient(self)
        vis_window.resizable(False, False)
        vis_window.configure(bg=self.COLORS["bg"])

        grille_str = "\n".join(
            " ".join(["■" if cell else "□" for cell in row]) for row in grille
        )

        ttk.Label(
            vis_window,
            text=grille_str,
            font=("Consolas", 16),
            padding=20,
            background=self.COLORS["bg"],
            foreground=self.COLORS["fg"],
        ).pack()

    def _visualize_scytale(self):
        try:
            text = self.input_text.get("1.0", tk.END).rstrip("\n")
            key = int(self.key_entry.get())
            if not text or key <= 0:
                raise ValueError("Текст не пуст, ключ > 0.")
            ScytaleAnimationWindow(self, text, key, self.COLORS)
        except Exception as e:
            messagebox.showerror("Ошибка ввода", f"Невозможно запустить анимацию: {e}")

    def _process_encrypt(self):
        # Корректное получение текста из виджета.
        text = self.input_text.get("1.0", tk.END).rstrip("\n")
        if not text:
            messagebox.showerror("Ошибка", "Исходный текст пуст.")
            return
        try:
            if self.selected_cipher.get() == "scytale":
                key = int(self.key_entry.get())
                result = ciphers.scytale_encrypt(text, key)
            else:  # cardan
                key_phrase = self.cardan_key_entry.get()
                if not key_phrase:
                    messagebox.showerror("Ошибка", "Введите ключевое слово.")
                    return
                random.seed(key_phrase)
                size = self.grille_size_var.get()
                grille = ciphers.cardan_generate_grille(size)
                self._show_grille_visualization(grille)
                padded = text.ljust(size * size, "_")[: size * size]
                result = ciphers.cardan_encrypt(padded, grille)
            self._display_result(result)
        except Exception as e:
            messagebox.showerror("Ошибка ввода", str(e))

    def _process_decrypt(self):
        text = self.input_text.get("1.0", tk.END).rstrip("\n")
        if not text:
            messagebox.showerror("Ошибка", "Исходный текст пуст.")
            return
        try:
            if self.selected_cipher.get() == "scytale":
                key = int(self.key_entry.get())
                result = ciphers.scytale_decrypt(text, key)
            else:  # cardan
                key_phrase = self.cardan_key_entry.get()
                if not key_phrase:
                    messagebox.showerror("Ошибка", "Введите ключ.")
                    return
                # Повторное использование того же seed для восстановления ключа.
                random.seed(key_phrase)
                size = self.grille_size_var.get()
                grille = ciphers.cardan_generate_grille(size)
                self._show_grille_visualization(grille)
                if len(text) != size * size:
                    messagebox.showerror(
                        "Ошибка", f"Длина текста ({len(text)}) должна быть {size*size}."
                    )
                    return
                result = ciphers.cardan_decrypt(text, grille).rstrip("_")
            self._display_result(result)
        except Exception as e:
            messagebox.showerror("Ошибка ввода", str(e))


if __name__ == "__main__":
    app = CipherApp()
    app.mainloop()
