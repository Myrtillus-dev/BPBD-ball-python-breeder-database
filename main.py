"""
main.py — Application entry point and main CustomTkinter window.

WINDOW STRUCTURE:
  Header bar (dark)  — app name + CSV button + version
  CTkTabview         — tab navigation with bright text labels
    📊 Dashboard     — overview, alerts, quick-log
    🐍 Animals       — collection profiles
    📋 Husbandry     — daily care logs
    ❤️  Health        — medical records
    🥚 Clutches      — breeding cycle management
    🐣 Hatchlings    — per-hatchling tracking
    🌳 Pedigree & CoI — ancestor viewer + inbreeding calculator

ERROR LOGGING:
  Errors in refresh_all() are caught and written silently to:
  %LOCALAPPDATA%\BallPythonDB\error.log
  This means UI never freezes on a non-critical refresh error.

DB PATH:
  %LOCALAPPDATA%\BallPythonDB\ballpython.db
  Using AppData avoids PyInstaller's temp folder which is deleted on exit.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import database as db
import logging
import os
from ui_helpers import C, apply_treeview_style


# ── Silent error logging ──────────────────────────────────────────────────────
def _setup_logging():
    """
    Set up file-based error logging to AppData/BallPythonDB/error.log.
    Called once at startup. Does not affect the UI in any way.
    """
    log_dir = os.path.join(
        os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"),
        "BallPythonDB"
    )
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(log_dir, "error.log"),
        level=logging.ERROR,
        format="%(asctime)s %(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        encoding="utf-8",
    )

_setup_logging()
log = logging.getLogger(__name__)


class App(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.title("Myrtillus Reptiles — From Breeder to Breeders")
        self.geometry("1400x900")
        self.minsize(1100, 700)
        self.configure(fg_color=C["bg"])

        # Set window icon — works both in development and PyInstaller bundle
        try:
            import sys
            base = getattr(sys, "_MEIPASS",
                           os.path.dirname(os.path.abspath(__file__)))
            self.iconbitmap(os.path.join(base, "icon.ico"))
        except Exception:
            pass  # Icon is optional, skip silently

        db.init_db()
        apply_treeview_style(self)
        self._build()

    def _build(self):
        """Build header bar and tab view with all tab contents."""
        from ui_dashboard  import DashboardTab
        from ui_animals    import AnimalsTab
        from ui_husbandry  import HusbandryTab
        from ui_health     import HealthTab
        from ui_clutches   import ClutchTab
        from ui_hatchlings import HatchlingsTab
        from ui_pedigree   import PedigreeTab

        # ── Header bar ────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=C["sidebar"], height=58, corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # App name (left)
        ctk.CTkLabel(hdr,
                     text="🐍  Ball Python Breeder Database",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=C["accent"]
                    ).pack(side="left", padx=18, pady=12)

        # CSV button and version (right)
        from ui_csv import CsvDialog
        ctk.CTkButton(hdr, text="📥  CSV Export/Import",
                      command=lambda: CsvDialog(self, self),
                      width=170, height=34, corner_radius=6,
                      fg_color=C["card2"], hover_color=C["accent"],
                      text_color=C["text"],
                      border_width=1, border_color=C["border"],
                      font=ctk.CTkFont("Segoe UI", 10)
                     ).pack(side="right", padx=12, pady=12)
        ctk.CTkLabel(hdr, text="v3.0",
                     font=ctk.CTkFont("Segoe UI", 9),
                     text_color=C["text_dim"]
                    ).pack(side="right", padx=4)

        # ── Tab view ──────────────────────────────────────────────────────────
        self.tabs = ctk.CTkTabview(self,
                                   fg_color=C["bg"],
                                   segmented_button_fg_color=C["sidebar"],
                                   segmented_button_selected_color=C["accent_dim"],
                                   segmented_button_selected_hover_color=C["accent"],
                                   segmented_button_unselected_color=C["sidebar"],
                                   segmented_button_unselected_hover_color=C["card"],
                                   text_color="#e0e8ff",       # bright, readable
                                   text_color_disabled=C["text_dim"],
                                   border_color=C["border"],
                                   border_width=1,
                                   anchor="nw")
        self.tabs.pack(fill="both", expand=True, padx=0, pady=0)

        # Add all tabs
        tab_names = [
            "📊  Dashboard",
            "🐍  Animals",
            "📋  Husbandry",
            "❤️   Health",
            "🥚  Clutches",
            "🐣  Hatchlings",
            "🌳  Pedigree & CoI",
        ]
        for name in tab_names:
            self.tabs.add(name)

        # Make tab buttons bigger and bolder
        self.tabs._segmented_button.configure(
            font=ctk.CTkFont(
		family="Segoe UI",
		size=11,
		weight="bold"
	    ),
            height=42,
            text_color="#e0e8ff",
            text_color_disabled="#8899cc",
            selected_color=C["accent_dim"],
            selected_hover_color=C["accent"],
            unselected_color=C["sidebar"],
            unselected_hover_color=C["card"])

        # Build tab contents — each tab fills its parent frame
        self.tab_dash       = DashboardTab( self.tabs.tab("📊  Dashboard"),     self)
        self.tab_animals    = AnimalsTab(   self.tabs.tab("🐍  Animals"),        self)
        self.tab_husbandry  = HusbandryTab( self.tabs.tab("📋  Husbandry"),      self)
        self.tab_health     = HealthTab(    self.tabs.tab("❤️   Health"),         self)
        self.tab_clutches   = ClutchTab(    self.tabs.tab("🥚  Clutches"),        self)
        self.tab_hatchlings = HatchlingsTab(self.tabs.tab("🐣  Hatchlings"),     self)
        self.tab_pedigree   = PedigreeTab(  self.tabs.tab("🌳  Pedigree & CoI"), self)

    def _on_tab(self, name):
        """
        Called when user switches tabs.
        Refreshes pedigree dropdowns or dashboard when navigated to.
        """
        if "Pedigree" in name:
            self.tab_pedigree.refresh_animals()
        elif "Dashboard" in name:
            self.tab_dash.load()

    def refresh_all(self):
        """
        Refresh all tabs after any data change.
        Called after add/edit/delete in any tab.
        Errors are caught and logged silently — one tab failing
        does not prevent other tabs from refreshing.
        """
        for name, func in [
            ("animals",    lambda: self.tab_animals.load()),
            ("husbandry",  lambda: self.tab_husbandry.load()),
            ("health",     lambda: self.tab_health.load()),
            ("clutches",   lambda: self.tab_clutches.load()),
            ("hatchlings", lambda: self.tab_hatchlings.load()),
            ("pedigree",   lambda: self.tab_pedigree.refresh_animals()),
            ("dashboard",  lambda: self.tab_dash.load()),
        ]:
            try:
                func()
            except Exception as e:
                log.error("refresh_all [%s]: %s", name, e, exc_info=True)


if __name__ == "__main__":
    app = App()
    app.mainloop()
