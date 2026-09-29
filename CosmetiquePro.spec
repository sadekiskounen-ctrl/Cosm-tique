# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:/Users/hppor/OneDrive/Desktop/gestion cosmétique/main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/hppor/AppData/Local/Programs/Python/Python313/Lib/site-packages/customtkinter', 'customtkinter'), ('C:/Users/hppor/AppData/Local/Programs/Python/Python313/Lib/site-packages/matplotlib', 'matplotlib'), ('C:/Users/hppor/AppData/Local/Programs/Python/Python313/tcl/tcl8.6', 'tcl8.6'), ('C:/Users/hppor/AppData/Local/Programs/Python/Python313/tcl/tcl8.6', '_tcl_data'), ('C:/Users/hppor/AppData/Local/Programs/Python/Python313/tcl/tcl8.6', 'lib/tcl8.6'), ('C:/Users/hppor/AppData/Local/Programs/Python/Python313/tcl/tk8.6', 'tk8.6'), ('C:/Users/hppor/AppData/Local/Programs/Python/Python313/tcl/tk8.6', '_tk_data'), ('C:/Users/hppor/AppData/Local/Programs/Python/Python313/tcl/tk8.6', 'lib/tk8.6')],
    hiddenimports=['PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont', 'PIL._tkinter_finder', 'barcode', 'barcode.writer', 'matplotlib', 'matplotlib.pyplot', 'matplotlib.backends.backend_tkagg', 'matplotlib.backends._backend_tk', 'openpyxl', 'sqlite3', 'customtkinter', 'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'hashlib', 'threading', 'reportlab', 'reportlab.platypus', 'reportlab.lib.pagesizes', 'reportlab.lib.units', 'reportlab.lib.styles', 'reportlab.lib.colors', 'reportlab.lib.enums', 'reportlab.pdfgen', 'reportlab.graphics', 'fitz', 'pymupdf'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CosmetiquePro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CosmetiquePro',
)
