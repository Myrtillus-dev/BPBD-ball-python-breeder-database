"""Husbandry Logs"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import database as db
from ui_helpers import C, make_tree, toolbar_frame, btn, open_form, confirm_delete

FIELDS = [
    ("Date (YYYY-MM-DD) *", "date",          "entry"),
    ("Animal *",             "animal_id",     "combo_live"),
    ("Event Type *",         "event_type",    "combo",
     ["Feeding","Weight Check","Shed","Defecation","Cleaning","Medication","Other"]),
    ("Prey Type",            "prey_type",     "entry"),
    ("Prey Weight (g)",      "prey_weight",   "entry"),
    ("Fed?",                 "fed",           "combo", ["","Yes","No","Partial"]),
    ("Refusal Reason",       "refusal_reason","entry"),
    ("Weight (g)",           "weight_g",      "entry"),
    ("Length (cm)",          "length_cm",     "entry"),
    ("In Blue (pre-shed)?",  "in_blue",       "combo", ["","Yes","No"]),
    ("Complete Shed?",       "complete_shed", "combo", ["","Yes","No"]),
    ("Shed Date",            "shed_date",     "entry"),
    ("Defecation?",          "defecation",    "combo", ["","Yes","No"]),
    ("Cleaning Done?",       "cleaning",      "combo", ["","Yes","No"]),
    ("Logged By",            "logged_by",     "entry"),
    ("Notes",                "notes",         "text"),
]
COLS   = ("Date","Animal","Event","Prey type","Prey (g)","Anim.wt(g)","Fed?","Notes")
WIDTHS = (100,130,120,120,70,80,60,200)

class HusbandryTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        tb = toolbar_frame(self)
        btn(tb, "＋  Add Log", self._add, accent=True)
        btn(tb, "✏  Edit",     self._edit)
        btn(tb, "🗑  Delete",   self._delete)
        btn(tb, "↻  Refresh",  self.load)

        tk.Label(tb, text="  Animal:", bg=C["sidebar"],
                 fg=C["text_dim"], font=("Segoe UI",9)).pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        self.filter_cb  = ttk.Combobox(tb, textvariable=self.filter_var,
                                       width=22, state="readonly")
        self.filter_cb.pack(side="left", padx=4, pady=8)
        self.filter_cb.bind("<<ComboboxSelected>>", lambda e: self.load())

        tk.Label(tb, text="  Event:", bg=C["sidebar"],
                 fg=C["text_dim"], font=("Segoe UI",9)).pack(side="left")
        self.event_var = tk.StringVar(value="All")
        ttk.Combobox(tb, textvariable=self.event_var, width=14, state="readonly",
                     values=["All","Feeding","Weight Check","Shed",
                             "Defecation","Cleaning","Medication","Other"]
                    ).pack(side="left", padx=4)
        self.event_var.trace_add("write", lambda *a: self.load())

        frame, self.tree = make_tree(self, COLS, WIDTHS)
        frame.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self.tree.bind("<Double-1>", lambda e: self._edit())
        self.load()

    def load(self):
        ids = ["All"] + db.get_animal_ids()
        self.filter_cb["values"] = ids
        filt = self.filter_var.get()
        aid  = db.resolve_combo(filt) if filt != "All" else None
        rows = db.get_husbandry(aid)
        evt  = self.event_var.get()
        if evt != "All":
            rows = [r for r in rows if r["event_type"] == evt]
        self.tree.delete(*self.tree.get_children())
        for i,r in enumerate(rows):
            name = r["animal_name"] if "animal_name" in r.keys() else r["animal_id"]
            tag  = "deceased" if r["fed"]=="No" else ("even" if i%2==0 else "odd")
            self.tree.insert("","end", iid=str(r["id"]),
                values=(r["date"], name or r["animal_id"],
                        r["event_type"] or "",
                        r["prey_type"] or "",
                        r["prey_weight"] or "",
                        r["weight_g"] or "",
                        r["fed"] or "",
                        r["notes"] or ""),
                tags=(tag,))

    def _selected_id(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def _add(self):  self._open_form(None)
    def _edit(self):
        hid = self._selected_id()
        if not hid: messagebox.showinfo("Select","Select a log entry first."); return
        self._open_form(hid)
    def _delete(self):
        hid = self._selected_id()
        if not hid: return
        if confirm_delete("this log entry"):
            db.delete_husbandry(hid); self.load()

    def _open_form(self, hid):
        is_new   = (hid is None)
        existing = {"date": str(date.today())}
        if not is_new:
            row = db.fetchone("SELECT * FROM husbandry WHERE id=?", (hid,))
            if row:
                existing = {k: str(row[k]) if row[k] is not None else ""
                            for k in row.keys()}
                # Convert animal_id → "ID – Name" for combo_live
                a = db.get_animal(existing.get("animal_id",""))
                if a:
                    existing["animal_id"] = f"{a['id']} – {a['name'] or ''}"

        def on_save(data, win):
            if not data.get("date") or not data.get("animal_id") or not data.get("event_type"):
                messagebox.showerror("Required",
                    "Date, Animal and Event Type are required.", parent=win); return
            data["animal_id"] = db.resolve_combo(data["animal_id"])
            if not is_new: data["id"] = hid
            try:
                db.save_husbandry(data); win.destroy(); self.load()
                self.app.tab_dash.load()
            except Exception as e:
                messagebox.showerror("Save Error", str(e), parent=win)

        open_form(self, "Log Entry", FIELDS, existing, on_save=on_save)
