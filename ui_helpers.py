"""
ui_helpers.py — Shared theme, widgets and form dialog for CustomTkinter.

CONTENTS:
  C              — Color palette dict used across all tabs
  STATUS_TAG     — Maps status strings to treeview row color tags
  apply_treeview_style() — Dark theme for ttk.Treeview (CTk has no replacement)
  tag_tree()     — Apply color tags to a Treeview widget
  make_tree()    — Create a scrollable Treeview inside a tk.Frame
  confirm_delete() — Yes/No confirmation dialog
  section_header() — Dark header bar with accent label (used in panels)
  toolbar_frame() — Standard toolbar container for each tab
  btn()          — Standard toolbar button (CTkButton)
  open_form()    — Generic scrollable modal form dialog

CUSTOMTKINTER NOTES:
  - CTk widgets use appearance_mode="dark" and default "dark-blue" theme
  - ctk.set_widget_scaling(1.15) makes all CTk widgets 15% larger globally
  - Treeview is still ttk because CTk has no Treeview replacement
  - Form entries store StringVar objects (not widgets) so .get() works
    correctly when editing existing records

FORM DIALOG FIX (vs old tkinter version):
  - Combo boxes use CTkComboBox + StringVar — values always load on edit
  - Scroll binding is window-local (win.bind) not global (bind_all)
    so closing the window cleans up the binding automatically
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

# ── Global CTk appearance ─────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")
ctk.set_widget_scaling(1.15)   # All CTk widgets 15% bigger — adjust if needed
ctk.set_window_scaling(1.0)    # Keep window size as defined in geometry()

# ── Color palette ─────────────────────────────────────────────────────────────
# Used across all tab files. Change values here to retheme the whole app.
C = {
    "bg":          "#141b2d",   # main background
    "sidebar":     "#0f1624",   # toolbar and header background
    "card":        "#1a2440",   # card/panel background
    "card2":       "#1e2d50",   # secondary card (buttons etc.)
    "accent":      "#52d9a0",   # primary accent (green)
    "accent_dim":  "#1a5a40",   # darker accent for button bg
    "gold":        "#e9c46a",   # gold / warning color
    "orange":      "#e76f51",   # orange / caution color
    "red":         "#e63946",   # red / danger color
    "blue":        "#7ecfff",   # blue / info color
    "purple":      "#a78bfa",   # purple / holdback color
    "text":        "#ccd6f6",   # main text
    "text_dim":    "#6b7fa0",   # secondary / label text
    "border":      "#253555",   # widget border
    "entry":       "#1a2440",   # entry/combo background
    "row_even":    "#1a2440",   # treeview even row
    "row_odd":     "#141b2d",   # treeview odd row
    "green_dim":   "#1a3a2a",   # green row background (active/hatched)
    "gold_dim":    "#2a2510",   # gold row background (available/incubating)
    "red_dim":     "#2a1010",   # red row background (deceased/failed)
    "purple_dim":  "#1a1028",   # purple row background (holdback)
    "blue_dim":    "#0a1a2e",   # blue row background (reserved/gravid)
}

# ── Status → treeview tag mapping ─────────────────────────────────────────────
# Used by _populate() in each tab to color-code rows by status.
STATUS_TAG = {
    "Available":  "available",
    "Reserved":   "reserved",
    "Holdback":   "holdback",
    "Sold":       "sold",
    "Deceased":   "deceased",
    "Hatched":    "hatched",
    "Incubating": "available",
    "Gravid":     "reserved",
    "Pairing":    "holdback",
    "Failed":     "deceased",
    "Active":     "hatched",
    "Quarantine": "available",
}


def apply_treeview_style(root):
    """
    Apply dark theme to ttk.Treeview and Scrollbar widgets.
    Must be called once after the root window is created (in App.__init__).
    Also sets Listbox colors used by CTkComboBox dropdowns.
    """
    s = ttk.Style(root)
    s.theme_use("clam")

    s.configure("Treeview",
        background=C["row_even"], foreground=C["text"],
        fieldbackground=C["row_even"], rowheight=32,
        borderwidth=0, relief="flat",
        font=("Segoe UI", 10))

    s.configure("Treeview.Heading",
        background=C["sidebar"], foreground=C["accent"],
        relief="flat",
        font=("Segoe UI", 10, "bold"),
        padding=(8, 8))

    s.map("Treeview",
        background=[("selected", C["card2"])],
        foreground=[("selected", "#ffffff")])
    s.map("Treeview.Heading",
        background=[("active", C["card"])])

    # Scrollbar styling
    for orient in ("Vertical", "Horizontal"):
        s.configure(f"{orient}.TScrollbar",
            background=C["sidebar"], troughcolor=C["bg"],
            arrowcolor=C["text_dim"], bordercolor=C["bg"], relief="flat")

    # CTkComboBox dropdown listbox colors
    root.option_add("*TCombobox*Listbox.background", C["entry"])
    root.option_add("*TCombobox*Listbox.foreground", C["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", C["card"])


def tag_tree(tree):
    """
    Configure color tags on a Treeview widget.
    Tags are applied per-row in _populate() methods.
    """
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
    """
    Create a scrollable Treeview inside a tk.Frame.

    Returns (frame, tree) — pack/grid the frame, use tree to insert rows.
    All columns are left-aligned (anchor="w") for consistent readability.
    """
    frame = tk.Frame(parent, bg=C["bg"])
    tree  = ttk.Treeview(frame, columns=columns, show="headings",
                         selectmode="browse")
    for col, w in zip(columns, widths):
        tree.heading(col, text=col, anchor="w")
        tree.column(col, width=w, minwidth=40, anchor="w")

    vsb = ttk.Scrollbar(frame, orient="vertical",   command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    tag_tree(tree)
    return frame, tree


def confirm_delete(what):
    """Show a yes/no confirmation dialog. Returns True if confirmed."""
    return messagebox.askyesno("Confirm Delete",
        f"Delete {what}?\nThis cannot be undone.")


def section_header(parent, text):
    """
    Dark header bar with accent-colored bold label.
    Used at the top of dashboard panels.
    """
    f = ctk.CTkFrame(parent, fg_color=C["sidebar"], height=34, corner_radius=0)
    f.pack(fill="x")
    f.pack_propagate(False)
    ctk.CTkLabel(f, text=text,
                 font=ctk.CTkFont("Segoe UI", 12, "bold"),
                 text_color=C["accent"]
                ).pack(side="left", padx=12, pady=8)
    return f


def toolbar_frame(parent):
    """
    Standard toolbar container packed at the top of each tab.
    Returns a CTkFrame — pack buttons into it with side="left".
    """
    f = ctk.CTkFrame(parent, fg_color=C["sidebar"], height=56, corner_radius=8)
    f.pack(fill="x", padx=10, pady=(10, 6))
    f.pack_propagate(False)
    return f


def btn(parent, text, cmd, accent=False, width=115):
    """
    Standard toolbar button (CTkButton).
    accent=True uses green accent color for primary actions (Add).
    accent=False uses neutral card2 color for secondary actions.
    """
    b = ctk.CTkButton(
        parent, text=text, command=cmd,
        width=width, height=36, corner_radius=6,
        font=ctk.CTkFont("Segoe UI", 11),
        fg_color=C["accent_dim"] if accent else C["card2"],
        hover_color=C["accent"],
        text_color="#ffffff",
        border_width=1 if not accent else 0,
        border_color=C["border"],
    )
    b.pack(side="left", padx=4, pady=10)
    return b


def open_form(parent, title, fields, existing=None, on_save=None):
    """
    Generic scrollable modal form dialog.

    Parameters:
      parent   — parent widget
      title    — window title string
      fields   — list of (label, db_key, field_type, [options])
                 field_type: "entry" | "combo" | "combo_live" | "text"
                 combo_live: populated from db.get_animal_ids() dynamically
      existing — dict of current values (for edit mode); all values as strings
      on_save  — callback(data_dict, window) called when Save is clicked

    Storage:
      entries dict stores StringVar for entry/combo fields
      and the Text widget itself for "text" fields.
      Use .get() on StringVar, .get("1.0","end-1c") on Text widget.

    FIX — edit mode:
      Values not in the combo list are prepended so they always display.
      This fixes the blank-on-edit bug from the old tkinter version.

    FIX — scroll leak:
      Mouse wheel is bound to the window (win.bind), not globally (bind_all).
      When the window is destroyed the binding is cleaned up automatically.
    """
    existing = existing or {}

    win = ctk.CTkToplevel(parent)
    win.title(title)
    win.grab_set()
    win.focus_set()

    # Scrollable body using CTkScrollableFrame
    scroll = ctk.CTkScrollableFrame(win, fg_color=C["bg"],
                                    scrollbar_button_color=C["card2"],
                                    scrollbar_button_hover_color=C["accent"])
    scroll.pack(fill="both", expand=True, padx=0, pady=0)
    scroll.columnconfigure(1, weight=1)

    entries = {}
    import database as db  # imported here to avoid circular import

    for i, field in enumerate(fields):
        label, key, ftype = field[0], field[1], field[2]
        opts = list(field[3]) if len(field) > 3 else []

        # Convert existing value to string (handles None and numeric values)
        val = str(existing.get(key) or "")

        # Label column
        ctk.CTkLabel(scroll, text=label,
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["text_dim"], anchor="w", width=24
                    ).grid(row=i, column=0, sticky="w", padx=(12, 8), pady=4)

        # Widget column
        if ftype in ("combo", "combo_live"):
            if ftype == "combo_live":
                # Dynamic animal list — refreshed each time form opens
                opts = db.get_animal_ids()
                # If stored value is a raw ID, find matching "ID – Name" entry
                if val and " – " not in val:
                    val = next(
                        (o for o in opts if o.startswith(val + " –") or o == val),
                        val)

            var = tk.StringVar(value=val)
            # Ensure current value is always in the list (edit mode fix)
            values = list(opts) if val in opts else (
                [val] + list(opts) if val else list(opts))
            w = ctk.CTkComboBox(scroll, variable=var, values=values,
                                width=300, height=36,
                                fg_color=C["entry"],
                                border_color=C["border"],
                                button_color=C["card2"],
                                button_hover_color=C["accent"],
                                text_color=C["text"],
                                dropdown_fg_color=C["card"],
                                dropdown_text_color=C["text"],
                                dropdown_hover_color=C["card2"],
                                font=ctk.CTkFont("Segoe UI", 11),
                                state="readonly")
            w.set(val)
            w.grid(row=i, column=1, sticky="ew", padx=(0, 12), pady=4)
            entries[key] = var  # store StringVar — .get() returns current value

        elif ftype == "text":
            w = ctk.CTkTextbox(scroll, height=64, width=300,
                               fg_color=C["entry"],
                               border_color=C["border"],
                               border_width=1,
                               text_color=C["text"],
                               font=ctk.CTkFont("Segoe UI", 11))
            if val:
                w.insert("1.0", val)
            w.grid(row=i, column=1, sticky="ew", padx=(0, 12), pady=4)
            entries[key] = w  # store widget — use .get("1.0","end-1c")

        else:  # entry
            var = tk.StringVar(value=val)
            w = ctk.CTkEntry(scroll, textvariable=var,
                             width=300, height=36,
                             fg_color=C["entry"],
                             border_color=C["border"],
                             border_width=1,
                             text_color=C["text"],
                             font=ctk.CTkFont("Segoe UI", 11))
            w.grid(row=i, column=1, sticky="ew", padx=(0, 12), pady=4)
            entries[key] = var  # store StringVar

    # ── Button bar ────────────────────────────────────────────────────────────
    bar = ctk.CTkFrame(win, fg_color=C["sidebar"], height=56, corner_radius=0)
    bar.pack(side="bottom", fill="x")
    bar.pack_propagate(False)

    def _do_save():
        """Collect all field values and call on_save callback."""
        data = {}
        for field in fields:
            label, key, ftype = field[0], field[1], field[2]
            w = entries[key]
            if ftype == "text":
                v = w.get("1.0", "end-1c").strip()
            else:
                v = w.get().strip()  # StringVar.get()
            data[key] = v if v else None
        if on_save:
            on_save(data, win)

    ctk.CTkButton(bar, text="💾  Save", command=_do_save,
                  width=140, height=38, corner_radius=6,
                  fg_color=C["accent_dim"], hover_color=C["accent"],
                  text_color="#ffffff",
                  font=ctk.CTkFont("Segoe UI", 11, "bold")
                 ).pack(side="right", padx=12, pady=9)

    ctk.CTkButton(bar, text="Cancel", command=win.destroy,
                  width=100, height=38, corner_radius=6,
                  fg_color=C["card2"], hover_color=C["card"],
                  text_color=C["text"],
                  border_width=1, border_color=C["border"],
                  font=ctk.CTkFont("Segoe UI", 11)
                 ).pack(side="right", padx=4, pady=9)

    # Size window to content
    h = min(680, max(320, len(fields) * 46 + 70))
    win.geometry(f"560x{h}")
    win.minsize(480, 300)
    return win, entries
