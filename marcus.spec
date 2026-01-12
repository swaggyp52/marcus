# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Marcus v0.5.2
Packages the application with all dependencies and static files
"""

import sys
from pathlib import Path

block_cipher = None

# Define paths
project_root = Path(SPECPATH)
frontend_path = project_root / 'frontend'
static_path = frontend_path / 'static'

# Collect all frontend files
frontend_data = []
if frontend_path.exists():
    frontend_data.append((str(frontend_path / 'index.html'), 'frontend'))
    if static_path.exists():
        for subdir in ['css', 'js']:
            subdir_path = static_path / subdir
            if subdir_path.exists():
                for file in subdir_path.glob('*'):
                    if file.is_file():
                        frontend_data.append((str(file), f'frontend/static/{subdir}'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=frontend_data,
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'sqlmodel',
        'pydantic',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Marcus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window for desktop app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon file path here if you have one
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # Disabled for better antivirus compatibility
    upx_exclude=[],
    name='Marcus',
)
