"""
ui_csv.py — CSV Export/Import dialog with CustomTkinter.

Provides two modes:
  1. Export/Import ALL tables at once to/from a chosen folder
     - Exports each table as a separate .csv file (animals.csv, etc.)
     - Import reads all .csv files from folder, skips existing IDs
  2. Single table export/import via dropdown

Tables: animals | husbandry | health | clutches | hatchlings

All operations are logged in the text area at the bottom of the dialog.
Import never overwrites existing rows (INSERT OR IGNORE).
After import: app.refresh_all() updates all tabs.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
import os
import database as db
from ui_helpers import C

# Tables available for export/import
TABLES = ["animals", "husbandry", "health", "clutches", "hatchlings"]


class CsvDialog(ctk.CTkToplevel):
    """Modal dialog for CSV export and import operations."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("CSV Export / Import")
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self.geometry("500x460")
        self.resizable(False, False)
        self._build()

    def _build(self):
        """Build dialog: title, all-tables section, single-table section, log."""

        # Title
        ctk.CTkLabel(self, text="CSV Export / Import",
                     font=ctk.CTkFont("Segoe UI", 14, "bold"),
                     text_color=C["accent"]
                    ).pack(pady=(18, 6))

        # ── Export/Import ALL tables ──────────────────────────────────────────
        all_frame = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=8)
        all_frame.pack(fill="x", padx=16, pady=(0, 8))
        ctk.CTkLabel(all_frame, text="All tables at once:",
                     font=ctk.CTkFont("Segoe UI", 10, "bold"),
                     text_color=C["text_dim"]
                    ).pack(anchor="w", padx=12, pady=(10, 4))

        btn_row = ctk.CTkFrame(all_frame, fg_color=C["card"])
        btn_row.pack(anchor="w", padx=12, pady=(0, 10))

        ctk.CTkButton(btn_row, text="⬇  Export ALL to folder",
                      command=self._export_all,
                      width=200, height=34, corner_radius=6,
                      fg_color=C["accent_dim"], hover_color=C["accent"],
                      text_color="#ffffff",
                      font=ctk.CTkFont("Segoe UI", 10, "bold")
                     ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(btn_row, text="⬆  Import ALL from folder",
                      command=self._import_all,
                      width=200, height=34, corner_radius=6,
                      fg_color=C["card2"], hover_color=C["accent"],
                      text_color=C["text"],
                      border_width=1, border_color=C["border"]
                     ).pack(side="left")

        # ── Single table section ──────────────────────────────────────────────
        sep = ctk.CTkFrame(self, fg_color=C["border"], height=1, corner_radius=0)
        sep.pack(fill="x", padx=16, pady=6)

        ctk.CTkLabel(self, text="Single table:",
                     font=ctk.CTkFont("Segoe UI", 10, "bold"),
                     text_color=C["text_dim"]
                    ).pack(anchor="w", padx=16)

        row = ctk.CTkFrame(self, fg_color=C["bg"])
        row.pack(fill="x", padx=16, pady=4)

        self.table_var = tk.StringVar(value="animals")
        ctk.CTkComboBox(row, variable=self.table_var, values=TABLES,
                        width=160, height=36, state="readonly",
                        fg_color=C["entry"], border_color=C["border"],
                        button_color=C["card2"], text_color=C["text"],
                        dropdown_fg_color=C["card"], dropdown_text_color=C["text"]
                       ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(row, text="⬇  Export",
                      command=self._export,
                      width=110, height=34, corner_radius=6,
                      fg_color=C["accent_dim"], hover_color=C["accent"],
                      text_color="#ffffff"
                     ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(row, text="⬆  Import",
                      command=self._import,
                      width=110, height=34, corner_radius=6,
                      fg_color=C["card2"], hover_color=C["accent"],
                      text_color=C["text"],
                      border_width=1, border_color=C["border"]
                     ).pack(side="left")

        # ── Operation log ─────────────────────────────────────────────────────
        self._log = tk.Text(self, height=10, bg=C["entry"], fg=C["text"],
                            font=("Consolas", 9), relief="flat",
                            insertbackground=C["text"],
                            highlightthickness=1,
                            highlightbackground=C["border"])
        self._log.pack(fill="both", expand=True, padx=16, pady=(8, 16))
        self._log.configure(state="disabled")

    def _log_msg(self, msg):
        """Append a message to the log text area."""
        self._log.configure(state="normal")
        self._log.insert("end", msg + "\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _export_all(self):
        """
        Export all tables to separate CSV files in a chosen folder.
        File names: animals.csv, husbandry.csv, etc.
        Tables with no data are skipped.
        """
        folder = filedialog.askdirectory(title="Select folder for CSV export")
        if not folder:
            return
        exported = 0
        for table in TABLES:
            csv_text = db.export_csv(table)
            if csv_text:
                path = os.path.join(folder, f"{table}.csv")
                with open(path, "w", encoding="utf-8", newline="") as f:
                    f.write(csv_text)
                self._log_msg(f"✅ {table}.csv")
                exported += 1
            else:
                self._log_msg(f"⏭  {table} — no data, skipped")
        self._log_msg(f"\nExported {exported}/{len(TABLES)} tables to:\n   {folder}")

    def _import_all(self):
        """
        Import all tables from CSV files in a chosen folder.
        Looks for: animals.csv, husbandry.csv, health.csv, clutches.csv, hatchlings.csv
        Existing rows (same primary key) are skipped — no overwrites.
        """
        folder = filedialog.askdirectory(title="Select folder with CSV files")
        if not folder:
            return
        if not messagebox.askyesno("Confirm Import All",
            "Import all CSV files from this folder?\n"
            "Existing rows with same ID will be skipped.\n\n"
            f"Folder: {folder}", parent=self):
            return
        total = 0
        for table in TABLES:
            path = os.path.join(folder, f"{table}.csv")
            if not os.path.exists(path):
                self._log_msg(f"⏭  {table}.csv not found, skipped")
                continue
            with open(path, "r", encoding="utf-8-sig") as f:
                csv_text = f.read()
            try:
                n = db.import_csv(table, csv_text)
                self._log_msg(f"✅ {table}: {n} rows imported")
                total += n
            except Exception as e:
                self._log_msg(f"❌ {table}: {e}")
        self._log_msg(f"\nTotal: {total} rows imported")
        self.app.refresh_all()

    def _export(self):
        """Export single selected table to a .csv file."""
        table = self.table_var.get()
        path  = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"{table}.csv",
            title=f"Export {table}")
        if not path:
            return
        csv_text = db.export_csv(table)
        if not csv_text:
            self._log_msg(f"No data in table '{table}'.")
            return
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(csv_text)
        self._log_msg(f"✅ Exported '{table}' to:\n   {path}")

    def _import(self):
        """Import single CSV file into selected table. Skips existing rows."""
        table = self.table_var.get()
        path  = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title=f"Import into {table}")
        if not path:
            return
        if not messagebox.askyesno("Confirm Import",
            f"Import CSV into '{table}'?\n"
            "Existing rows with same ID will be skipped.", parent=self):
            return
        with open(path, "r", encoding="utf-8-sig") as f:
            csv_text = f.read()
        try:
            n = db.import_csv(table, csv_text)
            self._log_msg(f"✅ Imported {n} rows into '{table}'.")
            self.app.refresh_all()
        except Exception as e:
            self._log_msg(f"❌ Import error: {e}")
