"""
ui_hatchlings.py — Hatchling Records tab with CustomTkinter toolbar.

Tracks every hatchling from hatch to sale or holdback.

KEY FEATURE — Holdback auto-sync:
  When status is set to Holdback and saved, sync.after_hatchling_save()
  automatically creates an Animal Profile with the hatchling's basic data:
    ID, name (= hatchling ID initially), morph, het, sex, dob, sire/dam.
  The breeder can then go to Animals tab to rename and fill in more details.
  If the animal profile already exists, only missing fields are updated.

Hatchling ID format:
  Step 1 popup asks for Clutch ID + suffix.
  Suffix is appended directly: "26MYR1" + "AA" = "26MYR1AA"
                               "26MYR1" + "-1" = "26MYR1-1"
  Empty suffix = auto number (next available integer for that clutch).
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import customtkinter as ctk
import database as db
from ui_helpers import C, make_tree, toolbar_frame, btn, open_form, \
                       confirm_delete, STATUS_TAG

# ── Form field definitions ────────────────────────────────────────────────────
FIELDS = [
    ("Hatchling ID *",        "id",             "entry"),
    ("Clutch ID *",           "clutch_id",      "entry"),
    ("Hatch Date",            "hatch_date",     "entry"),
    ("Birth Weight (g)",      "birth_weight_g", "entry"),
    ("Sex",                   "sex",            "combo", ["","Male","Female","Unknown"]),
    ("Confirmed Morph",       "confirmed_morph","entry"),
    ("Possible Morph",        "possible_morph", "entry"),
    ("Het / Carrier Genes",   "het_genes",      "entry"),
    ("First Shed Date",       "first_shed",     "entry"),
    ("First Successful Feed", "first_feed",     "entry"),
    ("Prey Offered (g)",      "prey_offered_g", "entry"),
    ("Status *",              "status",         "combo",
     ["Available","Reserved","Holdback","Sold","Deceased"]),
    ("Sale Price (€)",        "sale_price",     "entry"),
    ("Buyer Name",            "buyer_name",     "entry"),
    ("Buyer Contact",         "buyer_contact",  "entry"),
    ("Sale Date",             "sale_date",      "entry"),
    ("Paid?",                 "paid",           "combo", ["","Yes","No"]),
    ("Notes",                 "notes",          "text"),
]

# ── Treeview columns ──────────────────────────────────────────────────────────
COLS   = ("ID","Clutch","Hatch Date","Weight","Sex","Morph","Status",
          "Price","Buyer","Sale Date","Paid?")
WIDTHS = (130, 100, 100, 70, 70, 180, 90, 70, 130, 100, 60)


class HatchlingsTab(ctk.CTkFrame):
    """Hatchling Records tab — per-hatchling tracking from hatch to sale."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg"])
        self.pack(fill="both", expand=True)
        self.app = app
        self._build()

    def _build(self):
        """Build toolbar with status/clutch filters, search box and treeview."""
        # ── Toolbar ───────────────────────────────────────────────────────────
        tb = toolbar_frame(self)
        btn(tb, "＋  Add",    self._add, accent=True)
        btn(tb, "✏  Edit",    self._edit)
        btn(tb, "🗑  Delete",  self._delete)
        btn(tb, "↻  Refresh", self.load)

        # Status filter
        ctk.CTkLabel(tb, text="  Status:", font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["text_dim"]).pack(side="left")
        self.status_var = tk.StringVar(value="All")
        ctk.CTkComboBox(tb, variable=self.status_var, width=130, height=36,
                        state="readonly",
                        values=["All","Available","Reserved","Holdback","Sold","Deceased"],
                        fg_color=C["entry"], border_color=C["border"],
                        button_color=C["card2"], text_color=C["text"],
                        dropdown_fg_color=C["card"], dropdown_text_color=C["text"],
                        command=lambda _: self.load()
                       ).pack(side="left", padx=4, pady=9)

        # Clutch filter — populated dynamically from database
        ctk.CTkLabel(tb, text="  Clutch:", font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["text_dim"]).pack(side="left")
        self.clutch_var = tk.StringVar(value="All")
        self.clutch_cb  = ctk.CTkComboBox(tb, variable=self.clutch_var,
                                          width=160, height=36, state="readonly",
                                          fg_color=C["entry"], border_color=C["border"],
                                          button_color=C["card2"], text_color=C["text"],
                                          dropdown_fg_color=C["card"],
                                          dropdown_text_color=C["text"],
                                          command=lambda _: self.load())
        self.clutch_cb.pack(side="left", padx=4)

        # Search box
        ctk.CTkLabel(tb, text="  Search:", font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["text_dim"]).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._search())
        ctk.CTkEntry(tb, textvariable=self.search_var, width=160, height=36,
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
        """
        Reload hatchlings.
        Refreshes clutch filter dropdown.
        Applies status and clutch filters.
        """
        # Refresh clutch dropdown
        cids = ["All"] + db.get_clutch_ids()
        self.clutch_cb.configure(values=cids)

        cid  = self.clutch_var.get()
        rows = db.get_hatchlings(cid if cid != "All" else None)

        # Apply status filter
        st = self.status_var.get()
        if st != "All":
            rows = [r for r in rows if r["status"] == st]

        self._all_rows = rows
        self._populate(rows)

    def _populate(self, rows):
        """Fill treeview with given rows, color-coded by status."""
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            # Combine confirmed and possible morph for display
            morph = " | ".join(filter(None, [r["confirmed_morph"], r["possible_morph"]]))
            tag   = STATUS_TAG.get(r["status"], "even")
            self.tree.insert("", "end", iid=r["id"],
                values=(r["id"], r["clutch_id"] or "",
                        r["hatch_date"] or "", r["birth_weight_g"] or "",
                        r["sex"] or "", morph, r["status"] or "",
                        f"€{float(r['sale_price']):.0f}" if r["sale_price"] else "",
                        r["buyer_name"] or "", r["sale_date"] or "",
                        r["paid"] or ""),
                tags=(tag,))

    def _search(self):
        """Filter by hatchling ID, morph or buyer name."""
        q = self.search_var.get().lower()
        if not q:
            self._populate(self._all_rows)
            return
        self._populate([r for r in self._all_rows
                        if q in str(r["id"]).lower() or
                           q in str(r["confirmed_morph"] or "").lower() or
                           q in str(r["buyer_name"] or "").lower()])

    def _selected_id(self):
        """Return ID of selected hatchling row, or None."""
        sel = self.tree.selection()
        return sel[0] if sel else None

    def _add(self):  self._open_form(None)

    def _edit(self):
        hid = self._selected_id()
        if not hid:
            messagebox.showinfo("Select", "Select a hatchling first.")
            return
        self._open_form(hid)

    def _delete(self):
        hid = self._selected_id()
        if not hid: return
        if confirm_delete(f"hatchling '{hid}'"):
            db.delete_hatchling(hid)
            self.load()

    def _open_form(self, hid):
        """
        For new hatchlings: show ID helper popup first (Step 1).
        For existing hatchlings: open main form directly.
        """
        is_new = (hid is None)
        existing = {"status": "Available"}

        if not is_new:
            # Load existing data
            row = db.fetchone("SELECT * FROM hatchlings WHERE id=?", (hid,))
            if row:
                existing = {k: str(row[k]) if row[k] is not None else ""
                            for k in row.keys()}
        else:
            # Pre-fill from currently selected clutch
            cid = self.clutch_var.get()
            if cid and cid != "All":
                next_num = db.next_hatchling_id(cid)
                existing["clutch_id"] = cid
                existing["id"]        = f"{cid}{next_num}"
                clutch = db.get_clutch(cid)
                if clutch:
                    existing["sire_id"]    = clutch["sire_id"] or ""
                    existing["dam_id"]     = clutch["dam_id"]  or ""
                    existing["hatch_date"] = clutch["hatch_date_actual"] or ""
            # Show ID helper popup before main form
            self._show_id_helper(existing)
            return

        self._open_main_form(existing, hid)

    def _show_id_helper(self, prefill):
        """
        Step 1 popup: pick clutch + type suffix → preview full snake ID.

        Rules:
          - Empty suffix → auto number (next available integer)
          - Suffix appended directly: "26MYR1" + "AA" = "26MYR1AA"
          - Suffix appended directly: "26MYR1" + "-1" = "26MYR1-1"
          - Duplicate IDs are rejected
        """
        win = ctk.CTkToplevel(self)
        win.title("New Hatchling — Set ID")
        win.configure(fg_color=C["bg"])
        win.grab_set()
        win.geometry("440x280")
        win.resizable(False, False)
        win.columnconfigure(1, weight=1)

        # Clutch selector
        ctk.CTkLabel(win, text="Clutch ID:", anchor="w",
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["text_dim"]
                    ).grid(row=0, column=0, sticky="w", padx=16, pady=(20, 6))
        cids    = db.get_clutch_ids()
        cid_var = tk.StringVar(value=prefill.get("clutch_id", ""))
        ctk.CTkComboBox(win, variable=cid_var, values=cids,
                        width=240, height=36, state="readonly",
                        fg_color=C["entry"], border_color=C["border"],
                        button_color=C["card2"], text_color=C["text"],
                        dropdown_fg_color=C["card"], dropdown_text_color=C["text"]
                       ).grid(row=0, column=1, sticky="ew", padx=(0,16), pady=(20,6))

        # Suffix input
        ctk.CTkLabel(win, text="Hatchling suffix\n(empty = auto):", anchor="w",
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["text_dim"], justify="left"
                    ).grid(row=1, column=0, sticky="w", padx=16, pady=6)
        num_var = tk.StringVar(value="")
        ctk.CTkEntry(win, textvariable=num_var, width=140, height=36,
                     fg_color=C["entry"], border_color=C["border"],
                     text_color=C["text"]
                    ).grid(row=1, column=1, sticky="w", padx=(0,16), pady=6)
        ctk.CTkLabel(win, text="e.g. AA → 26MYR1AA  |  -1 → 26MYR1-1",
                     font=ctk.CTkFont("Segoe UI", 9), text_color=C["text_dim"]
                    ).grid(row=1, column=1, sticky="e", padx=(0,16))

        # Live preview of resulting ID
        preview_var = tk.StringVar(value="—")
        ctk.CTkLabel(win, text="Snake ID will be:", anchor="w",
                     font=ctk.CTkFont("Segoe UI", 10), text_color=C["text_dim"]
                    ).grid(row=2, column=0, sticky="w", padx=16, pady=6)
        ctk.CTkLabel(win, textvariable=preview_var,
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color=C["accent"]
                    ).grid(row=2, column=1, sticky="w", padx=(0,16), pady=6)

        def _update(*_):
            """Recalculate preview whenever clutch or suffix changes."""
            cid = cid_var.get()
            n   = num_var.get().strip()
            if not cid:
                preview_var.set("—")
                return
            if n == "":
                n = str(db.next_hatchling_id(cid))
            preview_var.set(f"{cid}{n}")

        cid_var.trace_add("write", _update)
        num_var.trace_add("write", _update)
        _update()

        def proceed():
            """Validate ID and open main form."""
            cid = cid_var.get()
            n   = num_var.get().strip()
            if not cid:
                messagebox.showerror("Required", "Select a Clutch ID.", parent=win)
                return
            if n == "":
                n = str(db.next_hatchling_id(cid))
            snake_id = f"{cid}{n}"
            # Reject duplicate IDs
            if db.fetchone("SELECT id FROM hatchlings WHERE id=?", (snake_id,)):
                messagebox.showerror("Duplicate",
                    f"ID '{snake_id}' already exists.", parent=win)
                return
            win.destroy()
            # Build pre-filled data for main form
            pf = dict(prefill)
            pf["id"] = snake_id
            pf["clutch_id"] = cid
            clutch = db.get_clutch(cid)
            if clutch:
                pf.setdefault("sire_id",    clutch["sire_id"] or "")
                pf.setdefault("dam_id",     clutch["dam_id"]  or "")
                pf.setdefault("hatch_date", clutch["hatch_date_actual"] or "")
            self._open_main_form(pf, None)

        ctk.CTkButton(win, text="Continue →", command=proceed,
                      width=140, height=36, corner_radius=6,
                      fg_color=C["accent_dim"], hover_color=C["accent"],
                      text_color="#ffffff",
                      font=ctk.CTkFont("Segoe UI", 11, "bold")
                     ).grid(row=3, column=0, columnspan=2, pady=18)

    def _open_main_form(self, existing, hid):
        """
        Open main hatchling data entry form.

        After save:
          - sync.after_hatchling_save() creates Animal Profile if Holdback
          - Animals tab and Dashboard are refreshed
          - User shown notification if new animal was created
        """
        is_new = (hid is None)

        def on_save(data, win):
            if not data.get("id"):
                messagebox.showerror("Required", "Hatchling ID is required.", parent=win)
                return
            try:
                db.save_hatchling(data, is_new=is_new)
                # Sync to Animals if Holdback (centralized in sync.py)
                import sync
                created = sync.after_hatchling_save(data)
                win.destroy()
                self.load()
                self.app.tab_animals.load()
                self.app.tab_dash.load()
                if created:
                    messagebox.showinfo("Animal Profile Created",
                        f"'{data['id']}' has been added to Animal Profiles.\n"
                        "Go to Animals tab to update the name and details.")
            except Exception as e:
                messagebox.showerror("Save Error", str(e), parent=win)

        open_form(self, "Hatchling", FIELDS, existing, on_save=on_save)
