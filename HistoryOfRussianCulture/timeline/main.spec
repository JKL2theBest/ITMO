# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('1.jpg', '.'), ('2.jpg', '.'), ('3.jpg', '.'), ('4.jpg', '.'), ('5.jpg', '.'), ('6.jpg', '.'), ('7.jpg', '.'), ('8.jpg', '.'), ('9.jpg', '.'), ('10.jpg', '.'), ('11.jpg', '.'), ('12.jpg', '.'), ('13.jpg', '.'), ('14.jpg', '.'), ('15.jpg', '.'), ('16.jpg', '.'), ('17.jpg', '.'), ('18.jpg', '.'), ('19.jpg', '.'), ('20.jpg', '.'), ('21.jpg', '.'), ('22.jpg', '.'), ('23.jpg', '.'), ('24.jpg', '.'), ('25.jpg', '.'), ('26.jpg', '.'), ('27.jpg', '.'), ('28.jpg', '.'), ('29.jpg', '.'), ('30.jpg', '.'), ('31.jpg', '.'), ('32.jpg', '.'), ('33.jpg', '.'), ('34.jpg', '.'), ('35.jpg', '.'), ('36.jpg', '.'), ('37.jpg', '.'), ('38.jpg', '.'), ('39.jpg', '.'), ('40.jpg', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
