# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['ui\\ui_meta_analysis.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ui\\assets', 'assets'),
    ],
    hiddenimports=[
        'folium',
        'branca',
        'branca.colormap',
        'branca.element',
        'jinja2',
        'jinja2.ext',
        'reportlab',
        'reportlab.lib',
        'reportlab.platypus',
        'reportlab.lib.pagesizes',
        'reportlab.lib.styles',
        'reportlab.lib.colors',
        'pandas',
        'PIL',
        'PIL.Image',
        'PyPDF2',
        'docx',
        'hashlib',
        'http.server',
        'socketserver',
        'threading',
    ],
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
    name='MetaAnalisis',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='ui\\assets\\icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='MetaAnalisis',
)