"""main.py — App entry point"""
import tkinter as tk
from tkinter import ttk
import database as db
import logging
import os
from ui_helpers import C, apply_theme

# Lokitus AppData-kansioon — sama kansio kuin tietokanta
# Kirjoittaa virheet hiljaa taustalla, ei näy käyttäjälle
def _setup_logging():
    log_dir = os.path.join(
        os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"),
        "BallPythonDB"
    )
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "error.log")
    logging.basicConfig(
        filename=log_path,
        level=logging.ERROR,
        format="%(asctime)s %(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        encoding="utf-8",
    )

_setup_logging()
log = logging.getLogger(__name__)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Myrtillus Reptiles — From Breeder to Breeders")
        self.geometry("1340x840")
        self.minsize(1000,660)
        self.configure(bg=C["bg"])
        # Set window icon
        try:
            import os
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
            self.iconbitmap(icon_path)
        except Exception:
            pass
        db.init_db()
        apply_theme(self)
        self._build()

    def _build(self):
        from ui_dashboard  import DashboardTab
        from ui_animals    import AnimalsTab
        from ui_husbandry  import HusbandryTab
        from ui_health     import HealthTab
        from ui_clutches   import ClutchTab
        from ui_hatchlings import HatchlingsTab
        from ui_pedigree   import PedigreeTab

        # Header bar
        hdr = tk.Frame(self, bg=C["sidebar"], height=50)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="🐍  Ball Python Breeder Database",
                 bg=C["sidebar"], fg=C["accent"],
                 font=("Segoe UI",14,"bold")).pack(side="left", padx=18, pady=12)
        # CSV button in header
        from ui_csv import CsvDialog
        ttk.Button(hdr, text="📥  CSV Export/Import",
                   command=lambda: CsvDialog(self, self)
                  ).pack(side="right", padx=12, pady=10)
        tk.Label(hdr, text="v2.1", bg=C["sidebar"],
                 fg=C["text_dim"], font=("Segoe UI",9)).pack(side="right", padx=4)

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)

        self.tab_dash       = DashboardTab(self.nb, self)
        self.tab_animals    = AnimalsTab(self.nb, self)
        self.tab_husbandry  = HusbandryTab(self.nb, self)
        self.tab_health     = HealthTab(self.nb, self)
        self.tab_clutches   = ClutchTab(self.nb, self)
        self.tab_hatchlings = HatchlingsTab(self.nb, self)
        self.tab_pedigree   = PedigreeTab(self.nb, self)

        for tab, label in [
            (self.tab_dash,       "📊  Dashboard"),
            (self.tab_animals,    "🐍  Animals"),
            (self.tab_husbandry,  "📋  Husbandry"),
            (self.tab_health,     "❤️   Health"),
            (self.tab_clutches,   "🥚  Clutches"),
            (self.tab_hatchlings, "🐣  Hatchlings"),
            (self.tab_pedigree,   "🌳  Pedigree & CoI"),
        ]:
            self.nb.add(tab, text=label)

        self.nb.bind("<<NotebookTabChanged>>", self._on_tab)

    def _on_tab(self, event):
        name = self.nb.tab(self.nb.select(), "text")
        if "Pedigree" in name:
            self.tab_pedigree.refresh_animals()
        elif "Dashboard" in name:
            self.tab_dash.load()

    def refresh_all(self):
        """Paivittaa kaikki valilehdet datamuutoksen jalkeen.
        Virheet kirjataan lokiin mutta eivat keskeyta muita paivityksia."""
        for name, func in [
            ("husbandry",  lambda: self.tab_husbandry.load()),
            ("health",     lambda: self.tab_health.load()),
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
