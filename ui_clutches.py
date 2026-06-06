"""Clutch Management"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta
import database as db
from ui_helpers import C, make_tree, toolbar_frame, btn, open_form, confirm_delete, STATUS_TAG

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
COLS   = ("Clutch ID","Season","Sire","Dam","Lay Date","Eggs","Good","Slugs",
          "Est. Hatch","Hatchlings","Status")
WIDTHS = (110,70,130,130,100,55,55,55,105,80,100)

class ClutchTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        tb = toolbar_frame(self)
        btn(tb, "＋  Add Clutch",     self._add,             accent=True)
        btn(tb, "✏  Edit",            self._edit)
        btn(tb, "🐣  Add Hatchlings", self._add_hatchlings)
        btn(tb, "🗑  Delete",          self._delete)
        btn(tb, "↻  Refresh",         self.load)

        tk.Label(tb, text="  Status:", bg=C["sidebar"],
                 fg=C["text_dim"], font=("Segoe UI",9)).pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        ttk.Combobox(tb, textvariable=self.filter_var, width=13, state="readonly",
                     values=["All","Pairing","Gravid","Incubating","Hatched","Failed"]
                    ).pack(side="left", padx=4, pady=8)
        self.filter_var.trace_add("write", lambda *a: self.load())

        frame, self.tree = make_tree(self, COLS, WIDTHS)
        frame.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self.tree.bind("<Double-1>", lambda e: self._edit())
        self.load()

    def load(self):
        rows = db.get_all_clutches()
        filt = self.filter_var.get()
        if filt != "All": rows = [r for r in rows if r["status"]==filt]
        self.tree.delete(*self.tree.get_children())
        for i,r in enumerate(rows):
            est = ""
            if r["lay_date"]:
                try: est = str(date.fromisoformat(r["lay_date"])+timedelta(days=55))
                except: pass
            sire = f"{r['sire_id'] or ''} {r['sire_name'] or ''}".strip()
            dam  = f"{r['dam_id']  or ''} {r['dam_name']  or ''}".strip()
            tag  = STATUS_TAG.get(r["status"],"even" if i%2==0 else "odd")
            self.tree.insert("","end", iid=r["id"],
                values=(r["id"],r["season"] or "",sire,dam,
                        r["lay_date"] or "",r["total_eggs"] or "",
                        r["good_eggs"] or "",r["slugs"] or "",
                        r["hatch_date_actual"] or est,
                        r["hatchling_count"] or "",r["status"] or ""),
                tags=(tag,))

    def _selected_id(self):
        sel = self.tree.selection()
        return sel[0] if sel else None

    def _add(self):  self._open_form(None)
    def _edit(self):
        cid = self._selected_id()
        if not cid: messagebox.showinfo("Select","Select a clutch first."); return
        self._open_form(cid)
    def _delete(self):
        cid = self._selected_id()
        if not cid: return
        if confirm_delete(f"clutch '{cid}'"): db.delete_clutch(cid); self.load()

    def _add_hatchlings(self):
        cid = self._selected_id()
        if not cid: messagebox.showinfo("Select","Select a clutch first."); return
        clutch = db.get_clutch(cid)
        if not clutch: return
        count = clutch["hatchling_count"] or clutch["good_eggs"] or 0
        if not count:
            messagebox.showinfo("Info","Set Hatchling Count on the clutch first."); return
        existing = {h["id"] for h in db.get_hatchlings(cid)}
        added = 0
        for i in range(1, int(count)+1):
            hid = f"{cid}-{i}"
            if hid not in existing:
                db.save_hatchling({
                    "id":hid,"clutch_id":cid,
                    "dam_id":clutch["dam_id"],"sire_id":clutch["sire_id"],
                    "hatch_date":clutch["hatch_date_actual"] or "","status":"Available",
                }, is_new=True)
                added += 1
        messagebox.showinfo("Done",f"Added {added} hatchling record(s) for clutch {cid}.")
        self.app.refresh_all()

    def _open_form(self, cid):
        is_new   = (cid is None)
        existing = {"season":str(date.today().year),"status":"Pairing"}
        if not is_new:
            row = db.get_clutch(cid)
            if row:
                existing = {k: str(row[k]) if row[k] is not None else ""
                            for k in row.keys()}
                for key in ("sire_id","dam_id"):
                    a = db.get_animal(existing.get(key,""))
                    if a: existing[key] = f"{a['id']} – {a['name'] or ''}"

        def on_save(data, win):
            if not data.get("id"):
                messagebox.showerror("Required","Clutch ID is required.",parent=win); return
            data["sire_id"] = db.resolve_combo(data.get("sire_id"))
            data["dam_id"]  = db.resolve_combo(data.get("dam_id"))
            try:
                db.save_clutch(data, is_new=is_new); win.destroy(); self.load()
            except Exception as e:
                messagebox.showerror("Save Error",str(e),parent=win)

        open_form(self,"Clutch",FIELDS,existing,on_save=on_save)
