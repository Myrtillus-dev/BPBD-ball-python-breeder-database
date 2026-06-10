"""
ui_dashboard.py — Dashboard tab with CustomTkinter widgets.

Shows an overview of the collection and quick-action buttons.

PANELS:
  Left:   Feeding Alerts — animals due or overdue for feeding
  Center: Active Clutches — clutches not yet Hatched or Failed
  Right:  Recent Feedings — last 12 feeding log entries

STAT CARDS (top row):
  Active Animals | Active Clutches | For Sale | Total Revenue | Feedings (30d)

QUICK LOG buttons (top bar):
  🍖 Add Feeding  — pick animal, prey type (Rat/Mice/Other), weight, fed yes/no
  ⚖ Add Weight   — pick animal, enter weight (Enter key saves)
  🐍 Log Shed     — pick animal, complete yes/no, optional notes

All quick-log saves call sync.after_husbandry_save() to propagate
weight updates to Animal Profiles automatically.

Auto-refreshes every 30 seconds.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import customtkinter as ctk
import database as db
from ui_helpers import C, tag_tree, section_header


class DashboardTab(ctk.CTkFrame):
    """Main dashboard — overview, alerts and quick-log buttons."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg"])
        self.pack(fill="both", expand=True)
        self.app = app
        self._after_id = None  # holds the after() reference for auto-refresh
        self._build()

    def _build(self):
        """Build quick-action bar, stat cards and three data panels."""

        # ── Quick-action toolbar ──────────────────────────────────────────────
        qbar = ctk.CTkFrame(self, fg_color=C["sidebar"], height=52, corner_radius=8)
        qbar.pack(fill="x", padx=10, pady=(10, 4))
        qbar.pack_propagate(False)

        ctk.CTkLabel(qbar, text="Quick Log:",
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["text_dim"]
                    ).pack(side="left", padx=(12, 4), pady=10)

        for text, cmd, color in [
            ("🍖  Add Feeding",  self._quick_feed,   C["accent_dim"]),
            ("⚖  Add Weight",   self._quick_weight, C["card2"]),
            ("🐍  Log Shed",     self._quick_shed,   C["card2"]),
        ]:
            ctk.CTkButton(qbar, text=text, command=cmd,
                          width=140, height=34, corner_radius=6,
                          fg_color=color, hover_color=C["accent"],
                          text_color="#ffffff",
                          font=ctk.CTkFont("Segoe UI", 10, "bold")
                         ).pack(side="left", padx=6, pady=9)

        ctk.CTkButton(qbar, text="↻  Refresh", command=self.load,
                      width=90, height=34, corner_radius=6,
                      fg_color=C["card2"], hover_color=C["accent"],
                      text_color=C["text"],
                      border_width=1, border_color=C["border"],
                      font=ctk.CTkFont("Segoe UI", 10)
                     ).pack(side="right", padx=10, pady=9)

        # Last refresh timestamp label
        self._clock_lbl = ctk.CTkLabel(qbar, text="",
                                       font=ctk.CTkFont("Segoe UI", 8),
                                       text_color=C["text_dim"])
        self._clock_lbl.pack(side="right", padx=4)

        # ── Stat cards row ────────────────────────────────────────────────────
        card_row = ctk.CTkFrame(self, fg_color=C["bg"])
        card_row.pack(fill="x", padx=12, pady=(4, 8))
        for i in range(5):
            card_row.columnconfigure(i, weight=1)

        self._cards = {}
        for col, (key, title, color) in enumerate([
            ("total_active",    "Active Animals",    C["accent"]),
            ("active_clutches", "Active Clutches",   C["gold"]),
            ("available",       "For Sale",          C["gold"]),
            ("sold_revenue",    "Total Revenue (€)", C["accent"]),
            ("feed_30",         "Feedings (30d)",    C["blue"]),
        ]):
            f = ctk.CTkFrame(card_row, fg_color=C["card"],
                             corner_radius=10, border_width=1,
                             border_color=C["border"])
            f.grid(row=0, column=col, padx=5, pady=4, sticky="nsew")
            card_row.rowconfigure(0, weight=1)
            ctk.CTkLabel(f, text=title,
                         font=ctk.CTkFont("Segoe UI", 10),
                         text_color=C["text_dim"]
                        ).pack(anchor="w", padx=12, pady=(10, 2))
            lbl = ctk.CTkLabel(f, text="—",
                               font=ctk.CTkFont("Segoe UI", 26, "bold"),
                               text_color=color)
            lbl.pack(anchor="w", padx=12, pady=(0, 10))
            self._cards[key] = lbl

        # ── Three data panels ─────────────────────────────────────────────────
        panels = tk.Frame(self, bg=C["bg"])
        panels.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        panels.columnconfigure(0, weight=2)
        panels.columnconfigure(1, weight=2)
        panels.columnconfigure(2, weight=2)
        panels.rowconfigure(0, weight=1)

        # Panel 1: Feeding alerts
        p1 = tk.Frame(panels, bg=C["card"])
        p1.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        section_header(p1, "⚠️  Feeding Alerts")
        self.alert_tree = self._mini_tree(p1,
            ("Animal", "Last Fed", "Next Due", "Days", "Status"),
            (120, 100, 100, 50, 130))

        # Panel 2: Active clutches
        p2 = tk.Frame(panels, bg=C["card"])
        p2.grid(row=0, column=1, sticky="nsew", padx=(0, 5))
        section_header(p2, "🥚  Active Clutches")
        self.clutch_tree = self._mini_tree(p2,
            ("Clutch ID", "Sire × Dam", "Lay Date", "Est. Hatch", "Status"),
            (100, 150, 90, 90, 90))

        # Panel 3: Recent feedings
        p3 = tk.Frame(panels, bg=C["card"])
        p3.grid(row=0, column=2, sticky="nsew")
        section_header(p3, "🍖  Recent Feedings")
        self.feed_tree = self._mini_tree(p3,
            ("Animal", "Prey (g)", "Fed?", "Date"),
            (120, 90, 50, 90))

        self.load()

    def _mini_tree(self, parent, cols, widths):
        """Create a small read-only Treeview for dashboard panels."""
        t = ttk.Treeview(parent, columns=cols, show="headings",
                         selectmode="none")
        for col, w in zip(cols, widths):
            t.heading(col, text=col, anchor="w")
            t.column(col, width=w, minwidth=30, anchor="w")
        vsb = ttk.Scrollbar(parent, orient="vertical", command=t.yview)
        t.configure(yscrollcommand=vsb.set)
        t.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)
        vsb.pack(side="right", fill="y", pady=4, padx=(0, 4))
        tag_tree(t)
        return t

    def load(self):
        """
        Reload all dashboard data from database.
        Cancels any pending auto-refresh before scheduling a new one.
        """
        # Cancel pending refresh to avoid stacking
        if self._after_id:
            try:
                self.after_cancel(self._after_id)
            except: pass

        # ── Stat cards ────────────────────────────────────────────────────────
        s = db.get_summary()
        for key, lbl in self._cards.items():
            v = s.get(key, 0)
            lbl.configure(text=f"€{v:,.0f}" if key == "sold_revenue" else str(v))

        # ── Feeding alerts ────────────────────────────────────────────────────
        # get_feeding_alerts() uses per-animal feed_interval
        # Warning shown 3 days before due; overdue shown in orange/red
        self.alert_tree.delete(*self.alert_tree.get_children())
        for a in db.get_feeding_alerts():
            tag  = "overdue" if a["level"] == "overdue" else "warning"
            days = str(a["days_since"]) if a["days_since"] is not None else "?"
            self.alert_tree.insert("", "end",
                values=(f"{a['id']} {a['name'] or ''}",
                        a["last_fed"], a["next_due"], days, a["msg"]),
                tags=(tag,))

        # ── Active clutches ───────────────────────────────────────────────────
        from datetime import timedelta
        self.clutch_tree.delete(*self.clutch_tree.get_children())
        for c in db.get_active_clutches():
            est = ""
            if c["lay_date"]:
                try:
                    est = str(date.fromisoformat(c["lay_date"]) + timedelta(days=55))
                except: pass
            pair    = f"{c['sire_name'] or '?'} × {c['dam_name'] or '?'}"
            hatch_d = c["hatch_date_actual"] or (f"~{est}" if est else "—")
            self.clutch_tree.insert("", "end",
                values=(c["id"], pair, c["lay_date"] or "",
                        hatch_d, c["status"]),
                tags=("available",))

        # ── Recent feedings ───────────────────────────────────────────────────
        self.feed_tree.delete(*self.feed_tree.get_children())
        for r in db.fetchall("""
            SELECT a.name, h.prey_type, h.prey_weight, h.fed, h.date
            FROM husbandry h LEFT JOIN animals a ON h.animal_id=a.id
            WHERE h.event_type='Feeding'
            ORDER BY h.date DESC, h.id DESC LIMIT 12"""):
            prey = f"{r['prey_type'] or ''} {r['prey_weight'] or ''}".strip()
            tag  = ("hatched" if r["fed"] == "Yes"
                    else "deceased" if r["fed"] == "No" else "even")
            self.feed_tree.insert("", "end",
                values=(r["name"] or "", prey, r["fed"] or "", r["date"]),
                tags=(tag,))

        self._clock_lbl.configure(text=f"Updated: {date.today()}")
        # Schedule next auto-refresh in 30 seconds
        self._after_id = self.after(30000, self.load)

    # ── Quick log helpers ─────────────────────────────────────────────────────

    def _pick_animal(self, title):
        """
        Small popup to select an active animal.
        Returns the animal ID string, or None if cancelled.
        """
        ids = db.get_animal_ids()
        if not ids:
            messagebox.showinfo("No Animals", "Add animals first.")
            return None
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.configure(fg_color=C["bg"])
        win.grab_set()
        win.geometry("340x150")
        win.resizable(False, False)
        ctk.CTkLabel(win, text="Animal:",
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["text_dim"]).pack(pady=(16, 4))
        var = tk.StringVar(value=ids[0])
        ctk.CTkComboBox(win, variable=var, values=ids,
                        width=280, height=36, state="readonly",
                        fg_color=C["entry"], border_color=C["border"],
                        button_color=C["card2"], text_color=C["text"],
                        dropdown_fg_color=C["card"], dropdown_text_color=C["text"]
                       ).pack(pady=4)
        result = [None]
        def ok():
            result[0] = db.resolve_combo(var.get())
            win.destroy()
        ctk.CTkButton(win, text="OK", command=ok,
                      width=100, height=34, corner_radius=6,
                      fg_color=C["accent_dim"], hover_color=C["accent"],
                      text_color="#ffffff"
                     ).pack(pady=10)
        win.wait_window()
        return result[0]

    def _date_row(self, parent, row):
        """
        Reusable date input row for quick-log popups.
        Pre-filled with today's date. Returns the StringVar.
        """
        ctk.CTkLabel(parent, text="Date:", anchor="w",
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["text_dim"]
                    ).grid(row=row, column=0, sticky="w", padx=16, pady=6)
        var = tk.StringVar(value=str(date.today()))
        ctk.CTkEntry(parent, textvariable=var, width=140, height=36,
                     fg_color=C["entry"], border_color=C["border"],
                     text_color=C["text"]
                    ).grid(row=row, column=1, sticky="w", padx=(0, 16), pady=6)
        ctk.CTkLabel(parent, text="YYYY-MM-DD",
                     font=ctk.CTkFont("Segoe UI", 8),
                     text_color=C["text_dim"]
                    ).grid(row=row, column=2, sticky="w", pady=6)
        return var

    def _quick_feed(self):
        """
        Quick feeding log popup.
        Prey Type: Rat / Mice / Other (combo, matches husbandry form)
        Fed?: Yes / No only — no Partial (ball pythons eat fully or refuse)
        Saves via save_husbandry() + sync.after_husbandry_save()
        """
        aid = self._pick_animal("Quick — Add Feeding")
        if not aid:
            return
        win = ctk.CTkToplevel(self)
        win.title("Add Feeding")
        win.configure(fg_color=C["bg"])
        win.grab_set()
        win.geometry("420x330")
        win.resizable(False, False)
        win.columnconfigure(1, weight=1)

        date_var = self._date_row(win, 0)

        # Fields match ui_husbandry.py:
        # Prey Type = combo (Rat/Mice/Other), Fed? = Yes/No only
        fields = [
            ("Prey Type",       "prey_type",  "combo", "Rat",  ["Rat","Mice","Other"]),
            ("Prey Weight (g)", "prey_weight","entry",  "",    []),
            ("Fed?",            "fed",        "combo", "Yes",  ["Yes","No"]),
            ("Notes",           "notes",      "entry",  "",    []),
        ]
        vars_ = {}
        for i, (lbl, key, ftype, default, opts) in enumerate(fields, 1):
            ctk.CTkLabel(win, text=lbl, anchor="w",
                         font=ctk.CTkFont("Segoe UI", 10),
                         text_color=C["text_dim"]
                        ).grid(row=i, column=0, sticky="w", padx=16, pady=6)
            v = tk.StringVar(value=default)
            if ftype == "combo":
                w = ctk.CTkComboBox(win, variable=v, values=opts,
                                    width=220, height=36, state="readonly",
                                    fg_color=C["entry"], border_color=C["border"],
                                    button_color=C["card2"], text_color=C["text"],
                                    dropdown_fg_color=C["card"],
                                    dropdown_text_color=C["text"])
            else:
                w = ctk.CTkEntry(win, textvariable=v, width=220, height=36,
                                 fg_color=C["entry"], border_color=C["border"],
                                 text_color=C["text"])
            w.grid(row=i, column=1, sticky="ew", padx=(0, 16), pady=6)
            vars_[key] = v

        def save():
            data = {
                "date":        date_var.get().strip() or str(date.today()),
                "animal_id":   aid,
                "event_type":  "Feeding",
                "prey_type":   vars_["prey_type"].get() or None,
                "prey_weight": vars_["prey_weight"].get() or None,
                "fed":         vars_["fed"].get() or None,
                "notes":       vars_["notes"].get() or None,
            }
            db.save_husbandry(data)
            import sync; sync.after_husbandry_save(data)
            win.destroy()
            self.load()
            self.app.tab_husbandry.load()
            self.app.tab_animals.load()

        ctk.CTkButton(win, text="💾  Save Feeding", command=save,
                      width=160, height=36, corner_radius=6,
                      fg_color=C["accent_dim"], hover_color=C["accent"],
                      text_color="#ffffff",
                      font=ctk.CTkFont("Segoe UI", 11, "bold")
                     ).grid(row=len(fields)+1, column=0, columnspan=3, pady=16)

    def _quick_weight(self):
        """
        Quick weight entry popup.
        Enter key triggers save.
        Syncs to animals.weight_g via sync.after_husbandry_save().
        """
        aid = self._pick_animal("Quick — Add Weight")
        if not aid:
            return
        win = ctk.CTkToplevel(self)
        win.title("Add Weight")
        win.configure(fg_color=C["bg"])
        win.grab_set()
        win.geometry("340x190")
        win.resizable(False, False)
        win.columnconfigure(1, weight=1)

        date_var = self._date_row(win, 0)

        ctk.CTkLabel(win, text="Weight (g):", anchor="w",
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["text_dim"]
                    ).grid(row=1, column=0, sticky="w", padx=16, pady=6)
        wvar = tk.StringVar()
        e = ctk.CTkEntry(win, textvariable=wvar, width=160, height=36,
                         fg_color=C["entry"], border_color=C["border"],
                         text_color=C["text"],
                         font=ctk.CTkFont("Segoe UI", 14))
        e.grid(row=1, column=1, sticky="w", padx=(0, 16), pady=6)
        e.focus()

        def save():
            w = wvar.get().strip()
            if not w:
                return
            wdata = {
                "date":       date_var.get().strip() or str(date.today()),
                "animal_id":  aid,
                "event_type": "Weight Check",
                "weight_g":   w,
            }
            db.save_husbandry(wdata)
            import sync; sync.after_husbandry_save(wdata)
            win.destroy()
            self.load()
            self.app.tab_husbandry.load()
            self.app.tab_animals.load()

        win.bind("<Return>", lambda e: save())
        ctk.CTkButton(win, text="💾  Save", command=save,
                      width=120, height=36, corner_radius=6,
                      fg_color=C["accent_dim"], hover_color=C["accent"],
                      text_color="#ffffff"
                     ).grid(row=2, column=0, columnspan=3, pady=14)

    def _quick_shed(self):
        """
        Quick shed log popup.
        Records complete/partial shed and optional notes.
        """
        aid = self._pick_animal("Quick — Log Shed")
        if not aid:
            return
        win = ctk.CTkToplevel(self)
        win.title("Log Shed")
        win.configure(fg_color=C["bg"])
        win.grab_set()
        win.geometry("360x230")
        win.resizable(False, False)
        win.columnconfigure(1, weight=1)

        date_var = self._date_row(win, 0)

        ctk.CTkLabel(win, text="Complete shed?", anchor="w",
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["text_dim"]
                    ).grid(row=1, column=0, sticky="w", padx=16, pady=6)
        svar = tk.StringVar(value="Yes")
        ctk.CTkComboBox(win, variable=svar, values=["Yes", "No"],
                        width=160, height=36, state="readonly",
                        fg_color=C["entry"], border_color=C["border"],
                        button_color=C["card2"], text_color=C["text"],
                        dropdown_fg_color=C["card"], dropdown_text_color=C["text"]
                       ).grid(row=1, column=1, sticky="w", padx=(0, 16), pady=6)

        ctk.CTkLabel(win, text="Notes:", anchor="w",
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["text_dim"]
                    ).grid(row=2, column=0, sticky="w", padx=16, pady=6)
        nvar = tk.StringVar()
        ctk.CTkEntry(win, textvariable=nvar, width=220, height=36,
                     fg_color=C["entry"], border_color=C["border"],
                     text_color=C["text"]
                    ).grid(row=2, column=1, sticky="ew", padx=(0, 16), pady=6)

        def save():
            d = date_var.get().strip() or str(date.today())
            db.save_husbandry({
                "date":          d,
                "animal_id":     aid,
                "event_type":    "Shed",
                "complete_shed": svar.get(),
                "shed_date":     d,
                "notes":         nvar.get() or None,
            })
            win.destroy()
            self.load()
            self.app.tab_husbandry.load()
            self.app.tab_animals.load()

        ctk.CTkButton(win, text="💾  Save Shed", command=save,
                      width=140, height=36, corner_radius=6,
                      fg_color=C["accent_dim"], hover_color=C["accent"],
                      text_color="#ffffff"
                     ).grid(row=3, column=0, columnspan=3, pady=14)
