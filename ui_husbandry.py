"""
ui_husbandry.py — Husbandry Logs tab with CustomTkinter toolbar.

Shows feeding, weight, shed, cleaning and other daily care logs.
Columns: Date | Animal | Event | Prey type | Prey(g) | Animal weight(g) | Fed? | Notes

Prey type is now a dropdown (Rat / Mice / Other).
Fed? is Yes or No only — partial feeding does not happen with ball pythons.
After save: syncs weight to Animal Profile via sync.after_husbandry_save().
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import customtkinter as ctk
import database as db
from ui_helpers import C, make_tree, toolbar_frame, btn, open_form, confirm_delete

# ── Form field definitions ────────────────────────────────────────────────────
# Prey Type is a combo (not free text) — Rat, Mice or Other
# Fed? is Yes/No only — no Partial option for ball pythons
FIELDS = [
    ("Date (YYYY-MM-DD) *", "date",          "entry"),
    ("Animal *",             "animal_id",     "combo_live"),
    ("Event Type *",         "event_type",    "combo",
     ["Feeding","Weight Check","Shed","Defecation","Cleaning","Medication","Other"]),
    ("Prey Type",            "prey_type",     "combo", ["", "Rat", "Mice", "Other"]),
    ("Prey Weight (g)",      "prey_weight",   "entry"),
    ("Fed?",                 "fed",           "combo", ["", "Yes", "No"]),
    ("Refusal Reason",       "refusal_reason","entry"),
    ("Weight (g)",           "weight_g",      "entry"),
    ("Length (cm)",          "length_cm",     "entry"),
    ("In Blue (pre-shed)?",  "in_blue",       "combo", ["", "Yes", "No"]),
    ("Complete Shed?",       "complete_shed", "combo", ["", "Yes", "No"]),
    ("Shed Date",            "shed_date",     "entry"),
    ("Defecation?",          "defecation",    "combo", ["", "Yes", "No"]),
    ("Cleaning Done?",       "cleaning",      "combo", ["", "Yes", "No"]),
    ("Logged By",            "logged_by",     "entry"),
    ("Notes",                "notes",         "text"),
]

# ── Treeview columns ──────────────────────────────────────────────────────────
COLS   = ("Date","Animal","Event","Prey type","Prey (g)","Anim.wt(g)","Fed?","Notes")
WIDTHS = (100, 130, 120, 120, 70, 80, 60, 200)


class HusbandryTab(ctk.CTkFrame):
    """Husbandry Logs tab — all daily care events for all animals."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg"])
        self.pack(fill="both", expand=True)
        self.app = app
        self._build()

    def _build(self):
        """Build toolbar with animal/event filters and the log treeview."""
        # ── Toolbar ───────────────────────────────────────────────────────────
        tb = toolbar_frame(self)
        btn(tb, "＋  Add Log", self._add, accent=True)
        btn(tb, "✏  Edit",     self._edit)
        btn(tb, "🗑  Delete",   self._delete)
        btn(tb, "↻  Refresh",  self.load)

        # Filter by animal
        ctk.CTkLabel(tb, text="  Animal:", font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["text_dim"]).pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        self.filter_cb  = ctk.CTkComboBox(tb, variable=self.filter_var,
                                          width=190, height=36, state="readonly",
                                          fg_color=C["entry"],
                                          border_color=C["border"],
                                          button_color=C["card2"],
                                          text_color=C["text"],
                                          dropdown_fg_color=C["card"],
                                          dropdown_text_color=C["text"],
                                          command=lambda _: self.load())
        self.filter_cb.pack(side="left", padx=4, pady=9)

        # Filter by event type
        ctk.CTkLabel(tb, text="  Event:", font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["text_dim"]).pack(side="left")
        self.event_var = tk.StringVar(value="All")
        ctk.CTkComboBox(tb, variable=self.event_var, width=140, height=36,
                        state="readonly",
                        values=["All","Feeding","Weight Check","Shed",
                                "Defecation","Cleaning","Medication","Other"],
                        fg_color=C["entry"], border_color=C["border"],
                        button_color=C["card2"], text_color=C["text"],
                        dropdown_fg_color=C["card"], dropdown_text_color=C["text"],
                        command=lambda _: self.load()
                       ).pack(side="left", padx=4)

        # ── Treeview ──────────────────────────────────────────────────────────
        frame, self.tree = make_tree(self, COLS, WIDTHS)
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tree.bind("<Double-1>", lambda e: self._edit())
        self.load()

    def load(self):
        """
        Reload logs from database.
        Refreshes the animal dropdown so new animals appear immediately.
        Rows where Fed?=No are shown in red (deceased tag).
        """
        # Refresh animal filter dropdown with current animals
        ids = ["All"] + db.get_animal_ids()
        self.filter_cb.configure(values=ids)

        filt = self.filter_var.get()
        aid  = db.resolve_combo(filt) if filt != "All" else None
        rows = db.get_husbandry(aid)

        # Apply event type filter
        evt = self.event_var.get()
        if evt != "All":
            rows = [r for r in rows if r["event_type"] == evt]

        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(rows):
            name = r["animal_name"] if "animal_name" in r.keys() else r["animal_id"]
            # Refused feedings shown red, alternating row colors otherwise
            tag  = "deceased" if r["fed"] == "No" else ("even" if i%2==0 else "odd")
            self.tree.insert("", "end", iid=str(r["id"]),
                values=(r["date"], name or r["animal_id"],
                        r["event_type"] or "",
                        r["prey_type"] or "",
                        r["prey_weight"] or "",
                        r["weight_g"] or "",
                        r["fed"] or "",
                        r["notes"] or ""),
                tags=(tag,))

    def _selected_id(self):
        """Return integer ID of selected log row, or None."""
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def _add(self):
        """Open blank log entry form."""
        self._open_form(None)

    def _edit(self):
        """Open form pre-filled with selected log entry."""
        hid = self._selected_id()
        if not hid:
            messagebox.showinfo("Select", "Select a log entry first.")
            return
        self._open_form(hid)

    def _delete(self):
        """Delete selected log entry after confirmation."""
        hid = self._selected_id()
        if not hid:
            return
        if confirm_delete("this log entry"):
            db.delete_husbandry(hid)
            self.load()

    def _open_form(self, hid):
        """
        Open add/edit dialog for a husbandry log entry.
        hid=None means new entry; hid=int means edit existing.

        After save:
          - sync.after_husbandry_save() updates animals.weight_g if Weight Check
          - Animals tab and Dashboard are refreshed
        """
        is_new   = (hid is None)
        existing = {"date": str(date.today())}

        if not is_new:
            row = db.fetchone("SELECT * FROM husbandry WHERE id=?", (hid,))
            if row:
                existing = {k: str(row[k]) if row[k] is not None else ""
                            for k in row.keys()}
                # Convert animal_id to "ID – Name" format for the combo_live dropdown
                a = db.get_animal(existing.get("animal_id", ""))
                if a:
                    existing["animal_id"] = f"{a['id']} – {a['name'] or ''}"

        def on_save(data, win):
            # Validate required fields
            if not data.get("date") or not data.get("animal_id") or not data.get("event_type"):
                messagebox.showerror("Required",
                    "Date, Animal and Event Type are required.", parent=win)
                return
            # Resolve "ID – Name" back to just ID
            data["animal_id"] = db.resolve_combo(data["animal_id"])
            if not is_new:
                data["id"] = hid
            try:
                db.save_husbandry(data)
                # Sync weight to Animal Profile if this is a Weight Check
                import sync
                sync.after_husbandry_save(data)
                win.destroy()
                self.load()
                self.app.tab_animals.load()
                self.app.tab_dash.load()
            except Exception as e:
                messagebox.showerror("Save Error", str(e), parent=win)

        open_form(self, "Log Entry", FIELDS, existing, on_save=on_save)
