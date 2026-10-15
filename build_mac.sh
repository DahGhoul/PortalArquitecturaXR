#!/bin/bash
# Genera dist/PortalArquitecto.app  (ejecutar EN un Mac: chmod +x build_mac.sh && ./build_mac.sh)
set -e
cd "$(dirname "$0")"

python3 -m venv .venv-build
source .venv-build/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt

# gltfpack para macOS (los binarios oficiales son solo Apple Silicon; en Intel usar: brew install meshoptimizer)
if [ ! -f herramientas_vr/gltfpack ] && [ "$(uname -m)" = "arm64" ]; then
    echo "Descargando gltfpack para macOS..."
    curl -fsSL -o /tmp/gltfpack-macos.zip https://github.com/zeux/meshoptimizer/releases/latest/download/gltfpack-macos.zip
    unzip -o -j /tmp/gltfpack-macos.zip "*gltfpack" -d herramientas_vr/
    chmod +x herramientas_vr/gltfpack
fi

pyinstaller --noconfirm --clean PortalArquitecto.spec

# Firma ad-hoc (sin cuenta de Apple Developer). El usuario debera abrirla con clic derecho > Abrir la primera vez.
codesign --force --deep --sign - dist/RooSpatialPortal.app || true

# .dmg de distribucion
hdiutil create -volname "Roo Spatial Portal XR" -srcfolder dist/RooSpatialPortal.app -ov -format UDZO dist/RooSpatialPortal.dmg

echo
echo "========================================================"
echo " Listo: dist/RooSpatialPortal.app y dist/RooSpatialPortal.dmg"
echo " Desarrollado por roo Soluciones Digitales"
echo " Los datos se alojan en: ~/Library/Application Support/RooSpatialPortal/modelos_vr"
echo "========================================================"

