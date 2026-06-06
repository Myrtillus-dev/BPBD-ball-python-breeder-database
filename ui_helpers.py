"""ui_helpers.py — theme, widgets, form dialog. Fixed: edit loads data correctly."""
import tkinter as tk
from tkinter import ttk, messagebox

C = {
    "bg":        "#141b2d", "sidebar":   "#0f1624", "card":     "#1a2440",
    "card2":     "#1e2d50", "accent":    "#52d9a0", "accent_dim":"#1a5a40",
    "gold":      "#e9c46a", "orange":    "#e76f51", "red":      "#e63946",
    "blue":      "#7ecfff", "purple":    "#a78bfa", "text":     "#ccd6f6",
    "text_dim":  "#6b7fa0", "border":    "#253555", "entry":    "#1a2440",
    "row_even":  "#1a2440", "row_odd":   "#141b2d",
    "green_dim": "#1a3a2a", "gold_dim":  "#2a2510",
    "red_dim":   "#2a1010", "purple_dim":"#1a1028", "blue_dim": "#0a1a2e",
}

STATUS_TAG = {
    "Available":"available","Reserved":"reserved","Holdback":"holdback",
    "Sold":"sold","Deceased":"deceased","Hatched":"hatched",
    "Incubating":"available","Gravid":"reserved","Pairing":"holdback","Failed":"deceased",
    "Active":"hatched",
}

def apply_theme(root):
    s = ttk.Style(root)
    s.theme_use("clam")
    bg=C["bg"]; card=C["card"]; acc=C["accent"]; txt=C["text"]
    dim=C["text_dim"]; bdr=C["border"]; ent=C["entry"]

    s.configure(".", background=bg, foreground=txt, fieldbackground=ent,
        troughcolor=C["sidebar"], bordercolor=bdr, darkcolor=card, lightcolor=card,
        insertcolor=txt, selectbackground=card, selectforeground=txt,
        font=("Segoe UI",10))
    s.configure("TFrame",      background=bg)
    s.configure("TLabel",      background=bg, foreground=txt)
    s.configure("TLabelframe", background=bg, foreground=acc)
    s.configure("TLabelframe.Label", background=bg, foreground=acc, font=("Segoe UI",10,"bold"))
    s.configure("TButton", background=card, foreground=txt, bordercolor=bdr,
        relief="flat", padding=(10,5), font=("Segoe UI",9))
    s.map("TButton",
        background=[("active",C["accent_dim"]),("pressed",acc)],
        foreground=[("active","#fff")])
    s.configure("Accent.TButton", background=C["accent_dim"], foreground="#fff",
        font=("Segoe UI",9,"bold"), relief="flat", padding=(12,6))
    s.map("Accent.TButton",
        background=[("active",acc),("pressed",acc)])
    s.configure("Quick.TButton", background="#1a3050", foreground=C["gold"],
        font=("Segoe UI",10,"bold"), relief="flat", padding=(14,8))
    s.map("Quick.TButton",
        background=[("active","#254070"),("pressed","#254070")])
    s.configure("TEntry", fieldbackground=ent, foreground=txt,
        insertcolor=txt, bordercolor=bdr, relief="flat", padding=(6,4))
    s.configure("TCombobox", fieldbackground=ent, foreground=txt,
        selectbackground=card, selectforeground=txt, arrowcolor=acc)
    s.map("TCombobox",
        fieldbackground=[("readonly",ent)], foreground=[("readonly",txt)])
    s.configure("TNotebook", background=C["sidebar"], borderwidth=0)
    s.configure("TNotebook.Tab", background=C["sidebar"], foreground=dim,
        padding=(16,8), font=("Segoe UI",10))
    s.map("TNotebook.Tab",
        background=[("selected",bg),("active",card)],
        foreground=[("selected",acc),("active",txt)])
    s.configure("Treeview", background=C["row_even"], foreground=txt,
        fieldbackground=C["row_even"], rowheight=26, borderwidth=0, relief="flat",
        font=("Segoe UI",9))
    s.configure("Treeview.Heading", background=C["sidebar"], foreground=acc,
        relief="flat", font=("Segoe UI",9,"bold"), padding=(6,6))
    s.map("Treeview",
        background=[("selected",C["card2"])], foreground=[("selected","#fff")])
    s.map("Treeview.Heading", background=[("active",card)])
    for o in ("Vertical","Horizontal"):
        s.configure(f"{o}.TScrollbar", background=C["sidebar"], troughcolor=bg,
            arrowcolor=dim, bordercolor=bg, relief="flat")
    root.option_add("*TCombobox*Listbox.background", ent)
    root.option_add("*TCombobox*Listbox.foreground", txt)
    root.option_add("*TCombobox*Listbox.selectBackground", card)
    root.option_add("*TCombobox*Listbox.font", ("Segoe UI",10))
    root.option_add("*Background", bg)

def tag_tree(tree):
    tree.tag_configure("even",      background=C["row_even"], foreground=C["text"])
    tree.tag_configure("odd",       background=C["row_odd"],  foreground=C["text"])
    tree.tag_configure("sold",      background=C["card"],     foreground=C["text_dim"])
    tree.tag_configure("available", background=C["gold_dim"], foreground=C["gold"])
    tree.tag_configure("reserved",  background=C["blue_dim"], foreground=C["blue"])
    tree.tag_configure("holdback",  background=C["purple_dim"],foreground=C["purple"])
    tree.tag_configure("deceased",  background=C["red_dim"],  foreground=C["red"])
    tree.tag_configure("hatched",   background=C["green_dim"],foreground=C["accent"])
    tree.tag_configure("warning",   background="#2a2000",     foreground=C["gold"])
    tree.tag_configure("overdue",   background="#2a0a00",     foreground=C["orange"])

def make_tree(parent, columns, widths):
    frame = tk.Frame(parent, bg=C["bg"])
    tree  = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
    for col,w in zip(columns,widths):
        tree.heading(col, text=col, anchor="w")
        tree.column(col, width=w, minwidth=40, anchor="w")
    vsb = ttk.Scrollbar(frame, orient="vertical",   command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.grid(row=0,column=0,sticky="nsew")
    vsb.grid(row=0,column=1,sticky="ns")
    hsb.grid(row=1,column=0,sticky="ew")
    frame.rowconfigure(0,weight=1); frame.columnconfigure(0,weight=1)
    tag_tree(tree)
    return frame, tree

def confirm_delete(what):
    return messagebox.askyesno("Confirm Delete", f"Delete {what}?\nThis cannot be undone.")

def toolbar_frame(parent):
    f = tk.Frame(parent, bg=C["sidebar"], height=46)
    f.pack(fill="x", padx=10, pady=(10,6))
    f.pack_propagate(False)
    return f

def btn(parent, text, cmd, accent=False, style=None):
    st = style or ("Accent.TButton" if accent else "TButton")
    b  = ttk.Button(parent, text=text, command=cmd, style=st)
    b.pack(side="left", padx=4, pady=7)
    return b

def section_header(parent, text, color=None):
    f = tk.Frame(parent, bg=color or C["sidebar"], height=32)
    f.pack(fill="x"); f.pack_propagate(False)
    tk.Label(f, text=text, bg=color or C["sidebar"],
             fg=C["accent"], font=("Segoe UI",10,"bold")).pack(side="left",padx=10,pady=6)
    return f

# ── Generic form dialog ────────────────────────────────────────────────────────
def open_form(parent, title, fields, existing=None, on_save=None):
    """
    Modal form. existing must be a plain dict with string values.
    FIX: combo boxes set value directly via StringVar, not .set() on widget.
    FIX: scroll binding is window-local, cleaned up on destroy.
    """
    existing = existing or {}

    win = tk.Toplevel(parent)
    win.title(title)
    win.configure(bg=C["bg"])
    win.grab_set(); win.focus_set()

    canvas = tk.Canvas(win, bg=C["bg"], highlightthickness=0, bd=0)
    vsb    = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    canvas.pack(side="top", fill="both", expand=True)

    inner  = tk.Frame(canvas, bg=C["bg"])
    wid    = canvas.create_window((0,0), window=inner, anchor="nw")

    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(wid, width=e.width))

    def _scroll(e):
        try: canvas.yview_scroll(int(-1*(e.delta/120)),"units")
        except tk.TclError: pass
    win.bind("<MouseWheel>", _scroll)

    inner.columnconfigure(1, weight=1)
    entries = {}

    import database as db

    for i, field in enumerate(fields):
        label, key, ftype = field[0], field[1], field[2]
        opts = list(field[3]) if len(field) > 3 else []
        val  = existing.get(key, "") or ""

        tk.Label(inner, text=label, bg=C["bg"], fg=C["text_dim"],
                 font=("Segoe UI",9), anchor="w", width=24
                ).grid(row=i, column=0, sticky="w", padx=(10,8), pady=3)

        if ftype in ("combo","combo_live"):
            if ftype == "combo_live":
                opts = db.get_animal_ids()
                # If stored value is a raw ID, find matching "ID – Name" entry
                if val and " – " not in val:
                    match = next((o for o in opts if o.startswith(val+" –") or o==val), val)
                    val   = match

            # Use a StringVar so we can set arbitrary values including ones not in list
            var = tk.StringVar(value=val)
            w   = ttk.Combobox(inner, textvariable=var, values=opts,
                               state="readonly", width=32, font=("Segoe UI",10))
            # Force the displayed value even if not in list (edit mode)
            if val:
                w["values"] = list(opts) if val in opts else [val] + list(opts)
                var.set(val)
            w.grid(row=i, column=1, sticky="ew", padx=(0,10), pady=3)
            entries[key] = var   # store StringVar, not widget

        elif ftype == "text":
            w = tk.Text(inner, height=3, bg=C["entry"], fg=C["text"],
                        insertbackground=C["text"], relief="flat",
                        font=("Segoe UI",10), highlightthickness=1,
                        highlightbackground=C["border"], highlightcolor=C["accent"])
            if val: w.insert("1.0", val)
            w.grid(row=i, column=1, sticky="ew", padx=(0,10), pady=3)
            entries[key] = w

        else:  # entry
            var = tk.StringVar(value=val)
            w   = ttk.Entry(inner, textvariable=var, width=34, font=("Segoe UI",10))
            w.grid(row=i, column=1, sticky="ew", padx=(0,10), pady=3)
            entries[key] = var   # store StringVar

    # Button bar
    bar = tk.Frame(win, bg=C["sidebar"], height=52)
    bar.pack(side="bottom", fill="x"); bar.pack_propagate(False)

    def _do_save():
        data = {}
        for field in fields:
            label, key, ftype = field[0], field[1], field[2]
            w = entries[key]
            if ftype == "text":
                v = w.get("1.0","end-1c").strip()
            else:
                v = w.get().strip()   # StringVar.get()
            data[key] = v if v else None
        if on_save:
            on_save(data, win)

    ttk.Button(bar, text="💾  Save",  command=_do_save,
               style="Accent.TButton").pack(side="right", padx=12, pady=10)
    ttk.Button(bar, text="Cancel", command=win.destroy
               ).pack(side="right", padx=4, pady=10)

    h = min(680, max(300, len(fields)*42+70))
    win.geometry(f"560x{h}"); win.minsize(480,280)
    return win, entries
