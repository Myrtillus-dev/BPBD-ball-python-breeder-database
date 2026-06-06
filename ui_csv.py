"""CSV Export / Import dialog."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import database as db
from ui_helpers import C

TABLES = ["animals","husbandry","health","clutches","hatchlings"]

class CsvDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("CSV Export / Import")
        self.configure(bg=C["bg"])
        self.grab_set()
        self.geometry("480x420")
        self.resizable(False,False)
        self._build()

    def _build(self):
        tk.Label(self, text="CSV Export / Import", bg=C["bg"],
                 fg=C["accent"], font=("Segoe UI",13,"bold")).pack(pady=(14,4))

        # ── Export / Import ALL ───────────────────────────────────────────────
        all_frame = tk.Frame(self, bg=C["card"], padx=12, pady=8)
        all_frame.pack(fill="x", padx=16, pady=(0,8))
        tk.Label(all_frame, text="All tables at once:", bg=C["card"],
                 fg=C["text_dim"], font=("Segoe UI",9,"bold")).pack(anchor="w", pady=(0,4))
        all_btn = tk.Frame(all_frame, bg=C["card"])
        all_btn.pack(anchor="w")
        ttk.Button(all_btn, text="⬇  Export ALL to folder",
                   command=self._export_all, style="Accent.TButton"
                  ).pack(side="left", padx=(0,8))
        ttk.Button(all_btn, text="⬆  Import ALL from folder",
                   command=self._import_all
                  ).pack(side="left")

        # ── Single table ──────────────────────────────────────────────────────
        sep = tk.Frame(self, bg=C["border"], height=1)
        sep.pack(fill="x", padx=16, pady=4)
        tk.Label(self, text="Single table:", bg=C["bg"],
                 fg=C["text_dim"], font=("Segoe UI",9,"bold")).pack(anchor="w", padx=16)

        row = tk.Frame(self, bg=C["bg"])
        row.pack(fill="x", padx=16, pady=4)
        self.table_var = tk.StringVar(value="animals")
        ttk.Combobox(row, textvariable=self.table_var, values=TABLES,
                     state="readonly", width=18).pack(side="left", padx=(0,8))
        ttk.Button(row, text="⬇  Export",
                   command=self._export, style="Accent.TButton"
                  ).pack(side="left", padx=(0,6))
        ttk.Button(row, text="⬆  Import",
                   command=self._import
                  ).pack(side="left")

        self._log = tk.Text(self, height=8, bg=C["entry"], fg=C["text"],
                            font=("Consolas",9), relief="flat",
                            highlightthickness=1, highlightbackground=C["border"])
        self._log.pack(fill="both", expand=True, padx=16, pady=(8,16))
        self._log.configure(state="disabled")

    def _log_msg(self, msg):
        self._log.configure(state="normal")
        self._log.insert("end", msg+"\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _export_all(self):
        """Export all tables to a chosen folder as separate CSV files."""
        folder = filedialog.askdirectory(title="Select folder for CSV export")
        if not folder: return
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
        """Import all tables from CSV files in a chosen folder."""
        folder = filedialog.askdirectory(title="Select folder with CSV files")
        if not folder: return
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
        table = self.table_var.get()
        path  = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files","*.csv"),("All files","*.*")],
            initialfile=f"{table}.csv",
            title=f"Export {table}")
        if not path: return
        csv_text = db.export_csv(table)
        if not csv_text:
            self._log_msg(f"No data in table '{table}'."); return
        with open(path,"w",encoding="utf-8",newline="") as f:
            f.write(csv_text)
        self._log_msg(f"✅ Exported '{table}' to:\n   {path}")

    def _import(self):
        table = self.table_var.get()
        path  = filedialog.askopenfilename(
            filetypes=[("CSV files","*.csv"),("All files","*.*")],
            title=f"Import into {table}")
        if not path: return
        if not messagebox.askyesno("Confirm Import",
            f"Import CSV into '{table}'?\nExisting rows with same ID will be skipped.",
            parent=self):
            return
        with open(path,"r",encoding="utf-8-sig") as f:
            csv_text = f.read()
        try:
            n = db.import_csv(table, csv_text)
            self._log_msg(f"✅ Imported {n} rows into '{table}'.")
            self.app.refresh_all()
        except Exception as e:
            self._log_msg(f"❌ Import error: {e}")
