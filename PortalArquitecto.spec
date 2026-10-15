# -*- mode: python ; coding: utf-8 -*-
# Receta de PyInstaller para Windows y macOS.
# PyInstaller NO compila de forma cruzada: el .exe se genera en Windows y el .app en un Mac.
#   Windows: build_windows.bat      macOS: ./build_mac.sh
import os
import sys

ES_WIN = sys.platform == "win32"
ES_MAC = sys.platform == "darwin"

# gltfpack del sistema operativo actual (si falta, la app lo descarga la primera vez que optimiza)
gltfpack = os.path.join("herramientas_vr", "gltfpack.exe" if ES_WIN else "gltfpack")
binarios = [(gltfpack, "herramientas_vr")] if os.path.isfile(gltfpack) else []

a = Analysis(
    ["portal_arquitecto.py"],
    pathex=[],
    binaries=binarios,
    datas=[("static", "static")],
    hiddenimports=[],
    excludes=["tkinter", "unittest", "pydoc"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RooSpatialPortal",
    console=False,
    upx=False,
    icon=None,
)

coll = COLLECT(exe, a.binaries, a.datas, name="RooSpatialPortal", upx=False)

if ES_MAC:
    app = BUNDLE(
        coll,
        name="RooSpatialPortal.app",
        icon=None,
        bundle_identifier="com.roosoluciones.spatialportal",
        info_plist={
            "CFBundleDisplayName": "Roo Spatial Portal XR",
            "CFBundleShortVersionString": "1.2.0",
            "NSHighResolutionCapable": True,
            "NSLocalNetworkUsageDescription": "Necesario para que el visor Meta Quest descubra este equipo mediante broadcast en la red local.",
        },
    )

