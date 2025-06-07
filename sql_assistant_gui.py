import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import pandas as pd
import os
import queue

class Colors:
    BACKGROUND = "#0a0a1f"
    FRAME = "#1a1a38"
    BORDER = "#00f0ff"
    HEADER = "#ff00a6"
    TEXT_PRIMARY = "#e0e0e0"
    TEXT_SECONDARY = "#00f0ff"
    INPUT_BG = "#2a2a4f"
    SELECT_BG = "#4a4e69"
    BUTTON_FG = "#00f0ff"

class SQLAssistantGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SQL Assistant")
        self.root.configure(bg=Colors.BACKGROUND)
        self.root.geometry("1200x800")
        
        self.response_queue = queue.Queue()
        self.current_df_to_download = None

        self._build_ui()

    def _build_ui(self):
        main_frame = tk.Frame(self.root, bg=Colors.BACKGROUND, padx=10, pady=10)
        main_frame.pack(expand=True, fill="both")
        
        self.display_frame = tk.Frame(main_frame, bg=Colors.FRAME, highlightbackground=Colors.BORDER, highlightthickness=1)
        self.display_frame.pack(expand=True, fill="both", pady=(0, 10))
        
        title_bar = tk.Frame(self.display_frame, bg=Colors.FRAME)
        title_bar.pack(fill="x", pady=10, padx=10)

        self.title_label = tk.Label(title_bar, font=("Consolas", 18, "bold"), bg=Colors.FRAME, fg=Colors.HEADER)
        self.title_label.pack(side="left")

        self.download_button = tk.Button(title_bar, text="💾 Download", font=("Consolas", 10, "bold"),
                                         bg=Colors.INPUT_BG, fg=Colors.BUTTON_FG, relief="flat", command=self._download_current_df)
        
        self.content_frame = tk.Frame(self.display_frame, bg=Colors.FRAME)
        self.content_frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.tree = ttk.Treeview(self.content_frame, style="Custom.Treeview")
        self.message_area = scrolledtext.ScrolledText(self.content_frame, wrap=tk.WORD, font=("Consolas", 11), bg=Colors.INPUT_BG, fg=Colors.TEXT_PRIMARY, relief="flat", bd=0)

        self.status_label = tk.Label(main_frame, text="Initializing...", font=("Consolas", 11), bg=Colors.BACKGROUND, fg=Colors.TEXT_SECONDARY, anchor="w")
        self.status_label.pack(fill="x")
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview", background=Colors.FRAME, foreground=Colors.TEXT_PRIMARY, fieldbackground=Colors.FRAME, rowheight=25)
        style.configure("Custom.Treeview.Heading", background=Colors.INPUT_BG, foreground=Colors.HEADER, font=("Consolas", 11, "bold"), relief="flat")
        style.map("Custom.Treeview.Heading", relief=[('active', 'groove'), ('pressed', 'sunken')])

    def _clear_content_frame(self):
        self.download_button.pack_forget()
        for widget in self.content_frame.winfo_children():
            widget.pack_forget()

    def _download_current_df(self):
        if self.current_df_to_download is None or self.current_df_to_download.empty:
            self.update_status("No data available to download.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Save Table Data"
        )
        if not file_path: return

        try:
            if file_path.endswith('.csv'):
                self.current_df_to_download.to_csv(file_path, index=False)
            elif file_path.endswith('.xlsx'):
                self.current_df_to_download.to_excel(file_path, index=False)
            self.update_status(f"Table successfully saved to {os.path.basename(file_path)}")
        except Exception as e:
            self.update_status(f"Error saving file: {e}")

    def display_table(self, df: pd.DataFrame, title: str):
        self.title_label.config(text=f"📊 {title}")
        self._clear_content_frame()
        self.tree.pack(expand=True, fill="both")
        
        self.current_df_to_download = df 
        self.download_button.pack(side="right")

        for i in self.tree.get_children():
            self.tree.delete(i)
        
        if df is None or df.empty:
            self.tree["columns"] = ("1",)
            self.tree.heading("1", text="Result")
            self.tree.insert("", "end", values=("No data to display.",))
            return
            
        self.tree["columns"] = list(df.columns)
        self.tree["show"] = "headings"
        
        for col in df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="w", width=120)

        for index, row in df.iterrows():
            self.tree.insert("", "end", values=list(row))

    def display_message(self, title: str, message: str, symbol="ℹ️"):
        self.title_label.config(text=f"{symbol} {title}")
        self._clear_content_frame()
        self.current_df_to_download = None # No DF to download
        self.message_area.pack(expand=True, fill="both")
        self.message_area.config(state=tk.NORMAL)
        self.message_area.delete(1.0, tk.END)
        self.message_area.insert(tk.END, message)
        self.message_area.config(state=tk.DISABLED)

    def prompt_for_menu_choice(self, title, intro_text, options_list):
        self.display_message(title, intro_text, symbol="✨")
        
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.configure(bg=Colors.BACKGROUND)
        dialog.transient(self.root)
        
        tk.Label(dialog, text=intro_text, font=("Consolas", 12), bg=Colors.BACKGROUND, fg=Colors.TEXT_PRIMARY).pack(pady=20, padx=20)
        
        button_frame = tk.Frame(dialog, bg=Colors.BACKGROUND)
        button_frame.pack(pady=10, padx=20, fill="x")

        def on_choice(value):
            self.response_queue.put(value)
            dialog.destroy()

        for option in options_list:
            btn = tk.Button(button_frame, text=option["text"], font=("Consolas", 11, "bold"),
                            bg=Colors.INPUT_BG, fg=Colors.BUTTON_FG, relief="flat",
                            command=lambda v=option["value"]: on_choice(v))
            btn.pack(fill="x", pady=5)
            
        self.root.wait_window(dialog)
        try:
            return self.response_queue.get_nowait()
        except queue.Empty:
            return None

    def prompt_for_text_input(self, prompt_text):
        dialog = tk.Toplevel(self.root)
        dialog.title(prompt_text)
        dialog.configure(bg=Colors.BACKGROUND)
        
        tk.Label(dialog, text=prompt_text, font=("Consolas", 12), bg=Colors.BACKGROUND, fg=Colors.TEXT_PRIMARY).pack(pady=20, padx=20)
        
        text_widget = tk.Text(dialog, height=5, font=("Consolas", 12), bg=Colors.INPUT_BG, fg=Colors.TEXT_PRIMARY, insertbackground=Colors.TEXT_PRIMARY, relief="flat", bd=2)
        text_widget.pack(padx=20, pady=10, fill="both", expand=True)
        text_widget.focus_set()

        def on_submit():
            self.response_queue.put(text_widget.get("1.0", tk.END).strip())
            dialog.destroy()

        submit_btn = tk.Button(dialog, text="Submit", command=on_submit, font=("Consolas", 11, "bold"), bg=Colors.INPUT_BG, fg=Colors.BUTTON_FG, relief="flat")
        submit_btn.pack(pady=20)
        
        self.root.wait_window(dialog)
        try:
            return self.response_queue.get_nowait()
        except queue.Empty:
            return None

    def prompt_for_file(self, purpose):
        self.update_status(f"Waiting for user to select a file for: {purpose}")
        filepath = filedialog.askopenfilename(title=f"Select file for {purpose}")
        self.update_status("File selected.")
        return filepath

    def update_status(self, text: str):
        self.status_label.config(text=text)

    def run(self):
        self.root.mainloop()