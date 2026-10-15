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
    exclude_binaries=True,       # modo carpeta (onedir): arranca mas rapido que onefile
    name="PortalArquitecto",
    console=False,               # sin ventana negra de consola
    upx=False,                   # UPX dispara falsos positivos de antivirus
    icon=None,                   # pon aqui "icono.ico" (Windows) / "icono.icns" (macOS)
)

coll = COLLECT(exe, a.binaries, a.datas, name="PortalArquitecto", upx=False)

if ES_MAC:
    app = BUNDLE(
        coll,
        name="PortalArquitecto.app",
        icon=None,
        bundle_identifier="com.portalarquitecto.app",
        info_plist={
            "CFBundleDisplayName": "Portal Arquitecto XR",
            "CFBundleShortVersionString": "1.0.0",
            "NSHighResolutionCapable": True,
            # macOS 15+ pide permiso para la red local (radar UDP hacia el Meta Quest)
            "NSLocalNetworkUsageDescription": "Necesario para que el visor Meta Quest encuentre este equipo en la red local.",
        },
    )

