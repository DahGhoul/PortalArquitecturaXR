<div align="center">

  <img src="static/img/roo-badge.png" alt="roo Soluciones Digitales" width="420" />

  <br/><br/>

  # Roo Spatial Portal XR
  **Pasarela y Servidor de Distribución de Geometría 3D para Meta Quest & WebXR**

  *Desarrollado por [roo Soluciones Digitales](https://github.com/dahghoul)*  
  *Tecnología con Propósito · El futuro, simple*

  <br/>

  [![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.12%20%7C%203.13-blue?logo=python&logoColor=white)](https://python.org)
  [![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-informational?logo=windows&logoColor=white)](https://github.com)
  [![glTF 2.0](https://img.shields.io/badge/Format-glTF%202.0%20%28.glb%29-orange?logo=khronosgroup&logoColor=white)](https://www.khronos.org/gltf/)
  [![UI](https://img.shields.io/badge/Engine-pywebview%20%2B%20model--viewer-brightgreen)](https://pywebview.flowrl.com/)
  [![Build](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blueviolet?logo=githubactions&logoColor=white)](.github/workflows/build.yml)

</div>

---

## 🌟 Descripción General

**Roo Spatial Portal XR** es una solución corporativa de alto rendimiento desarrollada por **roo Soluciones Digitales**, concebida para conectar estaciones de diseño arquitectónico y modelado 3D con visores de Realidad Extendida (**Meta Quest 2, 3, 3S, Pro** y navegadores WebXR).

Permite transferir, inspeccionar y optimizar proyectos tridimensionales a escala real sin cables, eliminando configuraciones complejas de red y garantizando una tasa de cuadros estable (**90 FPS**) en dispositivos móviles autónomos.

---

## 🚀 Características Principales

### 1. Descubrimiento Automático por Radar UDP
- Transmite paquetes de baliza UDP broadcast en el puerto `47777`.
- Los visores Meta Quest detectan automáticamente la estación de trabajo en la red local y se enlazan mediante un **PIN de 4 dígitos**.

### 2. Transmisión HTTP Eficiente con Range Requests (RFC 7233)
- Soporte nativo para peticiones `bytes` parciales (código HTTP `206 Partial Content`).
- Carga fluida de modelos pesados (+100 MB) con reanudación automática y mínimo uso de búfer en memoria.

### 3. Pipeline de Optimización de Geometría VR (`gltfpack`)
- **Recorrido de Lujo VR (Recomendado):** Fusión inteligente de primitivas por material (`-mm`) conservando el **100% de la geometría intacta** para reducir de miles a menos de 100 las llamadas de dibujado (*draw calls*).
- **Equilibrado VR:** Fusión de mallas con reducción conservadora del 15% de triángulos y protección estricta de bordes (`-slb`) para evitar grietas en peldaños y molduras.
- **Ultra Ligero VR:** Reducción del 50% con bloqueo de bordes para proyectos con alta densidad poligonal (+2M vértices).
- **Sin optimizar:** Almacenamiento directo del archivo de trabajo original sin transformaciones.

### 4. Gestión Inteligente de Almacenamiento (Cero Redundancia)
- Procesa directamente los modelos de trabajo sin almacenar duplicados ocultos.
- Monitor en tiempo real del almacenamiento utilizado en disco.
- Herramientas integradas de **Liberación de residuos** y **Vaciado de modelos** con un solo clic.

### 5. Interfaz Moderna y App de Escritorio Nativa
- Diseñada con CSS Grid adaptable y Container Queries (óptima para monitores de escritorio, laptops, tablets y visores).
- Se ejecuta como ventana de escritorio nativa mediante `pywebview` (utilizando Microsoft Edge WebView2 en Windows o WebKit en macOS), evitando el elevado consumo de RAM de entornos como Electron.
- Visor 3D WebGL integrado bajo demanda (`<model-viewer>`) que libera la GPU cuando está en espera.

---

## 📦 Estructura del Proyecto

```
PortalArquitecto/
├── portal_arquitecto.py        # Núcleo del servidor, radar UDP y motor de optimización
├── PortalArquitecto.spec       # Especificación PyInstaller para Windows y macOS
├── build_windows.bat           # Script de compilación y empaquetado para Windows (.exe)
├── build_mac.sh                # Script de compilación, firma y creación de .dmg para macOS
├── requirements.txt            # Dependencias del proyecto (pywebview, pyinstaller)
├── .gitignore                  # Exclusiones de Git (builds, temporales y modelos pesados)
├── .github/
│   └── workflows/
│       └── build.yml           # Integración continua para generar instaladores en la nube
├── static/                     # Frontend y recursos de la interfaz
│   ├── img/                    # Identidad gráfica (roo Soluciones Digitales)
│   │   ├── roo-logo.png        # Logotipo horizontal institucional
│   │   └── roo-badge.png       # Insignia corporativa y slogans
│   ├── index.html              # Estructura del panel de control
│   ├── styles.css              # Sistema de diseño responsivo
│   ├── app.js                  # Lógica asíncrona de cliente
│   └── vendor/
│       └── model-viewer.min.js # Motor de inspección WebGL
├── modelos_vr/                 # Directorio de trabajo local para modelos .glb
└── herramientas_vr/            # Binarios portables auxiliares (gltfpack)
```

---

## 💻 Instalación y Ejecución

### Entorno de Desarrollo

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/dahghoul/PortalArquitecto.git
   cd PortalArquitecto
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar la aplicación:**
   ```bash
   python portal_arquitecto.py
   ```

> **Consejo:** Para ejecutarlo en modo servidor web estándar abriendo tu navegador habitual en vez de la ventana nativa:
> ```bash
> python portal_arquitecto.py --navegador
> ```

---

## 🛠️ Compilación y Distribución

### Generar Ejecutable para Windows (`.exe`)
Ejecuta en la raíz del proyecto:
```cmd
build_windows.bat
```
El instalador empaquetará la aplicación en `dist\RooSpatialPortal\RooSpatialPortal.exe`.

### Generar Aplicación para macOS (`.app` y `.dmg`)
En un entorno macOS:
```bash
chmod +x build_mac.sh
./build_mac.sh
```
Se generará `dist/RooSpatialPortal.app` y la imagen distribuible `dist/RooSpatialPortal.dmg`.

---

## 🏢 Sobre Nosotros

**roo Soluciones Digitales**  
*Tecnología con Propósito · El futuro, simple*

Especialistas en ingeniería de software, transformación digital, computación espacial y soluciones interactivas para arquitectura, industria y entretenimiento.

---

## 📄 Licencia

Este proyecto está bajo la Licencia Propietaria de **roo Soluciones Digitales**. Todos los derechos reservados.
