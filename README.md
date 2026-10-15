# Portal Arquitecto XR (Servidor Local & Visor)

Servidor local ligero y optimizador de geometría 3D glTF (`.glb`) diseñado para transferir y visualizar modelos arquitectónicos de forma inalámbrica en visores **Meta Quest** y visores WebXR.

---

## Características

- **Radar UDP de Descubrimiento Automático:** Emite en broadcast en el puerto `47777` con PIN de seguridad para que el visor Meta Quest se conecte automáticamente sin tener que escribir URLs ni direcciones IP largas.
- **Transmisión HTTP con Range Requests (HTTP 206):** Soporta streaming eficiente y descarga reanudable de modelos masivos (+100 MB).
- **Optimizador de Geometría VR Integrado (`gltfpack`):**
  - **Recorrido de Lujo VR:** Fusión de mallas por material (`-mm`) sin decimar geometría para alcanzar 90 FPS estables en Meta Quest.
  - **Equilibrado VR:** Reducción del 15% con bordes protegidos (`-slb`).
  - **Ultra Ligero VR:** Reducción del 50% para proyectos de alta densidad (+2M polígonos).
- **Cero Redundancia de Almacenamiento:** Procesa y gestiona los archivos de trabajo sin duplicar copias ocultas en disco. Incluye monitor de espacio en disco y herramientas de limpieza en 1 clic.
- **Interfaz Web Responsive & App Nativa:**
  - Diseñada con CSS Grid adaptable y Container Queries (funciona en monitores 4K, laptops, tablets y móviles).
  - Funciona como ventana de escritorio nativa mediante `pywebview` (WebView2 en Windows, WebKit en macOS), sin el consumo excesivo de Chromium/Electron.
  - Visor 3D WebGL bajo demanda (`<model-viewer>`) que no consume GPU mientras está en espera.

---

## Requisitos

- Python 3.10 o superior (compatible con Python 3.12 y 3.13)
- Windows 10/11 o macOS 12+

---

## Instalación y Uso en Desarrollo

1. Clona el repositorio:
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd PortalArquitecto
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Ejecuta la aplicación:
   ```bash
   python portal_arquitecto.py
   ```

> **Nota:** Si deseas ejecutarlo en modo servidor tradicional (abriendo una pestaña en tu navegador habitual en lugar de una ventana nativa), puedes usar:
> ```bash
> python portal_arquitecto.py --navegador
> ```

---

## Empaquetado para Distribución

### Windows (.exe)
Ejecuta el script:
```cmd
build_windows.bat
```
Generará la carpeta autocontenida: `dist\PortalArquitecto\PortalArquitecto.exe`.

### macOS (.app y .dmg)
En una máquina con macOS (Apple Silicon o Intel):
```bash
chmod +x build_mac.sh
./build_mac.sh
```
Generará `dist/PortalArquitecto.app` y la imagen de disco `dist/PortalArquitecto.dmg`.

### Compilación Automática en la Nube (GitHub Actions)
El repositorio incluye el flujo `.github/workflows/build.yml`. Si no tienes una Mac física, puedes ejecutar la acción desde la pestaña **Actions** en GitHub o crear un tag (`v1.0.0`) para que GitHub compile automáticamente las versiones de Windows y macOS.

---

## Estructura del Proyecto

```
PortalArquitecto/
├── portal_arquitecto.py     # Servidor HTTP, radar UDP y lógica de optimización
├── PortalArquitecto.spec    # Especificación de PyInstaller (Windows y macOS)
├── build_windows.bat        # Script de build para Windows
├── build_mac.sh             # Script de build para macOS
├── requirements.txt         # Dependencias Python (pywebview, pyinstaller)
├── .gitignore               # Exclusiones de Git (temporales, builds, modelos pesados)
├── static/                  # Frontend web / UI
│   ├── index.html           # Estructura de la aplicación
│   ├── styles.css           # Estilos responsivos
│   ├── app.js               # Lógica del cliente
│   └── vendor/              # model-viewer WebGL
├── modelos_vr/              # Carpeta de trabajo para modelos .glb
└── herramientas_vr/         # Binarios portables auxiliares (gltfpack)
```
