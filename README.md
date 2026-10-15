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

## 📐 Guía de Buenas Prácticas de Exportación a .GLB (Para Modeladores y Arquitectos)

> [!IMPORTANT]
> **El 90% de los errores visuales en VR (suelos invisibles, texturas desplazadas, parpadeos coplanares y cuadros blancos en hojas) se originan por vicios de modelado en SketchUp o Revit.** Sigue estrictamente estas reglas antes de exportar a `.glb`:

### 1. Cuadros y Láminas: Importar como "Textura" y NUNCA como "Imagen Suelta"
- **El error común:** En SketchUp es frecuente usar `Archivo > Importar > como Imagen` y pegar una foto, plano o cuadro flotando sobre un muro. Al exportar a glTF/GLB, SketchUp genera una entidad desvinculada que no comparte coordenadas UV con la pared, provocando que la imagen se desfase, flote en el aire o parpadee.
- **La solución correcta:** 
  1. Crea un **Material nuevo**, cárgale la imagen como textura de mapa y **píntala directamente sobre la cara de la pared**.
  2. Si necesitas un cuadro físico: modela un marco con volumen real ($1\text{ a }2\text{ cm}$ de espesor) o, si usas una lámina plana, dale clic derecho > **Explotar** y sepárala al menos **$2\text{ mm}$ hacia afuera del muro** para erradicar el parpadeo coplanar (*Z-Fighting*).

### 2. Muros Estructurales: Geometría Sólida 3D vs Planos 2D
- **El error común:** Usar una imagen plana o un plano 2D de grosor $0$ para simular un tabique o división de ambientes.
- **La solución correcta:** Los sistemas de física en Realidad Virtual (`CharacterController` y `PhysX`) necesitan volumen espacial para frenar al jugador de forma sólida. **Todo muro debe modelarse con grosor real mediante Empujar/Tirar (Push/Pull)** de al menos $10\text{ a }15\text{ cm}$.

### 3. Suelos Invisibles y Caídas al Vacío: Caras Invertidas y Losas con Espesor
- **El error común:** Dibujar una losa o vereda como una simple lámina plana de 1 cara donde el lado azul/gris (reverso) queda hacia arriba. En motores de videojuegos y VR, por optimización de rendimiento se aplica *Backface Culling* (descarte de caras traseras): **el reverso es 100% invisible y verás un agujero hacia el vacío**.
- **La solución correcta:**
  1. **Espesor real:** Toda losa, piso o pavimento debe tener volumen tridimensional con *Empujar/Tirar* (mínimo $15\text{ a }20\text{ cm}$ hacia abajo).
  2. **Orientación de normales:** En SketchUp, las caras visibles desde donde camina el usuario deben ser **blancas**. Si ves alguna cara en tono azulado o grisáceo, selecciónala, haz clic derecho y pulsa **Invertir Caras** (*Reverse Faces*).

### 4. Follaje, Lianas y Vegetación: Fondos Transparentes Reales y Sin Tintes
- **El error común:**
  - Descargar texturas de plantas en formato JPG o con fondos de "cuadritos grises falsos" simulando transparencia: esto genera los temidos **cuadros blancos** o bordes sólidos alrededor de las hojas.
  - Aplicar un tinte o color de muestra sobre la textura en el panel de materiales de SketchUp: esto "destiñe" o apaga el verde fotográfico natural dejándolo grisáceo o plomizo en VR.
- **La solución correcta:**
  1. Usar únicamente imágenes **PNG con canal alfa transparente genuino**.
  2. Conservar el material en su color base blanco puro (`#FFFFFF`) para que el visor respete los colores fotográficos originales de las hojas.
  3. Nombrar el material incluyendo alguna de estas palabras clave: `enredad`, `hoja`, `leaf`, `plant`, `arbol`, `tree` o `liana`. El visor activará automáticamente el sombreador **Alpha Cutout optimizado** sin bordes residuales.

### 5. Vidrios y Ventanas
- **El error común:** Pintar vidrio sobre la misma malla del muro o modelar ventanas sin grupo independiente.
- **La solución correcta:**
  1. Agrupar la carpintería y el cristal en grupos separados.
  2. Asignar al material del cristal una opacidad menor al $70\%$ y nombrarlo con `vidrio`, `glass`, `cristal` o `ventana`. El visor le asignará el shader URP transparente con brillo fotométrico.

### 6. Césped y Terrenos Exteriores
- Nombrar el material con `pasto`, `grass`, `cesped` o `terreno`. El visor aplicará culling de una cara superior para evitar que losas de asfalto o cimientos inferiores se traslapen y parpadeen.

### 7. Limpieza y Purga del Archivo (Regla de Oro antes de Exportar)
1. **Purgar no usados:** En SketchUp ve a `Ventana > Información del modelo > Estadísticas > Purgar no usados`. Esto elimina gigabytes de materiales huérfanos, bloques invisibles y geometrías residuales.
2. **Modelar cerca del Origen (0,0,0):** Asegúrate de que el proyecto esté ubicado cerca del eje de coordenadas inicial. Modelar a cientos de metros del origen causa temblores de cámara (*jittering*) en visores VR por pérdida de precisión numérica.
3. **Formato:** Exportar siempre como **`.glb` binario (glTF 2.0)** con unidades en **metros**. Presupuesto sugerido: menor a $2\text{M}$ de polígonos para Meta Quest autónomo (o usar la optimización con `gltfpack` desde este portal).

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
