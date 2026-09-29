"""
Script de compilation PyInstaller pour CosmetiquePro
Génère un dossier dist/CosmetiquePro/ avec CosmetiquePro.exe autonome
Usage : python build_exe.py
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path


def build():
    root_dir = Path(__file__).parent.resolve()
    os.chdir(root_dir)

    print("=" * 65)
    print("  COMPILATION EXECUTABLE WINDOWS (.EXE) - COSMETIQUEPRO")
    print("  Application : Stock + Caisse + Code-barres")
    print("=" * 65)

    # Chemins des packages importants
    import customtkinter
    import matplotlib
    import PIL

    ctk_path  = Path(customtkinter.__file__).parent
    mpl_path  = Path(matplotlib.__file__).parent
    pil_path  = Path(PIL.__file__).parent

    dist_dir  = root_dir / "dist"
    build_dir = root_dir / "build_temp"
    main_py   = root_dir / "main.py"

    # Nettoyage des anciens builds
    for d in [dist_dir / "CosmetiquePro", build_dir]:
        if d.exists():
            print(f"  Nettoyage : {d}")
            shutil.rmtree(d, ignore_errors=True)

    tcl_dir = Path(sys.prefix) / "tcl"
    tcl86 = tcl_dir / "tcl8.6"
    tk86 = tcl_dir / "tk8.6"

    # ──────────────────────────────────────────────────────────────
    # Commande PyInstaller
    # ──────────────────────────────────────────────────────────────
    sep = ";"  # Windows path separator for --add-data

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",                          # dossier unique (stable, chargement rapide)
        "--windowed",                        # pas de console noire
        "--name=CosmetiquePro",

        # ── Données à inclure ──────────────────────────────────────
        f"--add-data={ctk_path}{sep}customtkinter",
        f"--add-data={mpl_path}{sep}matplotlib",
    ]

    if tcl86.exists():
        cmd.extend([
            f"--add-data={tcl86}{sep}tcl8.6",
            f"--add-data={tcl86}{sep}_tcl_data",
            f"--add-data={tcl86}{sep}lib/tcl8.6",
        ])
    if tk86.exists():
        cmd.extend([
            f"--add-data={tk86}{sep}tk8.6",
            f"--add-data={tk86}{sep}_tk_data",
            f"--add-data={tk86}{sep}lib/tk8.6",
        ])

    cmd.extend([
        # ── Hidden imports (modules non détectés automatiquement) ──
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        "--hidden-import=PIL.ImageDraw",
        "--hidden-import=PIL.ImageFont",
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=barcode",
        "--hidden-import=barcode.writer",
        "--hidden-import=matplotlib",
        "--hidden-import=matplotlib.pyplot",
        "--hidden-import=matplotlib.backends.backend_tkagg",
        "--hidden-import=matplotlib.backends._backend_tk",
        "--hidden-import=openpyxl",
        "--hidden-import=sqlite3",
        "--hidden-import=customtkinter",
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=tkinter.messagebox",
        "--hidden-import=hashlib",
        "--hidden-import=threading",
        "--hidden-import=reportlab",
        "--hidden-import=reportlab.platypus",
        "--hidden-import=reportlab.lib.pagesizes",
        "--hidden-import=reportlab.lib.units",
        "--hidden-import=reportlab.lib.styles",
        "--hidden-import=reportlab.lib.colors",
        "--hidden-import=reportlab.lib.enums",
        "--hidden-import=reportlab.pdfgen",
        "--hidden-import=reportlab.graphics",
        "--hidden-import=fitz",
        "--hidden-import=pymupdf",


        # ── Chemins ────────────────────────────────────────────────
        f"--workpath={build_dir}",
        f"--distpath={dist_dir}",

        str(main_py),
    ])

    print(f"\n  Lancement de PyInstaller sur : {main_py}")
    print("  Veuillez patienter (2-5 minutes)...\n")

    result = subprocess.run(cmd, cwd=str(root_dir))

    print()
    if result.returncode == 0:
        # Post-process : s'assurer que les répertoires tcl et tk sont copiés dans tous les emplacements attendus
        cosm_dist = dist_dir / "CosmetiquePro"
        if tcl86.exists():
            for target_loc in [cosm_dist / "lib" / "tcl8.6", cosm_dist / "_internal" / "tcl8.6", cosm_dist / "_internal" / "_tcl_data", cosm_dist / "_internal" / "lib" / "tcl8.6"]:
                if not target_loc.exists():
                    try:
                        shutil.copytree(tcl86, target_loc, dirs_exist_ok=True)
                    except Exception:
                        pass
        if tk86.exists():
            for target_loc in [cosm_dist / "lib" / "tk8.6", cosm_dist / "_internal" / "tk8.6", cosm_dist / "_internal" / "_tk_data", cosm_dist / "_internal" / "lib" / "tk8.6"]:
                if not target_loc.exists():
                    try:
                        shutil.copytree(tk86, target_loc, dirs_exist_ok=True)
                    except Exception:
                        pass

        exe_path = cosm_dist / "CosmetiquePro.exe"
        size_mb = exe_path.stat().st_size / (1024 * 1024) if exe_path.exists() else 0
        print("=" * 65)
        print("  [OK] COMPILATION TERMINEE AVEC SUCCES !")
        print(f"  [->] Dossier  : {cosm_dist}")
        print(f"  [->] Executable : CosmetiquePro.exe  ({size_mb:.1f} Mo)")
        print()
        print("  Pour distribuer l'application, copiez l'integralite du")
        print("  dossier CosmetiquePro/ sur le poste cible.")
        print("=" * 65)
    else:
        print("=" * 65)
        print("  [ERREUR] Echec de la compilation.")
        print("  Verifiez les messages ci-dessus pour les details.")
        print("=" * 65)
        sys.exit(1)


if __name__ == "__main__":
    build()
