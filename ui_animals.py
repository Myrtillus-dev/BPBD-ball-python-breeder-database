"""Animals tab — microchip removed, feed_interval added, edit fixed."""
import tkinter as tk
from tkinter import ttk, messagebox
import database as db
from ui_helpers import C, make_tree, toolbar_frame, btn, open_form, \
                       confirm_delete, STATUS_TAG

FIELDS = [
    ("ID *",               "id",           "entry"),
    ("Name",               "name",         "entry"),
    ("Sex",                "sex",          "combo",  ["","Male","Female","Unknown"]),
    ("Date of Birth",      "dob",          "entry"),
    ("Acquired Date",      "acquired",     "entry"),
    ("Purchase Price (€)", "price",        "entry"),
    ("Breeder / Seller",   "breeder",      "entry"),
    ("Morph / Visual",     "morph",        "entry"),
    ("Het / Carrier",      "het",          "entry"),
    ("Other Genetics",     "genetic_notes","entry"),
    ("Rack / Enclosure",   "rack",         "entry"),
    ("Row / Level",        "rack_level",   "entry"),
    ("Weight (g)",         "weight_g",     "entry"),
    ("Feed Interval (days)","feed_interval","combo",
     ["7","10","14","21","28"]),
    ("Status",             "status",       "combo",
     ["Active","Quarantine","Removed","Sold","Deceased"]),
    ("Sire ID",            "sire_id",      "entry"),
    ("Dam ID",             "dam_id",       "entry"),
    ("Notes",              "notes",        "text"),
]

COLS   = ("ID","Name","Sex","Morph","Het","Rack","Weight(g)","Feed Every","Status")
WIDTHS = (90,120,70,180,160,100,80,80,80)

class AnimalsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        tb = toolbar_frame(self)
        btn(tb, "＋  Add",    self._add,    accent=True)
        btn(tb, "✏  Edit",    self._edit)
        btn(tb, "🗑  Delete",  self._delete)
        btn(tb, "↻  Refresh", self.load)

        tk.Label(tb, text="  Status:", bg=C["sidebar"],
                 fg=C["text_dim"], font=("Segoe UI",9)).pack(side="left")
        self.filter_var = tk.StringVar(value="Active")
        ttk.Combobox(tb, textvariable=self.filter_var, width=12, state="readonly",
                     values=["All","Active","Quarantine","Removed","Sold","Deceased"]
                    ).pack(side="left", padx=4, pady=8)
        self.filter_var.trace_add("write", lambda *a: self.load())

        tk.Label(tb, text="  Search:", bg=C["sidebar"],
                 fg=C["text_dim"], font=("Segoe UI",9)).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._search())
        ttk.Entry(tb, textvariable=self.search_var, width=18).pack(side="left", padx=4)

        frame, self.tree = make_tree(self, COLS, WIDTHS)
        frame.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self.tree.bind("<Double-1>", lambda e: self._edit())
        self._all_rows = []
        self.load()

    def load(self):
        self._all_rows = db.get_all_animals(self.filter_var.get())
        self._populate(self._all_rows)

    def _populate(self, rows):
        self.tree.delete(*self.tree.get_children())
        for i,r in enumerate(rows):
            tag = STATUS_TAG.get(r["status"], "even" if i%2==0 else "odd")
            fi  = r["feed_interval"] or 7
            self.tree.insert("","end", iid=r["id"],
                values=(r["id"], r["name"] or "", r["sex"] or "",
                        r["morph"] or "", r["het"] or "",
                        r["rack"] or "", r["weight_g"] or "",
                        f"{fi}d", r["status"] or ""),
                tags=(tag,))

    def _search(self):
        q = self.search_var.get().lower()
        if not q: self._populate(self._all_rows); return
        self._populate([r for r in self._all_rows
                        if q in str(r["id"]).lower() or
                           q in str(r["name"] or "").lower() or
                           q in str(r["morph"] or "").lower() or
                           q in str(r["het"] or "").lower()])

    def _selected_id(self):
        sel = self.tree.selection()
        return sel[0] if sel else None

    def _add(self):  self._open_form(None)

    def _edit(self):
        aid = self._selected_id()
        if not aid:
            messagebox.showinfo("Select", "Select an animal first.")
            return
        self._open_form(aid)

    def _delete(self):
        aid = self._selected_id()
        if not aid: return
        if confirm_delete(f"animal '{aid}'"):
            db.delete_animal(aid)
            self.load(); self.app.refresh_all()

    def _open_form(self, aid):
        is_new  = (aid is None)
        existing = {}
        if not is_new:
            row = db.get_animal(aid)
            if row:
                # Convert every value to string so form widgets work correctly
                existing = {k: str(row[k]) if row[k] is not None else ""
                            for k in row.keys()}

        def on_save(data, win):
            if not data.get("id"):
                messagebox.showerror("Required", "ID is required.", parent=win)
                return
            try:
                db.save_animal(data, is_new=is_new)
                win.destroy()
                self.load(); self.app.refresh_all()
            except Exception as e:
                messagebox.showerror("Save Error", str(e), parent=win)

        open_form(self, f"{'Add' if is_new else 'Edit'} Animal",
                  FIELDS, existing, on_save=on_save)
