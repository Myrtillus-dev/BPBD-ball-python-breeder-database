"""Pedigree viewer and CoI calculator"""
import tkinter as tk
from tkinter import ttk, messagebox
import database as db
from ui_helpers import C, tag_tree, section_header

class PedigreeTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        # ── LEFT: pedigree tree ───────────────────────────────────────────────
        left = tk.Frame(paned, bg=C["bg"])
        paned.add(left, weight=3)
        section_header(left, "🌳  Pedigree Viewer")

        sel = tk.Frame(left, bg=C["bg"])
        sel.pack(fill="x", padx=10, pady=8)
        tk.Label(sel, text="Animal:", bg=C["bg"],
                 fg=C["text_dim"], font=("Segoe UI",9)).pack(side="left")
        self.ped_var = tk.StringVar()
        self.ped_cb  = ttk.Combobox(sel, textvariable=self.ped_var,
                                    width=28, state="readonly")
        self.ped_cb.pack(side="left", padx=8)
        ttk.Button(sel, text="Show Pedigree",
                   command=self._show_pedigree).pack(side="left")

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
        paned.add(right, weight=2)
        section_header(right, "🧬  Inbreeding Coefficient (CoI)")

        body = tk.Frame(right, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=14, pady=10)

        for label, attr in [("Sire (Father):","sire"), ("Dam (Mother):","dam")]:
            r = tk.Frame(body, bg=C["bg"])
            r.pack(fill="x", pady=4)
            tk.Label(r, text=label, bg=C["bg"], fg=C["text_dim"],
                     font=("Segoe UI",9), width=16, anchor="w").pack(side="left")
            var = tk.StringVar()
            cb  = ttk.Combobox(r, textvariable=var, width=26, state="readonly")
            cb.pack(side="left")
            setattr(self, f"{attr}_var", var)
            setattr(self, f"{attr}_cb",  cb)

        ttk.Button(body, text="⚡  Calculate CoI",
                   style="Accent.TButton",
                   command=self._calc_coi).pack(pady=12, anchor="w")

        res = tk.Frame(body, bg=C["card"])
        res.pack(fill="x", pady=4)
        self.coi_var  = tk.StringVar(value="—")
        self.risk_var = tk.StringVar(value="Select a pair above")
        tk.Label(res, textvariable=self.coi_var, bg=C["card"],
                 fg=C["accent"], font=("Segoe UI",32,"bold")).pack(pady=(10,2), padx=14)
        self.risk_lbl = tk.Label(res, textvariable=self.risk_var, bg=C["card"],
                 fg=C["text"], font=("Segoe UI",11), wraplength=260, justify="center")
        self.risk_lbl.pack(pady=(0,10))

        tk.Label(body, text="Shared ancestors:", bg=C["bg"],
                 fg=C["text_dim"], font=("Segoe UI",9,"bold")).pack(anchor="w", pady=(12,2))
        self.anc_text = tk.Text(body, height=8, bg=C["entry"], fg=C["text"],
                                font=("Consolas",9), relief="flat",
                                insertbackground=C["text"], state="disabled",
                                highlightthickness=1, highlightbackground=C["border"])
        self.anc_text.pack(fill="both", expand=True)

        ref = tk.Frame(body, bg=C["bg"])
        ref.pack(fill="x", pady=(12,0))
        tk.Label(ref, text="Reference:", bg=C["bg"],
                 fg=C["text_dim"], font=("Segoe UI",9,"bold")).pack(anchor="w")
        for rng, desc, col in [
            ("0%",         "No shared ancestors",         C["accent"]),
            ("≤6.25%",     "One grandparent shared",      C["gold"]),
            ("6.25–12.5%", "Half-sibling pairing",        C["orange"]),
            (">12.5%",     "Full sibling / parent×child", C["red"]),
        ]:
            rf = tk.Frame(ref, bg=C["card"])
            rf.pack(fill="x", pady=1)
            tk.Label(rf, text=f" {rng:12}", bg=C["card"], fg=col,
                     font=("Consolas",9), width=13).pack(side="left")
            tk.Label(rf, text=desc, bg=C["card"], fg=C["text_dim"],
                     font=("Segoe UI",9)).pack(side="left", padx=4)

        self.refresh_animals()

    def refresh_animals(self):
        ids = db.get_animal_ids()
        self.ped_cb["values"]  = ids
        self.sire_cb["values"] = ids
        self.dam_cb["values"]  = ids

    def _show_pedigree(self):
        val = self.ped_var.get()
        if not val:
            messagebox.showinfo("Select", "Select an animal first.")
            return
        aid = db.resolve_combo(val)
        anc = db.get_ancestors(aid, depth=3)
        self._draw_pedigree(aid, anc)

    def _draw_pedigree(self, root_id, ancestors):
        c = self.canvas
        c.delete("all")
        BW, BH = 190, 54
        HG, VG = 44, 16

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
        c.configure(scrollregion=(0,0,tw,th))

        root_data = db.get_animal(root_id) or {}
        all_items = [("", root_id, dict(root_data))] + \
                    [(p, v["id"], v) for p,v in ancestors.items()]

        coords = {}
        for path, aid, data in all_items:
            if path not in fixed: continue
            gen, yoff = fixed[path]
            x = mx + gen*(BW+HG)
            y = cy + yoff - BH/2
            sex = data.get("sex","")
            if sex=="Male":    bg,bdr = "#0d2a4a","#7ecfff"
            elif sex=="Female": bg,bdr = "#2a0d2a","#e091c0"
            else:               bg,bdr = "#1a2a1a","#52d9a0"
            c.create_rectangle(x,y,x+BW,y+BH, fill=bg, outline=bdr, width=2)
            c.create_text(x+BW/2, y+11, text=str(data.get("id",""))[:18],
                          font=("Consolas",8), fill="#7ecfff", anchor="center")
            c.create_text(x+BW/2, y+26, text=str(data.get("name",""))[:22],
                          font=("Segoe UI",9,"bold"), fill="#fff", anchor="center")
            c.create_text(x+BW/2, y+40, text=str(data.get("morph",""))[:26],
                          font=("Segoe UI",8), fill="#a0c8a0", anchor="center")
            coords[path] = (x,y,x+BW,y+BH)

        links = {"S":"","D":"","SS":"S","SD":"S","DS":"D","DD":"D",
                 "SSS":"SS","SSD":"SS","SDS":"SD","SDD":"SD",
                 "DSS":"DS","DSD":"DS","DDS":"DD","DDD":"DD"}
        for ch,pa in links.items():
            if ch in coords and pa in coords:
                x1,y1,x2,y2 = coords[pa]
                bx1,by1,bx2,by2 = coords[ch]
                px,py2 = x2,(y1+y2)/2
                bx,by2b = bx1,(by1+by2)/2
                mid = (px+bx)/2
                c.create_line(px,py2, mid,py2, mid,by2b, bx,by2b,
                              fill="#3a5a7a", width=1, smooth=True)

    def _calc_coi(self):
        sv = self.sire_var.get()
        dv = self.dam_var.get()
        if not sv or not dv:
            messagebox.showinfo("Select","Select both Sire and Dam.")
            return
        sid = db.resolve_combo(sv)
        did = db.resolve_combo(dv)
        if sid == did:
            messagebox.showerror("Error","Sire and Dam cannot be the same animal.")
            return
        coi = db.calc_coi(sid, did, depth=5)
        pct = coi*100
        self.coi_var.set(f"{pct:.2f}%")
        if pct == 0:
            risk,col = "✅  No shared ancestors\nSafe to pair", C["accent"]
        elif pct <= 3.125:
            risk,col = "✅  Very Low (≤3.125%)\nGenerally safe", C["accent"]
        elif pct <= 6.25:
            risk,col = "✅  Low (≤6.25%)\nAcceptable", C["gold"]
        elif pct <= 12.5:
            risk,col = "⚠️  Moderate (6.25–12.5%)\nUse caution", C["orange"]
        else:
            risk,col = "🚫  High (>12.5%)\nNot recommended", C["red"]
        self.risk_var.set(risk)
        self.risk_lbl.configure(fg=col)

        sa = db.get_ancestors(sid, depth=5)
        da = db.get_ancestors(did, depth=5)
        shared = {v["id"] for v in sa.values()} & {v["id"] for v in da.values()}
        self.anc_text.configure(state="normal")
        self.anc_text.delete("1.0","end")
        if shared:
            self.anc_text.insert("end",f"{len(shared)} shared ancestor(s):\n\n")
            for aid in sorted(shared):
                a = db.get_animal(aid)
                if a:
                    self.anc_text.insert("end",
                        f"  {a['id']:12}  {(a['name'] or ''):16}  {a['morph'] or ''}\n")
        else:
            self.anc_text.insert("end","No shared ancestors in known pedigree.")
        self.anc_text.configure(state="disabled")
