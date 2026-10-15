<div align="center">

<img src="static/img/roo-logo.png" alt="roo | Soluciones Digitales" width="460" />

# Portal Arquitectura XR
### Servidor Local, Hub de Modelos 3D y Radar de Distribución para Meta Quest & WebXR

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.12%20%7C%203.13-blue?logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-informational?logo=windows&logoColor=white)](https://github.com)
[![glTF 2.0](https://img.shields.io/badge/Format-glTF%202.0%20%28.glb%29-orange?logo=khronosgroup&logoColor=white)](https://www.khronos.org/gltf/)
[![UI](https://img.shields.io/badge/Engine-pywebview%20%2B%20model--viewer-brightgreen)](https://pywebview.flowrl.com/)
[![Ecosystem](https://img.shields.io/badge/Ecosistema-roo_AEC_Spatial_Suite-purple.svg)](#ecosistema-arquitectura-mr--xr)

<br/>

<img src="static/img/roo-badge.png" alt="Tecnología con Propósito — El futuro, simple" width="220" />

<p><em>"Tecnología con Propósito — El futuro, simple"</em></p>

---

### **Desarrollado por:**
**Diego Joel Cuba Moya** & **Ronaldo Carlos Robles Romero**  
**Empresa:** [roo | Soluciones Digitales](https://github.com/roo-soluciones)

</div>

---

## 🏛️ Ecosistema Arquitectura MR / XR

Este proyecto forma parte de la suite espacial de **roo | Soluciones Digitales**, compuesta por dos sistemas complementarios diseñados para trabajar en sincronía sin cables:

```
┌────────────────────────────────────────┐       Wi-Fi Local (5 GHz)        ┌────────────────────────────────────────┐
│     PORTAL ARQUITECTURA XR (PC)        │  ◄════════════════════════════►  │       VISOR ARQUITECTURA MR (VR)       │
│                                        │   UDP Radar Broadcast (47777)    │                                        │
│ • Servidor HTTP multihilo (RFC 7233)   │   HTTP Range Streaming (8000)    │ • Cliente inmersivo Meta Quest (Unity) │
│ • Sincronización y emparejamiento PIN  │                                  │ • Pipeline Universal URP PBR 90 FPS    │
│ • Optimizador de mallas (gltfpack)     │                                  │ • Modos: Peatón 1:1, Dron, Maqueta AR  │
│ • Panel Web y Desktop (pywebview)      │                                  │ • Interfaz curva World-Space VisionOS  │
└────────────────────────────────────────┘                                  └────────────────────────────────────────┘
```

1. **[Portal Arquitectura XR](https://github.com/roo-soluciones/portal-arquitectura-xr) (Este repositorio / PC):**  
   Aplicación de escritorio y servidor local para la laptop o estación de trabajo del arquitecto. Gestiona la carga de archivos `.glb`, optimiza mallas con `gltfpack`, emite la señal de radar UDP y transmite los modelos de forma ultrarrápida.
2. **[Visor Arquitectura MR](https://github.com/roo-soluciones/VisorArquitecturaMR) (Unity / Meta Quest):**  
   Aplicación inmersiva para visores Meta Quest (2, 3, 3S, Pro) y PC VR. Detecta automáticamente la PC en la red, descarga el modelo y permite recorrerlo a escala 1:1, sobrevolarlo como dron o manipularlo como maqueta en la mesa mediante Passthrough.

---

## 🌟 Características Principales

### 1. Descubrimiento Automático por Radar UDP
- Emite balizas UDP broadcast continuas en el puerto `47777`.
- El visor Meta Quest detecta de inmediato el servidor sin necesidad de escribir direcciones IP manuales.
- Incluye vinculación de respaldo por **código PIN de 4 dígitos** para redes corporativas con aislamiento de broadcast.

### 2. Transmisión HTTP Eficiente con Range Requests (RFC 7233)
- Soporte nativo para peticiones parciales por rangos de bytes (`HTTP 206 Partial Content`).
- Descarga fluida de proyectos pesados (+100 MB a +1 GB) sin bloquear la memoria RAM ni saturar la conexión inalámbrica.

### 3. Pipeline de Optimización VR Integrado (`gltfpack`)
- **Recorrido de Lujo VR (Recomendado):** Fusión de primitivas geométricas por material (`-mm`), reduciendo de miles a menos de 100 las llamadas de dibujado (*draw calls*) y preservando el **100% de la geometría intacta**.
- **Equilibrado VR:** Fusión de mallas con reducción conservadora del 15% de triángulos y protección estricta de bordes (`-slb`) para escalones y cornisas.
- **Ultra Ligero VR:** Reducción del 50% para proyectos con densidades masivas (+2M polígonos).
- **Sin optimizar:** Almacenamiento directo del archivo de trabajo original sin transformaciones.

### 4. Interfaz Moderna y App de Escritorio Nativa
- Ejecución de escritorio ultraligera mediante `pywebview` (utilizando Microsoft Edge WebView2 en Windows o WebKit en macOS), evitando el excesivo consumo de memoria de Electron.
- Visor 3D WebGL integrado bajo demanda (`<model-viewer>`) con liberación automática de GPU al salir del modo de inspección.

---

## 📐 Guía de Modelado y Exportación para Arquitectos y Diseñadores

Para asegurar que los modelos se visualicen con máxima fidelidad, sin errores visuales ni caídas de fotogramas en el visor Meta Quest, el equipo de modelado (SketchUp, Revit, Blender, Archicad, Rhino) debe considerar las siguientes pautas:

| Parámetro | Recomendación Óptima | Problema que evita |
| :--- | :--- | :--- |
| **Formato de Exportación** | **`.glb` binario (glTF 2.0)** | Evita carpetas de texturas sueltas o rutas rotas; todo viaja encapsulado. |
| **Escala Métrica** | **$1 \text{ unidad} = 1 \text{ metro}$** | Aunque el visor auto-reescala si detecta mm o cm, exportar en metros asegura que el spawn y la altura de ojos sean exactos. |
| **Orientación de Caras** | **Caras frontales hacia afuera** (blancas en SketchUp) | Evita sombreados oscurecidos o caras invertidas. En SketchUp: *Invertir Caras* si se muestran en tono azul/gris. |
| **Vidrios y Cristales** | Nombrar con `vidrio`, `glass`, `cristal` o `ventana` | El visor los clasifica automáticamente como material URP transparente con brillo fotométrico. |
| **Vegetación y Hojas** | Nombrar con `enredad`, `hoja`, `leaf`, `plant` o `arbol` | Activa el pipeline Cutout con Alpha Clipping (`_ALPHATEST_ON`), eliminando cuadros blancos y respetando tonos fotográficos. |
| **Césped y Terreno** | Nombrar con `pasto`, `grass`, `cesped` o `terreno` | Aplica culling superior, evitando que losas o asfaltos coplanares inferiores se traslapen (*z-fighting*). |
| **Cuadros y Láminas Murales** | Separar al menos $1 \text{ a } 2 \text{ mm}$ del muro base | Previene el parpadeo de texturas coplanares cuando dos caras comparten exactamente la misma coordenada. |
| **Presupuesto Poligonal** | **Menor a $2\text{M}$ de triángulos** para Meta Quest autónomo | Asegura 90 FPS estables. Modelos más pesados deben optimizarse desde este portal usando *Recorrido de Lujo VR*. |

---

## 📋 Requisitos del Sistema

### Para Portal Arquitectura XR (Estación PC):
- **Sistema Operativo:** Windows 10/11 (64-bit) o macOS 12+ (Apple Silicon o Intel).
- **Entorno:** Python 3.10 o superior (si se corre desde código fuente) o el ejecutable portable empaquetado `.exe` / `.app`.
- **Puertos de Red:** `8000` TCP (Servidor HTTP) y `47777` UDP (Radar broadcast).
- **Conectividad:** Conexión a la misma red Wi-Fi que el visor Meta Quest (se recomienda router Wi-Fi 5 GHz o 6 GHz).

### Para Visor Arquitectura MR (Visor VR):
- **Dispositivo:** Meta Quest 2, Meta Quest 3, Meta Quest 3S o Meta Quest Pro.
- **Instalación:** Paquete `.apk` instalado mediante SideQuest o Meta Quest Developer Hub.

---

## 💻 Instalación y Ejecución

### Opción A: Ejecución desde Código Fuente (Python)

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/roo-soluciones/portal-arquitectura-xr.git
   cd portal-arquitectura-xr
   ```

2. **Crear entorno virtual e instalar dependencias:**
   ```bash
   python -m venv .venv
   # En Windows:
   .venv\Scripts\activate
   # En macOS/Linux:
   source .venv/bin/activate

   pip install -r requirements.txt
   ```

3. **Ejecutar la aplicación:**
   ```bash
   python portal_arquitecto.py
   ```

   > **Modo Navegador:** Si prefieres abrirlo en tu navegador habitual sin ventana nativa pywebview:
   > ```bash
   > python portal_arquitecto.py --navegador
   > ```

### Opción B: Compilación a Ejecutable Nativo

- **En Windows (`.exe`):**
  Ejecuta `build_windows.bat`. El ejecutable quedará generado en `dist\PortalArquitecturaXR\PortalArquitecturaXR.exe`.
- **En macOS (`.app` y `.dmg`):**
  Ejecuta `./build_mac.sh`. Se generará el paquete en `dist/PortalArquitecturaXR.app`.

---

## 📦 Estructura del Repositorio

```
portal-arquitectura-xr/
├── portal_arquitecto.py        # Núcleo del servidor, radar UDP y motor de optimización
├── PortalArquitecto.spec       # Receta de empaquetado PyInstaller para Windows y macOS
├── build_windows.bat           # Script de compilación desatendida para Windows
├── build_mac.sh                # Script de compilación, firma y creación de .dmg para macOS
├── requirements.txt            # Dependencias del proyecto (pywebview, pyinstaller)
├── .gitignore                  # Reglas de exclusión de Git (builds, temporales y modelos pesados)
├── .github/
│   └── workflows/
│       └── build.yml           # Integración continua para generar instaladores en GitHub Actions
├── static/                     # Frontend web responsive de la aplicación
│   ├── img/                    # Identidad gráfica institucional (roo Soluciones Digitales)
│   │   ├── roo-logo.png        # Logotipo horizontal institucional
│   │   └── roo-badge.png       # Insignia corporativa
│   ├── index.html              # Panel de control del portal
│   ├── styles.css              # Sistema de diseño dark
│   ├── app.js                  # Lógica de interacción y carga asíncrona
│   └── vendor/
│       └── model-viewer.min.js # Motor de previsualización 3D WebGL
├── modelos_vr/                 # Carpeta de trabajo para modelos .glb cargados
└── herramientas_vr/            # Binarios auxiliares portables (gltfpack)
```

---

## 📄 Licencia y Créditos

Este software ha sido diseñado y desarrollado como propiedad intelectual de:

**roo | Soluciones Digitales**  
*Lema:* **"Tecnología con Propósito — El futuro, simple"**

**Desarrolladores Principales:**
- **Diego Joel Cuba Moya**
- **Ronaldo Carlos Robles Romero**

*Copyright © 2026 roo Soluciones Digitales. Todos los derechos reservados.*
