"""Hatchlings tab — smart ID generation from clutch."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import database as db
from ui_helpers import C, make_tree, toolbar_frame, btn, open_form, \
                       confirm_delete, STATUS_TAG

FIELDS = [
    ("Hatchling ID *",       "id",             "entry"),
    ("Clutch ID *",          "clutch_id",      "entry"),
    ("Hatch Date",           "hatch_date",     "entry"),
    ("Birth Weight (g)",     "birth_weight_g", "entry"),
    ("Sex",                  "sex",            "combo", ["","Male","Female","Unknown"]),
    ("Confirmed Morph",      "confirmed_morph","entry"),
    ("Possible Morph",       "possible_morph", "entry"),
    ("Het / Carrier Genes",  "het_genes",      "entry"),
    ("First Shed Date",      "first_shed",     "entry"),
    ("First Successful Feed","first_feed",     "entry"),
    ("Prey Offered (g)",     "prey_offered_g", "entry"),
    ("Status *",             "status",         "combo",
     ["Available","Reserved","Holdback","Sold","Deceased"]),
    ("Sale Price (€)",       "sale_price",     "entry"),
    ("Buyer Name",           "buyer_name",     "entry"),
    ("Buyer Contact",        "buyer_contact",  "entry"),
    ("Sale Date",            "sale_date",      "entry"),
    ("Paid?",                "paid",           "combo", ["","Yes","No","Partial"]),
    ("Notes",                "notes",          "text"),
]

COLS   = ("ID","Clutch","Hatch Date","Weight","Sex","Morph","Status",
          "Price","Buyer","Sale Date","Paid?")
WIDTHS = (130,100,100,70,70,180,90,70,130,100,60)

class HatchlingsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        tb = toolbar_frame(self)
        btn(tb, "＋  Add",    self._add, accent=True)
        btn(tb, "✏  Edit",    self._edit)
        btn(tb, "🗑  Delete",  self._delete)
        btn(tb, "↻  Refresh", self.load)

        tk.Label(tb, text="  Status:", bg=C["sidebar"],
                 fg=C["text_dim"], font=("Segoe UI",9)).pack(side="left")
        self.status_var = tk.StringVar(value="All")
        ttk.Combobox(tb, textvariable=self.status_var, width=12, state="readonly",
                     values=["All","Available","Reserved","Holdback","Sold","Deceased"]
                    ).pack(side="left", padx=4, pady=8)
        self.status_var.trace_add("write", lambda *a: self.load())

        tk.Label(tb, text="  Clutch:", bg=C["sidebar"],
                 fg=C["text_dim"], font=("Segoe UI",9)).pack(side="left")
        self.clutch_var = tk.StringVar(value="All")
        self.clutch_cb  = ttk.Combobox(tb, textvariable=self.clutch_var,
                                       width=16, state="readonly")
        self.clutch_cb.pack(side="left", padx=4)
        self.clutch_cb.bind("<<ComboboxSelected>>", lambda e: self.load())

        tk.Label(tb, text="  Search:", bg=C["sidebar"],
                 fg=C["text_dim"], font=("Segoe UI",9)).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._search())
        ttk.Entry(tb, textvariable=self.search_var, width=16).pack(side="left", padx=4)

        frame, self.tree = make_tree(self, COLS, WIDTHS)
        frame.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self.tree.bind("<Double-1>", lambda e: self._edit())
        self._all_rows = []
        self.load()

    def load(self):
        cids = ["All"] + db.get_clutch_ids()
        self.clutch_cb["values"] = cids

        cid  = self.clutch_var.get()
        rows = db.get_hatchlings(cid if cid != "All" else None)
        st   = self.status_var.get()
        if st != "All":
            rows = [r for r in rows if r["status"] == st]
        self._all_rows = rows
        self._populate(rows)

    def _populate(self, rows):
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            morph = " | ".join(filter(None,[r["confirmed_morph"],r["possible_morph"]]))
            tag   = STATUS_TAG.get(r["status"],"even")
            self.tree.insert("","end", iid=r["id"],
                values=(r["id"], r["clutch_id"] or "",
                        r["hatch_date"] or "", r["birth_weight_g"] or "",
                        r["sex"] or "", morph, r["status"] or "",
                        f"€{float(r['sale_price']):.0f}" if r["sale_price"] else "",
                        r["buyer_name"] or "", r["sale_date"] or "",
                        r["paid"] or ""),
                tags=(tag,))

    def _search(self):
        q = self.search_var.get().lower()
        if not q: self._populate(self._all_rows); return
        self._populate([r for r in self._all_rows
                        if q in str(r["id"]).lower() or
                           q in str(r["confirmed_morph"] or "").lower() or
                           q in str(r["buyer_name"] or "").lower()])

    def _selected_id(self):
        sel = self.tree.selection()
        return sel[0] if sel else None

    def _add(self):  self._open_form(None)
    def _edit(self):
        hid = self._selected_id()
        if not hid: messagebox.showinfo("Select","Select a hatchling first."); return
        self._open_form(hid)
    def _delete(self):
        hid = self._selected_id()
        if not hid: return
        if confirm_delete(f"hatchling '{hid}'"):
            db.delete_hatchling(hid); self.load()

    def _open_form(self, hid):
        is_new   = (hid is None)
        existing = {"status":"Available"}

        if not is_new:
            row = db.fetchone("SELECT * FROM hatchlings WHERE id=?", (hid,))
            if row:
                existing = {k: str(row[k]) if row[k] is not None else ""
                            for k in row.keys()}
        else:
            # Pre-fill clutch_id from current filter, auto-generate ID
            cid = self.clutch_var.get()
            if cid and cid != "All":
                next_num = db.next_hatchling_id(cid)
                existing["clutch_id"] = cid
                existing["id"]        = f"{cid}-{next_num}"
                # Pre-fill sire/dam from clutch
                clutch = db.get_clutch(cid)
                if clutch:
                    existing["sire_id"]    = clutch["sire_id"] or ""
                    existing["dam_id"]     = clutch["dam_id"]  or ""
                    existing["hatch_date"] = clutch["hatch_date_actual"] or ""

        # Show ID-generation helper when adding
        if is_new:
            self._show_id_helper(existing)
            return

        self._open_main_form(existing, hid)

    def _show_id_helper(self, prefill):
        """Step 1: Pick clutch + enter hatchling number → generate ID."""
        win = tk.Toplevel(self)
        win.title("New Hatchling — Set ID")
        win.configure(bg=C["bg"]); win.grab_set()
        win.geometry("400x240"); win.resizable(False,False)

        tk.Label(win, text="Clutch ID:", bg=C["bg"], fg=C["text_dim"],
                 font=("Segoe UI",9)).grid(row=0,column=0,sticky="w",padx=16,pady=(20,4))
        cids     = db.get_clutch_ids()
        cid_var  = tk.StringVar(value=prefill.get("clutch_id",""))
        cid_cb   = ttk.Combobox(win, textvariable=cid_var, values=cids,
                                state="readonly", width=26)
        cid_cb.grid(row=0,column=1,sticky="ew",padx=(0,16),pady=(20,4))

        tk.Label(win, text="Hatchling # (-1 = auto):", bg=C["bg"],
                 fg=C["text_dim"], font=("Segoe UI",9)
                ).grid(row=1,column=0,sticky="w",padx=16,pady=4)
        num_var = tk.StringVar(value="")
        ttk.Entry(win, textvariable=num_var, width=10).grid(
            row=1,column=1,sticky="w",padx=(0,16),pady=4)

        preview_var = tk.StringVar(value="")
        tk.Label(win, text="Snake ID will be:", bg=C["bg"],
                 fg=C["text_dim"], font=("Segoe UI",9)
                ).grid(row=2,column=0,sticky="w",padx=16,pady=4)
        tk.Label(win, textvariable=preview_var, bg=C["bg"],
                 fg=C["accent"], font=("Segoe UI",11,"bold")
                ).grid(row=2,column=1,sticky="w",padx=(0,16))

        def _update_preview(*_):
            cid = cid_var.get()
            n   = num_var.get().strip()
            if not cid: preview_var.set("—"); return
            if n == "":
                n = str(db.next_hatchling_id(cid))
            preview_var.set(f"{cid}{n}")
        cid_var.trace_add("write", _update_preview)
        num_var.trace_add("write", _update_preview)
        _update_preview()
        win.columnconfigure(1,weight=1)

        def proceed():
            cid = cid_var.get()
            n   = num_var.get().strip()
            if not cid: messagebox.showerror("Required","Select a Clutch ID.",parent=win); return
            if n == "":
                n = str(db.next_hatchling_id(cid))
            snake_id = f"{cid}{n}"
            # Check duplicate
            if db.fetchone("SELECT id FROM hatchlings WHERE id=?", (snake_id,)):
                messagebox.showerror("Duplicate",
                    f"ID '{snake_id}' already exists.",parent=win); return
            win.destroy()
            # Build prefill for main form
            pf = dict(prefill)
            pf["id"]       = snake_id
            pf["clutch_id"]= cid
            clutch = db.get_clutch(cid)
            if clutch:
                pf.setdefault("sire_id",    clutch["sire_id"] or "")
                pf.setdefault("dam_id",     clutch["dam_id"]  or "")
                pf.setdefault("hatch_date", clutch["hatch_date_actual"] or "")
            self._open_main_form(pf, None)

        ttk.Button(win, text="Continue →", command=proceed,
                   style="Accent.TButton").grid(row=3,column=0,columnspan=2,pady=16)

    def _open_main_form(self, existing, hid):
        is_new = (hid is None)
        def on_save(data, win):
            if not data.get("id"):
                messagebox.showerror("Required","Hatchling ID is required.",parent=win); return
            try:
                db.save_hatchling(data, is_new=is_new)
                win.destroy(); self.load()
                self.app.tab_dash.load()
            except Exception as e:
                messagebox.showerror("Save Error",str(e),parent=win)
        open_form(self,"Hatchling",FIELDS,existing,on_save=on_save)
