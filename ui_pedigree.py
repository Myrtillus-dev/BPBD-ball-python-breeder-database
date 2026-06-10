"""
ui_pedigree.py — Pedigree Viewer and CoI Calculator tab.

LEFT PANEL: Pedigree tree canvas
  Draws up to 3 generations of ancestors for any selected animal.
  Color coded: blue = male, pink = female, green = unknown sex.
  Connecting lines show parent-child relationships.

RIGHT PANEL: CoI Calculator (Coefficient of Inbreeding)
  Select Sire and Dam to calculate the CoI using Wright's path
  coefficient method (depth 5 generations).
  CoI ranges:
    0%         = no shared ancestors
    ≤3.125%    = very low, safe
    ≤6.25%     = low, acceptable
    6.25-12.5% = moderate, use caution
    >12.5%     = high, not recommended

  Shared ancestors are listed with ID, name and morph.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import database as db
from ui_helpers import C, tag_tree, section_header


class PedigreeTab(ctk.CTkFrame):
    """Pedigree viewer and CoI calculator tab."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg"])
        self.pack(fill="both", expand=True)
        self.app = app
        self._build()

    def _build(self):
        """Build split pane: pedigree canvas left, CoI calculator right."""
        # Use tk.PanedWindow since CTk has no equivalent
        paned = tk.PanedWindow(self, orient="horizontal",
                               bg=C["bg"], sashwidth=4,
                               sashrelief="flat", bd=0)
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        # ── LEFT: Pedigree canvas ─────────────────────────────────────────────
        left = tk.Frame(paned, bg=C["bg"])
        paned.add(left, minsize=400)
        section_header(left, "🌳  Pedigree Viewer")

        # Animal selector row
        sel = ctk.CTkFrame(left, fg_color=C["bg"], height=46)
        sel.pack(fill="x", padx=8, pady=6)
        sel.pack_propagate(False)
        ctk.CTkLabel(sel, text="Animal:", font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["text_dim"]
                    ).pack(side="left", padx=(4, 6))
        self.ped_var = tk.StringVar()
        self.ped_cb  = ctk.CTkComboBox(sel, variable=self.ped_var,
                                       width=240, height=36, state="readonly",
                                       fg_color=C["entry"], border_color=C["border"],
                                       button_color=C["card2"], text_color=C["text"],
                                       dropdown_fg_color=C["card"],
                                       dropdown_text_color=C["text"])
        self.ped_cb.pack(side="left", padx=(0, 8))
        ctk.CTkButton(sel, text="Show Pedigree",
                      command=self._show_pedigree,
                      width=140, height=34, corner_radius=6,
                      fg_color=C["card2"], hover_color=C["accent"],
                      text_color=C["text"],
                      border_width=1, border_color=C["border"],
                      font=ctk.CTkFont("Segoe UI", 10)
                     ).pack(side="left")

        # Scrollable canvas for pedigree drawing
        wrap = tk.Frame(left, bg=C["bg"])
        wrap.pack(fill="both", expand=True, padx=4)
        self.canvas = tk.Canvas(wrap, bg="#0d1b2a", highlightthickness=0)
        vsb = ttk.Scrollbar(wrap, orient="vertical",   command=self.canvas.yview)
        hsb = ttk.Scrollbar(wrap, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        hsb.pack(side="bottom", fill="x")
        vsb.pack(side="right",  fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # ── RIGHT: CoI calculator ─────────────────────────────────────────────
        right = tk.Frame(paned, bg=C["bg"])
        paned.add(right, minsize=300)
        section_header(right, "🧬  Inbreeding Coefficient (CoI)")

        body = ctk.CTkFrame(right, fg_color=C["bg"])
        body.pack(fill="both", expand=True, padx=12, pady=10)

        # Sire and Dam selectors
        for label, attr in [("Sire (Father):", "sire"), ("Dam (Mother):", "dam")]:
            r = ctk.CTkFrame(body, fg_color=C["bg"])
            r.pack(fill="x", pady=4)
            ctk.CTkLabel(r, text=label, font=ctk.CTkFont("Segoe UI", 10),
                         text_color=C["text_dim"], width=140, anchor="w"
                        ).pack(side="left")
            var = tk.StringVar()
            cb  = ctk.CTkComboBox(r, variable=var, width=220, height=36,
                                  state="readonly",
                                  fg_color=C["entry"], border_color=C["border"],
                                  button_color=C["card2"], text_color=C["text"],
                                  dropdown_fg_color=C["card"],
                                  dropdown_text_color=C["text"])
            cb.pack(side="left")
            setattr(self, f"{attr}_var", var)
            setattr(self, f"{attr}_cb",  cb)

        ctk.CTkButton(body, text="⚡  Calculate CoI",
                      command=self._calc_coi,
                      width=170, height=36, corner_radius=6,
                      fg_color=C["accent_dim"], hover_color=C["accent"],
                      text_color="#ffffff",
                      font=ctk.CTkFont("Segoe UI", 11, "bold")
                     ).pack(pady=12, anchor="w")

        # CoI result display box
        res = ctk.CTkFrame(body, fg_color=C["card"], corner_radius=8)
        res.pack(fill="x", pady=4)
        self.coi_var  = tk.StringVar(value="—")
        self.risk_var = tk.StringVar(value="Select a pair above")
        ctk.CTkLabel(res, textvariable=self.coi_var,
                     font=ctk.CTkFont("Segoe UI", 36, "bold"),
                     text_color=C["accent"]
                    ).pack(pady=(10, 2), padx=14)
        self.risk_lbl = ctk.CTkLabel(res, textvariable=self.risk_var,
                     font=ctk.CTkFont("Segoe UI", 12),
                     text_color=C["text"], wraplength=260, justify="center")
        self.risk_lbl.pack(pady=(0, 10))

        # Shared ancestors list (read-only text box)
        ctk.CTkLabel(body, text="Shared ancestors:",
                     font=ctk.CTkFont("Segoe UI", 10, "bold"),
                     text_color=C["text_dim"]
                    ).pack(anchor="w", pady=(12, 2))
        self.anc_text = tk.Text(body, height=8, bg=C["entry"], fg=C["text"],
                                font=("Consolas", 9), relief="flat",
                                insertbackground=C["text"], state="disabled",
                                highlightthickness=1,
                                highlightbackground=C["border"])
        self.anc_text.pack(fill="both", expand=True)

        # Quick reference table
        ref = ctk.CTkFrame(body, fg_color=C["bg"])
        ref.pack(fill="x", pady=(12, 0))
        ctk.CTkLabel(ref, text="Reference:",
                     font=ctk.CTkFont("Segoe UI", 14, "bold"),
                     text_color=C["text_dim"]
                    ).pack(anchor="w")
        for rng, desc, col in [
            ("0%",         "No shared ancestors",          C["accent"]),
            ("≤6.25%",     "One grandparent shared",       C["gold"]),
            ("6.25–12.5%", "Half-sibling pairing",         C["orange"]),
            (">12.5%",     "Full sibling / parent×child",  C["red"]),
        ]:
            rf = ctk.CTkFrame(ref, fg_color=C["card"], corner_radius=4)
            rf.pack(fill="x", pady=1)
            ctk.CTkLabel(rf, text=f" {rng:12}",
                         font=ctk.CTkFont("Consolas", 9),
                         text_color=col, width=100
                        ).pack(side="left")
            ctk.CTkLabel(rf, text=desc,
                         font=ctk.CTkFont("Segoe UI", 11),
                         text_color=C["text_dim"]
                        ).pack(side="left", padx=4)

        self.refresh_animals()

    def refresh_animals(self):
        """Refresh all animal dropdowns with current active animals."""
        ids = db.get_animal_ids()
        self.ped_cb.configure(values=ids)
        self.sire_cb.configure(values=ids)
        self.dam_cb.configure(values=ids)

    def _show_pedigree(self):
        """Load ancestors for selected animal and draw pedigree tree."""
        val = self.ped_var.get()
        if not val:
            messagebox.showinfo("Select", "Select an animal first.")
            return
        aid = db.resolve_combo(val)
        self._draw_pedigree(aid, db.get_ancestors(aid, depth=3))

    def _draw_pedigree(self, root_id, ancestors):
        """
        Draw pedigree tree on canvas.

        Layout: 4 columns (generations 0-3), boxes placed at fixed
        vertical offsets. Lines connect child to parent boxes.

        Box colors: blue=male, pink=female, green=unknown.
        Each box shows: ID, name, morph.
        """
        import math
        c = self.canvas
        c.delete("all")

        BW, BH = 190, 54   # box width and height
        HG, VG = 44, 16    # horizontal and vertical gap

        # Fixed positions: path string → (generation, y_offset)
        # Path: "" = root, "S" = sire, "D" = dam, "SS" = sire's sire, etc.
        fixed = {
            "":    (0,  0),
            "S":   (1, -(BH+VG)*1),    "D":   (1,  (BH+VG)*1),
            "SS":  (2, -(BH+VG)*1.5),  "SD":  (2, -(BH+VG)*0.5),
            "DS":  (2,  (BH+VG)*0.5),  "DD":  (2,  (BH+VG)*1.5),
            "SSS": (3, -(BH+VG)*1.75), "SSD": (3, -(BH+VG)*1.25),
            "SDS": (3, -(BH+VG)*0.75), "SDD": (3, -(BH+VG)*0.25),
            "DSS": (3,  (BH+VG)*0.25), "DSD": (3,  (BH+VG)*0.75),
            "DDS": (3,  (BH+VG)*1.25), "DDD": (3,  (BH+VG)*1.75),
        }

        mx, my = 30, 20
        tw = (BW+HG)*4 + mx*2
        th = (BH+VG)*8 + my*2
        cx, cy = tw/2, th/2
        c.configure(scrollregion=(0, 0, tw, th))

        root_data = db.get_animal(root_id) or {}
        all_items = [("", root_id, dict(root_data))] + \
                    [(p, v["id"], v) for p, v in ancestors.items()]

        coords = {}
        for path, aid, data in all_items:
            if path not in fixed:
                continue
            gen, yoff = fixed[path]
            x = mx + gen*(BW+HG)
            y = cy + yoff - BH/2

            # Box color by sex
            sex = data.get("sex", "")
            if sex == "Male":
                bg, bdr = "#0d2a4a", "#7ecfff"
            elif sex == "Female":
                bg, bdr = "#2a0d2a", "#e091c0"
            else:
                bg, bdr = "#1a2a1a", "#52d9a0"

            c.create_rectangle(x, y, x+BW, y+BH,
                               fill=bg, outline=bdr, width=2)
            c.create_text(x+BW/2, y+11,
                          text=str(data.get("id", ""))[:18],
                          font=("Consolas", 8), fill="#7ecfff", anchor="center")
            c.create_text(x+BW/2, y+26,
                          text=str(data.get("name", ""))[:22],
                          font=("Segoe UI", 9, "bold"),
                          fill="#ffffff", anchor="center")
            c.create_text(x+BW/2, y+40,
                          text=str(data.get("morph", ""))[:26],
                          font=("Segoe UI", 8), fill="#a0c8a0", anchor="center")
            coords[path] = (x, y, x+BW, y+BH)

        # Draw connecting lines from parent to child
        links = {
            "S":"",  "D":"",
            "SS":"S","SD":"S","DS":"D","DD":"D",
            "SSS":"SS","SSD":"SS","SDS":"SD","SDD":"SD",
            "DSS":"DS","DSD":"DS","DDS":"DD","DDD":"DD",
        }
        for ch, pa in links.items():
            if ch in coords and pa in coords:
                x1,y1,x2,y2 = coords[pa]
                bx1,by1,bx2,by2 = coords[ch]
                px, py2  = x2, (y1+y2)/2
                bx, by2b = bx1, (by1+by2)/2
                mid = (px+bx)/2
                c.create_line(px, py2, mid, py2, mid, by2b, bx, by2b,
                              fill="#3a5a7a", width=1, smooth=True)

    def _calc_coi(self):
        """
        Calculate Coefficient of Inbreeding for selected pair.
        Uses Wright's path coefficient method (depth 5 generations).
        Updates result box with percentage and risk label.
        Lists all shared ancestors with ID, name, morph.
        """
        sv = self.sire_var.get()
        dv = self.dam_var.get()
        if not sv or not dv:
            messagebox.showinfo("Select", "Select both Sire and Dam.")
            return
        sid = db.resolve_combo(sv)
        did = db.resolve_combo(dv)
        if sid == did:
            messagebox.showerror("Error", "Sire and Dam cannot be the same animal.")
            return

        pct = db.calc_coi(sid, did, depth=5) * 100
        self.coi_var.set(f"{pct:.2f}%")

        # Risk assessment with color
        if pct == 0:
            risk, col = "✅  No shared ancestors\nSafe to pair", C["accent"]
        elif pct <= 3.125:
            risk, col = "✅  Very Low (≤3.125%)\nGenerally safe", C["accent"]
        elif pct <= 6.25:
            risk, col = "✅  Low (≤6.25%)\nAcceptable", C["gold"]
        elif pct <= 12.5:
            risk, col = "⚠️  Moderate (6.25–12.5%)\nUse caution", C["orange"]
        else:
            risk, col = "🚫  High (>12.5%)\nNot recommended", C["red"]

        self.risk_var.set(risk)
        self.risk_lbl.configure(text_color=col)

        # Find shared ancestors
        sa = db.get_ancestors(sid, depth=5)
        da = db.get_ancestors(did, depth=5)
        shared = {v["id"] for v in sa.values()} & {v["id"] for v in da.values()}

        self.anc_text.configure(state="normal")
        self.anc_text.delete("1.0", "end")
        if shared:
            self.anc_text.insert("end", f"{len(shared)} shared ancestor(s):\n\n")
            for aid in sorted(shared):
                a = db.get_animal(aid)
                if a:
                    self.anc_text.insert("end",
                        f"  {a['id']:12}  {(a['name'] or ''):16}  {a['morph'] or ''}\n")
        else:
            self.anc_text.insert("end", "No shared ancestors in known pedigree.")
        self.anc_text.configure(state="disabled")
