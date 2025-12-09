# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['monitor_gui_tkinter.py'],
    pathex=[],
    binaries=[],
    datas=[('config.py', '.')],
    hiddenimports=['requests', 'email', 'email.mime.text', 'email.mime.multipart', 'smtplib', 'monitor', 'config'],
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
    name='AppleStatusMonitor',
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
    name='AppleStatusMonitor',
)
app = BUNDLE(
    coll,
    name='AppleStatusMonitor.app',
    icon=None,
    bundle_identifier=None,
)
