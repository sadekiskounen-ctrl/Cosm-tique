import sys
import os
import logging
from pathlib import Path

# Configuration des variables d'environnement Tcl/Tk pour Windows et PyInstaller
if getattr(sys, 'frozen', False):
    base_dir = Path(sys.executable).parent
    candidates_tcl = [
        base_dir / "_internal" / "tcl8.6",
        base_dir / "_internal" / "tcl" / "tcl8.6",
        base_dir / "_internal" / "lib" / "tcl8.6",
        base_dir / "_internal" / "_tcl_data",
        base_dir / "tcl8.6",
        base_dir / "lib" / "tcl8.6",
    ]
    candidates_tk = [
        base_dir / "_internal" / "tk8.6",
        base_dir / "_internal" / "tcl" / "tk8.6",
        base_dir / "_internal" / "lib" / "tk8.6",
        base_dir / "_internal" / "_tk_data",
        base_dir / "tk8.6",
        base_dir / "lib" / "tk8.6",
    ]
    for p in candidates_tcl:
        if (p / "init.tcl").exists():
            os.environ["TCL_LIBRARY"] = str(p)
            break
    for p in candidates_tk:
        if (p / "tk.tcl").exists():
            os.environ["TK_LIBRARY"] = str(p)
            break

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MAIN")

def main():
    try:
        from database.db_manager import get_db
        # 1. Initialiser la base de données et la synchronisation multi-partitions C:/D:
        logger.info("Initialisation de la base de données SQLite et vérification C: / D:...")
        db = get_db()

        # 2. Démarrer l'interface graphique CustomTkinter
        logger.info("Lancement de l'interface CustomTkinter...")
        from ui.app import MainApp
        app = MainApp()
        app.mainloop()

    except Exception as e:
        logger.critical(f"Erreur fatale au lancement de l'application : {e}", exc_info=True)
        import tkinter.messagebox as mb
        mb.showerror("Erreur Fatale", f"Impossible de démarrer l'application :\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
