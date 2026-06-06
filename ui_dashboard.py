"""Dashboard — feeding alerts, active clutches, latest weights, quick-log buttons."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import database as db
from ui_helpers import C, tag_tree, section_header

class DashboardTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._after_id = None
        self._build()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build(self):
        # ── Quick-action bar ─────────────────────────────────────────────────
        qbar = tk.Frame(self, bg=C["sidebar"])
        qbar.pack(fill="x", padx=10, pady=(10,4))
        tk.Label(qbar, text="Quick Log:", bg=C["sidebar"],
                 fg=C["text_dim"], font=("Segoe UI",9)).pack(side="left", padx=(8,4), pady=8)
        for text, cmd in [
            ("🍖  Add Feeding",  self._quick_feed),
            ("⚖  Add Weight",   self._quick_weight),
            ("🐍  Log Shed",     self._quick_shed),
        ]:
            ttk.Button(qbar, text=text, command=cmd,
                       style="Quick.TButton").pack(side="left", padx=6, pady=6)
        ttk.Button(qbar, text="↻  Refresh", command=self.load
                   ).pack(side="right", padx=8, pady=6)
        self._clock_lbl = tk.Label(qbar, text="", bg=C["sidebar"],
                                   fg=C["text_dim"], font=("Segoe UI",8))
        self._clock_lbl.pack(side="right", padx=4)

        # ── Stat cards ────────────────────────────────────────────────────────
        grid = tk.Frame(self, bg=C["bg"])
        grid.pack(fill="x", padx=12, pady=(4,8))
        for i in range(5): grid.columnconfigure(i, weight=1)

        self._cards = {}
        for col,(key,title,color) in enumerate([
            ("total_active",   "Active Animals",    C["accent"]),
            ("active_clutches","Active Clutches",   C["gold"]),
            ("available",      "For Sale",          C["gold"]),
            ("sold_revenue",   "Total Revenue (€)", C["accent"]),
            ("feed_30",        "Feedings (30d)",    C["blue"]),
        ]):
            f = tk.Frame(grid, bg=C["card"], padx=12, pady=10)
            f.grid(row=0, column=col, padx=5, pady=4, sticky="nsew")
            grid.rowconfigure(0, weight=1)
            tk.Label(f, text=title, bg=C["card"], fg=C["text_dim"],
                     font=("Segoe UI",9), anchor="w").pack(anchor="w")
            lbl = tk.Label(f, text="—", bg=C["card"], fg=color,
                           font=("Segoe UI",22,"bold"), anchor="w")
            lbl.pack(anchor="w", pady=(4,0))
            self._cards[key] = lbl

        # ── Main 3-panel area ─────────────────────────────────────────────────
        panels = tk.Frame(self, bg=C["bg"])
        panels.pack(fill="both", expand=True, padx=12, pady=(0,8))
        panels.columnconfigure(0, weight=2)
        panels.columnconfigure(1, weight=2)
        panels.columnconfigure(2, weight=1)
        panels.rowconfigure(0, weight=1)

        # Panel 1 — Feeding alerts
        p1 = tk.Frame(panels, bg=C["card"])
        p1.grid(row=0, column=0, sticky="nsew", padx=(0,6))
        section_header(p1, "⚠️  Feeding Alerts")
        self.alert_tree = self._mini_tree(p1,
            ("Animal","Last Fed","Next Due","Days","Status"),
            (120,100,100,55,130))

        # Panel 2 — Active clutches
        p2 = tk.Frame(panels, bg=C["card"])
        p2.grid(row=0, column=1, sticky="nsew", padx=(0,6))
        section_header(p2, "🥚  Active Clutches")
        self.clutch_tree = self._mini_tree(p2,
            ("Clutch ID","Sire × Dam","Lay Date","Est.Hatch","Status"),
            (100,160,90,90,90))

        # Panel 3 — Recent feedings
        p3 = tk.Frame(panels, bg=C["card"])
        p3.grid(row=0, column=2, sticky="nsew")
        section_header(p3, "🍖  Recent Feedings")
        self.recent_feed_tree = self._mini_tree(p3,
            ("Animal","Prey (g)","Fed?","Date"),
            (110,90,50,90))

        self.load()

    def _mini_tree(self, parent, cols, widths):
        t = ttk.Treeview(parent, columns=cols, show="headings", selectmode="none")
        for col,w in zip(cols,widths):
            t.heading(col, text=col, anchor="w")
            t.column(col, width=w, minwidth=30, anchor="w")
        vsb = ttk.Scrollbar(parent, orient="vertical", command=t.yview)
        t.configure(yscrollcommand=vsb.set)
        t.pack(side="left", fill="both", expand=True, padx=(4,0), pady=4)
        vsb.pack(side="right", fill="y", pady=4, padx=(0,4))
        tag_tree(t)
        return t

    # ── Load ──────────────────────────────────────────────────────────────────
    def load(self):
        if self._after_id:
            try: self.after_cancel(self._after_id)
            except: pass

        # Stats
        s = db.get_summary()
        for key,lbl in self._cards.items():
            v = s.get(key,0)
            lbl.configure(text=f"€{v:,.0f}" if key=="sold_revenue" else str(v))

        # Feeding alerts
        self.alert_tree.delete(*self.alert_tree.get_children())
        for a in db.get_feeding_alerts():
            tag = "overdue" if a["level"]=="overdue" else "warning"
            days = str(a["days_since"]) if a["days_since"] is not None else "?"
            self.alert_tree.insert("","end",
                values=(f"{a['id']} {a['name'] or ''}",
                        a["last_fed"], a["next_due"], days, a["msg"]),
                tags=(tag,))

        # Active clutches
        from datetime import timedelta
        self.clutch_tree.delete(*self.clutch_tree.get_children())
        for c in db.get_active_clutches():
            est = ""
            if c["lay_date"]:
                try: est = str(date.fromisoformat(c["lay_date"]) + timedelta(days=55))
                except: pass
            # Use actual hatch date if set, otherwise show estimate with + prefix
            hatch_disp = c["hatch_date_actual"] or (f"~{est}" if est else "—")
            pair = f"{c['sire_name'] or '?'} × {c['dam_name'] or '?'}"
            self.clutch_tree.insert("","end",
                values=(c["id"], pair, c["lay_date"] or "", hatch_disp, c["status"]),
                tags=("available",))

        # Recent feedings
        self.recent_feed_tree.delete(*self.recent_feed_tree.get_children())
        for i,r in enumerate(db.fetchall("""
            SELECT a.name, h.prey_type, h.prey_weight, h.fed, h.date
            FROM husbandry h LEFT JOIN animals a ON h.animal_id=a.id
            WHERE h.event_type='Feeding'
            ORDER BY h.date DESC, h.id DESC LIMIT 12""")):
            prey = f"{r['prey_type'] or ''} {r['prey_weight'] or ''}".strip()
            tag  = "hatched" if r["fed"]=="Yes" else ("deceased" if r["fed"]=="No" else "even")
            self.recent_feed_tree.insert("","end",
                values=(r["name"] or "", prey, r["fed"] or "", r["date"]),
                tags=(tag,))

        self._clock_lbl.configure(text=f"Updated: {date.today()}")
        self._after_id = self.after(30000, self.load)

    # ── Quick log helpers ─────────────────────────────────────────────────────
    def _pick_animal(self, title):
        """Small popup to pick an animal, returns ID string or None."""
        ids = db.get_animal_ids()
        if not ids:
            messagebox.showinfo("No Animals", "Add animals first.")
            return None
        win = tk.Toplevel(self)
        win.title(title); win.configure(bg=C["bg"]); win.grab_set()
        win.geometry("340x140"); win.resizable(False,False)
        tk.Label(win, text="Animal:", bg=C["bg"], fg=C["text_dim"],
                 font=("Segoe UI",9)).pack(pady=(16,4))
        var = tk.StringVar(value=ids[0])
        cb  = ttk.Combobox(win, textvariable=var, values=ids,
                           state="readonly", width=30)
        cb.pack(pady=4)
        result = [None]
        def ok():
            result[0] = db.resolve_combo(var.get())
            win.destroy()
        ttk.Button(win, text="OK", command=ok,
                   style="Accent.TButton").pack(pady=10)
        win.wait_window()
        return result[0]

    def _date_row(self, parent, row):
        """Reusable date field row for quick log popups."""
        tk.Label(parent, text="Date:", bg=C["bg"], fg=C["text_dim"],
                 font=("Segoe UI",9), anchor="w").grid(
                 row=row, column=0, sticky="w", padx=16, pady=5)
        var = tk.StringVar(value=str(date.today()))
        ttk.Entry(parent, textvariable=var, width=16).grid(
                 row=row, column=1, sticky="w", padx=(0,16), pady=5)
        tk.Label(parent, text="(YYYY-MM-DD)", bg=C["bg"],
                 fg=C["text_dim"], font=("Segoe UI",8)).grid(
                 row=row, column=1, sticky="e", padx=(0,16))
        return var

    def _quick_feed(self):
        aid = self._pick_animal("Quick — Add Feeding")
        if not aid: return
        win = tk.Toplevel(self)
        win.title("Add Feeding"); win.configure(bg=C["bg"]); win.grab_set()
        win.geometry("400x340"); win.resizable(False,False)

        date_var = self._date_row(win, 0)

        fields_info = [
            ("Prey Type",      "prey_type",   "entry",  "Rat"),
            ("Prey Weight (g)","prey_weight", "entry",  ""),
            ("Fed?",           "fed",         "combo",  "Yes"),
            ("Notes",          "notes",       "entry",  ""),
        ]
        vars_ = {}
        for i,(lbl,key,ftype,default) in enumerate(fields_info, 1):
            tk.Label(win, text=lbl, bg=C["bg"], fg=C["text_dim"],
                     font=("Segoe UI",9), anchor="w").grid(
                     row=i, column=0, sticky="w", padx=16, pady=5)
            v = tk.StringVar(value=default)
            if ftype == "combo":
                w = ttk.Combobox(win, textvariable=v,
                                 values=["Yes","No","Partial"],
                                 state="readonly", width=26)
            else:
                w = ttk.Entry(win, textvariable=v, width=28)
            w.grid(row=i, column=1, sticky="ew", padx=(0,16), pady=5)
            vars_[key] = v
        win.columnconfigure(1, weight=1)

        def save():
            d = date_var.get().strip() or str(date.today())
            db.save_husbandry({
                "date": d, "animal_id": aid,
                "event_type": "Feeding",
                "prey_type":   vars_["prey_type"].get() or None,
                "prey_weight": vars_["prey_weight"].get() or None,
                "fed":         vars_["fed"].get() or None,
                "notes":       vars_["notes"].get() or None,
            })
            win.destroy(); self.load()
            self.app.tab_husbandry.load()

        ttk.Button(win, text="💾  Save Feeding", command=save,
                   style="Accent.TButton").grid(
                   row=len(fields_info)+1, column=0, columnspan=2, pady=14)

    def _quick_weight(self):
        aid = self._pick_animal("Quick — Add Weight")
        if not aid: return
        win = tk.Toplevel(self)
        win.title("Add Weight"); win.configure(bg=C["bg"]); win.grab_set()
        win.geometry("340x200"); win.resizable(False,False)

        date_var = self._date_row(win, 0)

        tk.Label(win, text="Weight (g):", bg=C["bg"], fg=C["text_dim"],
                 font=("Segoe UI",9), anchor="w").grid(
                 row=1, column=0, sticky="w", padx=16, pady=5)
        weight_var = tk.StringVar()
        e = ttk.Entry(win, textvariable=weight_var, width=16,
                      font=("Segoe UI",13))
        e.grid(row=1, column=1, sticky="w", padx=(0,16), pady=5)
        e.focus()
        win.columnconfigure(1, weight=1)

        def save():
            w = weight_var.get().strip()
            if not w: return
            d = date_var.get().strip() or str(date.today())
            db.save_husbandry({
                "date": d, "animal_id": aid,
                "event_type": "Weight Check", "weight_g": w,
            })
            win.destroy(); self.load()
            self.app.tab_husbandry.load()

        win.bind("<Return>", lambda e: save())
        ttk.Button(win, text="💾  Save", command=save,
                   style="Accent.TButton").grid(
                   row=2, column=0, columnspan=2, pady=14)

    def _quick_shed(self):
        aid = self._pick_animal("Quick — Log Shed")
        if not aid: return
        win = tk.Toplevel(self)
        win.title("Log Shed"); win.configure(bg=C["bg"]); win.grab_set()
        win.geometry("360x240"); win.resizable(False,False)

        date_var = self._date_row(win, 0)

        tk.Label(win, text="Complete shed?", bg=C["bg"], fg=C["text_dim"],
                 font=("Segoe UI",9), anchor="w").grid(
                 row=1, column=0, sticky="w", padx=16, pady=5)
        shed_var = tk.StringVar(value="Yes")
        ttk.Combobox(win, textvariable=shed_var, values=["Yes","No"],
                     state="readonly", width=16).grid(
                     row=1, column=1, sticky="w", padx=(0,16), pady=5)

        tk.Label(win, text="Notes (optional):", bg=C["bg"], fg=C["text_dim"],
                 font=("Segoe UI",9), anchor="w").grid(
                 row=2, column=0, sticky="w", padx=16, pady=5)
        notes_var = tk.StringVar()
        ttk.Entry(win, textvariable=notes_var, width=26).grid(
                  row=2, column=1, sticky="ew", padx=(0,16), pady=5)
        win.columnconfigure(1, weight=1)

        def save():
            d = date_var.get().strip() or str(date.today())
            db.save_husbandry({
                "date": d, "animal_id": aid,
                "event_type": "Shed",
                "complete_shed": shed_var.get(),
                "shed_date": d,
                "notes": notes_var.get() or None,
            })
            win.destroy(); self.load()
            self.app.tab_husbandry.load()

        ttk.Button(win, text="💾  Save Shed", command=save,
                   style="Accent.TButton").grid(
                   row=3, column=0, columnspan=2, pady=14)
