"""
ui_animals.py — Animal Profiles tab with CustomTkinter toolbar.

FIELDS defines all form fields shown when adding/editing an animal.
The Status dropdown includes Holdback so animals synced from hatchlings
can be properly tracked.

Feed interval per animal controls how often feeding alerts fire on the dashboard.
Microchip field has been removed — ball pythons are not chipped.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import database as db
from ui_helpers import C, make_tree, toolbar_frame, btn, open_form, \
                       confirm_delete, STATUS_TAG

# ── Form field definitions ────────────────────────────────────────────────────
# Each tuple: (label, db_column, field_type, [options_if_combo])
FIELDS = [
    ("ID *",                      "id",           "entry"),
    ("Name",                      "name",         "entry"),
    ("Sex",                       "sex",          "combo",  ["", "Male", "Female", "Unknown"]),
    ("Date of Birth (YYYY-MM-DD)","dob",          "entry"),
    ("Acquired Date",             "acquired",     "entry"),
    ("Purchase Price (€)",        "price",        "entry"),
    ("Breeder / Seller",          "breeder",      "entry"),
    ("Morph / Visual",            "morph",        "entry"),
    ("Het / Carrier",             "het",          "entry"),
    ("Other Genetics",            "genetic_notes","entry"),
    ("Rack / Enclosure",          "rack",         "entry"),
    ("Row / Level",               "rack_level",   "entry"),
    ("Weight (g)",                "weight_g",     "entry"),
    ("Feed Interval (days)",      "feed_interval","combo", ["7","10","14","21","28"]),
    ("Status",                    "status",       "combo",
     ["Active", "Holdback", "Quarantine", "Removed", "Sold", "Deceased"]),
    ("Sire ID",                   "sire_id",      "entry"),
    ("Dam ID",                    "dam_id",       "entry"),
    ("Notes",                     "notes",        "text"),
]

# ── Treeview column definitions ───────────────────────────────────────────────
COLS   = ("ID", "Name", "Sex", "Morph", "Het", "Rack", "Weight(g)", "Feed Every", "Status")
WIDTHS = (90, 120, 70, 180, 160, 100, 80, 80, 80)


class AnimalsTab(ctk.CTkFrame):
    """Main Animals tab — lists all animals, provides add/edit/delete."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg"])
        self.pack(fill="both", expand=True)
        self.app = app
        self._build()

    def _build(self):
        """Build toolbar and treeview."""
        # ── Toolbar ───────────────────────────────────────────────────────────
        tb = toolbar_frame(self)
        btn(tb, "＋  Add",    self._add,    accent=True)
        btn(tb, "✏  Edit",    self._edit)
        btn(tb, "🗑  Delete",  self._delete)
        btn(tb, "↻  Refresh", self.load)

        # Status filter dropdown
        ctk.CTkLabel(tb, text="  Status:", font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["text_dim"]).pack(side="left")
        self.filter_var = tk.StringVar(value="Active")
        ctk.CTkComboBox(tb, variable=self.filter_var, width=130, height=36,
                        state="readonly",
                        values=["All","Active","Holdback","Quarantine",
                                "Removed","Sold","Deceased"],
                        fg_color=C["entry"], border_color=C["border"],
                        button_color=C["card2"], text_color=C["text"],
                        dropdown_fg_color=C["card"], dropdown_text_color=C["text"],
                        command=lambda _: self.load()
                       ).pack(side="left", padx=4, pady=9)

        # Search box — filters by ID, name, morph or het
        ctk.CTkLabel(tb, text="  Search:", font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["text_dim"]).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._search())
        ctk.CTkEntry(tb, textvariable=self.search_var, width=190, height=36,
                     fg_color=C["entry"], border_color=C["border"],
                     text_color=C["text"]
                    ).pack(side="left", padx=4)

        # ── Treeview ──────────────────────────────────────────────────────────
        frame, self.tree = make_tree(self, COLS, WIDTHS)
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tree.bind("<Double-1>", lambda e: self._edit())
        self._all_rows = []
        self.load()

    def load(self):
        """Reload all animals from database and refresh the list."""
        self._all_rows = db.get_all_animals(self.filter_var.get())
        self._populate(self._all_rows)

    def _populate(self, rows):
        """Fill treeview with given rows, applying status color tags."""
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(rows):
            tag = STATUS_TAG.get(r["status"], "even" if i % 2 == 0 else "odd")
            fi  = r["feed_interval"] or 7
            self.tree.insert("", "end", iid=r["id"],
                values=(r["id"], r["name"] or "", r["sex"] or "",
                        r["morph"] or "", r["het"] or "",
                        r["rack"] or "", r["weight_g"] or "",
                        f"{fi}d", r["status"] or ""),
                tags=(tag,))

    def _search(self):
        """Filter visible rows by search text (ID, name, morph, het)."""
        q = self.search_var.get().lower()
        if not q:
            self._populate(self._all_rows)
            return
        self._populate([r for r in self._all_rows
                        if q in str(r["id"]).lower() or
                           q in str(r["name"] or "").lower() or
                           q in str(r["morph"] or "").lower() or
                           q in str(r["het"] or "").lower()])

    def _selected_id(self):
        """Return the ID of the currently selected row, or None."""
        sel = self.tree.selection()
        return sel[0] if sel else None

    def _add(self):
        """Open blank form to add a new animal."""
        self._open_form(None)

    def _edit(self):
        """Open form pre-filled with selected animal's data."""
        aid = self._selected_id()
        if not aid:
            messagebox.showinfo("Select", "Select an animal first.")
            return
        self._open_form(aid)

    def _delete(self):
        """Delete the selected animal after confirmation."""
        aid = self._selected_id()
        if not aid:
            return
        if confirm_delete(f"animal '{aid}'"):
            db.delete_animal(aid)
            self.load()
            self.app.refresh_all()

    def _open_form(self, aid):
        """
        Open add/edit dialog.
        aid=None means new animal; aid=string means edit existing.
        After save: refreshes this tab and all other tabs via app.refresh_all().
        """
        is_new   = (aid is None)
        existing = {}
        if not is_new:
            row = db.get_animal(aid)
            if row:
                # Convert all values to strings so CTk widgets display them correctly
                existing = {k: str(row[k]) if row[k] is not None else ""
                            for k in row.keys()}

        def on_save(data, win):
            if not data.get("id"):
                messagebox.showerror("Required", "ID is required.", parent=win)
                return
            try:
                db.save_animal(data, is_new=is_new)
                win.destroy()
                self.load()
                self.app.refresh_all()
            except Exception as e:
                messagebox.showerror("Save Error", str(e), parent=win)

        open_form(self, f"{'Add' if is_new else 'Edit'} Animal",
                  FIELDS, existing, on_save=on_save)
