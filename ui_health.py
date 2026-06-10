"""
ui_health.py — Health Records tab with CustomTkinter toolbar.

Tracks vet visits, medication courses, mite treatments,
behavioral changes and respiratory symptoms.

After save: Dashboard is refreshed so feeding alerts stay current.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import customtkinter as ctk
import database as db
from ui_helpers import C, make_tree, toolbar_frame, btn, open_form, confirm_delete

# ── Form field definitions ────────────────────────────────────────────────────
FIELDS = [
    ("Date (YYYY-MM-DD) *",    "date",         "entry"),
    ("Animal *",                "animal_id",    "combo_live"),
    ("Event Type *",            "event_type",   "combo",
     ["Vet Visit","Mite Treatment","Medication Course",
      "Quarantine","Behavioral Change","Respiratory Symptoms","Other"]),
    ("Description / Diagnosis", "description",  "entry"),
    ("Medication / Treatment",  "medication",   "entry"),
    ("Dosage",                  "dosage",       "entry"),
    ("Duration (days)",         "duration_days","entry"),
    ("Veterinarian",            "vet",          "entry"),
    ("Next Check-up",           "next_checkup", "entry"),
    ("Mite Check OK?",          "mite_check",   "combo", ["","Yes","No"]),
    ("Treatment Outcome",       "outcome",      "entry"),
    ("Cost (€)",                "cost",         "entry"),
    ("Notes",                   "notes",        "text"),
]

# ── Treeview columns ──────────────────────────────────────────────────────────
COLS   = ("Date","Animal","Event","Description","Medication","Outcome","Cost","Next Check-up")
WIDTHS = (100, 120, 160, 200, 140, 130, 70, 110)


class HealthTab(ctk.CTkFrame):
    """Health Records tab — logs all medical events per animal."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg"])
        self.pack(fill="both", expand=True)
        self.app = app
        self._build()

    def _build(self):
        """Build toolbar with animal filter and health records treeview."""
        # ── Toolbar ───────────────────────────────────────────────────────────
        tb = toolbar_frame(self)
        btn(tb, "＋  Add Record", self._add, accent=True)
        btn(tb, "✏  Edit",        self._edit)
        btn(tb, "🗑  Delete",      self._delete)
        btn(tb, "↻  Refresh",     self.load)

        # Filter by animal
        ctk.CTkLabel(tb, text="  Animal:", font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["text_dim"]).pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        self.filter_cb  = ctk.CTkComboBox(tb, variable=self.filter_var,
                                          width=190, height=36, state="readonly",
                                          fg_color=C["entry"], border_color=C["border"],
                                          button_color=C["card2"], text_color=C["text"],
                                          dropdown_fg_color=C["card"],
                                          dropdown_text_color=C["text"],
                                          command=lambda _: self.load())
        self.filter_cb.pack(side="left", padx=4, pady=9)

        # ── Treeview ──────────────────────────────────────────────────────────
        frame, self.tree = make_tree(self, COLS, WIDTHS)
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tree.bind("<Double-1>", lambda e: self._edit())
        self.load()

    def load(self):
        """Reload health records, refresh animal filter dropdown."""
        ids = ["All"] + db.get_animal_ids()
        self.filter_cb.configure(values=ids)
        filt = self.filter_var.get()
        aid  = db.resolve_combo(filt) if filt != "All" else None
        rows = db.get_health(aid)
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(rows):
            name = r["animal_name"] if "animal_name" in r.keys() else r["animal_id"]
            self.tree.insert("", "end", iid=str(r["id"]),
                values=(r["date"], name or r["animal_id"],
                        r["event_type"] or "", r["description"] or "",
                        r["medication"] or "", r["outcome"] or "",
                        f"€{float(r['cost']):.0f}" if r["cost"] else "",
                        r["next_checkup"] or ""),
                tags=("even" if i%2==0 else "odd",))

    def _selected_id(self):
        """Return integer ID of selected row, or None."""
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def _add(self):    self._open_form(None)
    def _edit(self):
        hid = self._selected_id()
        if not hid: messagebox.showinfo("Select","Select a record first."); return
        self._open_form(hid)
    def _delete(self):
        hid = self._selected_id()
        if not hid: return
        if confirm_delete("this health record"):
            db.delete_health(hid); self.load()

    def _open_form(self, hid):
        """
        Open add/edit dialog for a health record.
        After save: dashboard refreshed for alert updates.
        """
        is_new   = (hid is None)
        existing = {"date": str(date.today())}
        if not is_new:
            row = db.fetchone("SELECT * FROM health WHERE id=?", (hid,))
            if row:
                existing = {k: str(row[k]) if row[k] is not None else ""
                            for k in row.keys()}
                a = db.get_animal(existing.get("animal_id", ""))
                if a:
                    existing["animal_id"] = f"{a['id']} – {a['name'] or ''}"

        def on_save(data, win):
            if not data.get("date") or not data.get("animal_id"):
                messagebox.showerror("Required","Date and Animal are required.",parent=win)
                return
            data["animal_id"] = db.resolve_combo(data["animal_id"])
            if not is_new:
                data["id"] = hid
            try:
                db.save_health(data)
                win.destroy()
                self.load()
                self.app.tab_dash.load()
            except Exception as e:
                messagebox.showerror("Save Error", str(e), parent=win)

        open_form(self, "Health Record", FIELDS, existing, on_save=on_save)
