"""
ui_clutches.py — Clutch Management tab with CustomTkinter toolbar.

Tracks the full breeding cycle:
  Pairing → Lock observed → Ovulation → Pre-lay shed →
  Lay date → Incubation → Actual hatch date

Estimated hatch date is calculated automatically as lay_date + 55 days
and shown with a ~ prefix when the actual hatch date is not yet set.

'Add Hatchlings' button auto-creates hatchling records for a clutch
(one per good egg). Records are created with status=Available.

After clutch save: sync.after_clutch_save() propagates hatch_date_actual
to all hatchlings of this clutch.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta
import customtkinter as ctk
import database as db
from ui_helpers import C, make_tree, toolbar_frame, btn, open_form, \
                       confirm_delete, STATUS_TAG

# ── Form field definitions ────────────────────────────────────────────────────
FIELDS = [
    ("Clutch ID *",          "id",               "entry"),
    ("Season / Year",        "season",           "entry"),
    ("Sire *",               "sire_id",          "combo_live"),
    ("Dam *",                "dam_id",           "combo_live"),
    ("Pairing Start",        "pairing_start",    "entry"),
    ("Lock Observed",        "lock_date",        "entry"),
    ("Lock Count",           "lock_count",       "entry"),
    ("Pairing End",          "pairing_end",      "entry"),
    ("Ovulation Date",       "ovulation_date",   "entry"),
    ("Pre-Lay Shed",         "prelay_shed",      "entry"),
    ("Lay Date",             "lay_date",         "entry"),
    ("Total Eggs",           "total_eggs",       "entry"),
    ("Good Eggs",            "good_eggs",        "entry"),
    ("Slugs",                "slugs",            "entry"),
    ("Incubation Temp (°C)", "incubation_temp",  "entry"),
    ("Humidity %",           "humidity_pct",     "entry"),
    ("Incubator",            "incubator",        "entry"),
    ("Incubation Start",     "incubation_start", "entry"),
    ("Actual Hatch Date",    "hatch_date_actual","entry"),
    ("Hatchlings (count)",   "hatchling_count",  "entry"),
    ("Status",               "status",           "combo",
     ["Pairing","Gravid","Incubating","Hatched","Failed"]),
    ("Notes",                "notes",            "text"),
]

# ── Treeview columns ──────────────────────────────────────────────────────────
COLS   = ("Clutch ID","Season","Sire","Dam","Lay Date","Eggs","Good",
          "Slugs","Est. Hatch","Hatchlings","Status")
WIDTHS = (110, 70, 130, 130, 100, 55, 55, 55, 105, 80, 100)


class ClutchTab(ctk.CTkFrame):
    """Clutch Management tab — full breeding cycle tracking."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg"])
        self.pack(fill="both", expand=True)
        self.app = app
        self._build()

    def _build(self):
        """Build toolbar and clutch treeview."""
        # ── Toolbar ───────────────────────────────────────────────────────────
        tb = toolbar_frame(self)
        btn(tb, "＋  Add Clutch",     self._add,             accent=True)
        btn(tb, "✏  Edit",            self._edit)
        btn(tb, "🐣  Add Hatchlings", self._add_hatchlings)
        btn(tb, "🗑  Delete",          self._delete)
        btn(tb, "↻  Refresh",         self.load)

        # Status filter
        ctk.CTkLabel(tb, text="  Status:", font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["text_dim"]).pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        ctk.CTkComboBox(tb, variable=self.filter_var, width=140, height=36,
                        state="readonly",
                        values=["All","Pairing","Gravid","Incubating","Hatched","Failed"],
                        fg_color=C["entry"], border_color=C["border"],
                        button_color=C["card2"], text_color=C["text"],
                        dropdown_fg_color=C["card"], dropdown_text_color=C["text"],
                        command=lambda _: self.load()
                       ).pack(side="left", padx=4, pady=9)

        # ── Treeview ──────────────────────────────────────────────────────────
        frame, self.tree = make_tree(self, COLS, WIDTHS)
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tree.bind("<Double-1>", lambda e: self._edit())
        self.load()

    def load(self):
        """Reload clutches, calculate estimated hatch dates (lay + 55 days)."""
        rows = db.get_all_clutches()
        filt = self.filter_var.get()
        if filt != "All":
            rows = [r for r in rows if r["status"] == filt]
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(rows):
            # Est. hatch = lay_date + 55 days; shown with ~ if not actual
            est = ""
            if r["lay_date"]:
                try:
                    est = str(date.fromisoformat(r["lay_date"]) + timedelta(days=55))
                except: pass
            sire = f"{r['sire_id'] or ''} {r['sire_name'] or ''}".strip()
            dam  = f"{r['dam_id']  or ''} {r['dam_name']  or ''}".strip()
            tag  = STATUS_TAG.get(r["status"], "even" if i%2==0 else "odd")
            self.tree.insert("", "end", iid=r["id"],
                values=(r["id"], r["season"] or "", sire, dam,
                        r["lay_date"] or "", r["total_eggs"] or "",
                        r["good_eggs"] or "", r["slugs"] or "",
                        r["hatch_date_actual"] or (f"~{est}" if est else ""),
                        r["hatchling_count"] or "", r["status"] or ""),
                tags=(tag,))

    def _selected_id(self):
        """Return ID of selected clutch row, or None."""
        sel = self.tree.selection()
        return sel[0] if sel else None

    def _add(self):  self._open_form(None)

    def _edit(self):
        cid = self._selected_id()
        if not cid:
            messagebox.showinfo("Select", "Select a clutch first.")
            return
        self._open_form(cid)

    def _delete(self):
        cid = self._selected_id()
        if not cid: return
        if confirm_delete(f"clutch '{cid}'"):
            db.delete_clutch(cid)
            self.load()

    def _add_hatchlings(self):
        """
        Auto-create hatchling records for the selected clutch.
        Uses hatchling_count (or good_eggs as fallback).
        IDs are formed as clutch_id + sequential number (no dash).
        Skips IDs that already exist so it's safe to run multiple times.
        """
        cid = self._selected_id()
        if not cid:
            messagebox.showinfo("Select", "Select a clutch first.")
            return
        clutch = db.get_clutch(cid)
        if not clutch:
            return
        count = clutch["hatchling_count"] or clutch["good_eggs"] or 0
        if not count:
            messagebox.showinfo("Info", "Set Hatchling Count on the clutch first.")
            return
        existing = {h["id"] for h in db.get_hatchlings(cid)}
        added = 0
        for i in range(1, int(count) + 1):
            hid = f"{cid}{i}"
            if hid not in existing:
                db.save_hatchling({
                    "id": hid, "clutch_id": cid,
                    "dam_id": clutch["dam_id"], "sire_id": clutch["sire_id"],
                    "hatch_date": clutch["hatch_date_actual"] or "",
                    "status": "Available",
                }, is_new=True)
                added += 1
        messagebox.showinfo("Done", f"Added {added} hatchling record(s) for clutch {cid}.")
        self.app.refresh_all()

    def _open_form(self, cid):
        """
        Open add/edit dialog for a clutch.
        Sire/Dam shown as 'ID – Name' in the dropdown.
        After save: sync.after_clutch_save() propagates hatch date to hatchlings.
        """
        is_new   = (cid is None)
        existing = {"season": str(date.today().year), "status": "Pairing"}
        if not is_new:
            row = db.get_clutch(cid)
            if row:
                existing = {k: str(row[k]) if row[k] is not None else ""
                            for k in row.keys()}
                # Convert sire/dam IDs to "ID – Name" for combo_live dropdowns
                for key in ("sire_id", "dam_id"):
                    a = db.get_animal(existing.get(key, ""))
                    if a:
                        existing[key] = f"{a['id']} – {a['name'] or ''}"

        def on_save(data, win):
            if not data.get("id"):
                messagebox.showerror("Required", "Clutch ID is required.", parent=win)
                return
            # Resolve "ID – Name" back to just ID
            data["sire_id"] = db.resolve_combo(data.get("sire_id"))
            data["dam_id"]  = db.resolve_combo(data.get("dam_id"))
            try:
                db.save_clutch(data, is_new=is_new)
                # Propagate hatch date to hatchlings if set
                import sync
                sync.after_clutch_save(data)
                win.destroy()
                self.load()
                self.app.tab_hatchlings.load()
            except Exception as e:
                messagebox.showerror("Save Error", str(e), parent=win)

        open_form(self, "Clutch", FIELDS, existing, on_save=on_save)
