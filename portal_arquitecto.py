# ================================================================================================
# PROYECTO: Portal Arquitectura XR (Servidor Local & Hub de Modelos 3D)
# EMPRESA: roo | Soluciones Digitales
# LEMA: "Tecnología con Propósito — El futuro, simple"
# AUTORES: Diego Joel Cuba Moya & Ronaldo Carlos Robles Romero
# COPYRIGHT: © 2026 roo Soluciones Digitales. Todos los derechos reservados.
# ================================================================================================

"""
Portal Arquitectura XR (roo Spatial Portal)
===========================================
Pasarela de Geometria 3D y Servidor de Distribucion Local para Meta Quest & WebXR.
Desarrollado por roo | Soluciones Digitales.
Autores: Diego Joel Cuba Moya & Ronaldo Carlos Robles Romero.
Filosofia: "Tecnologia con Proposito — El futuro, simple"

Arquitectura:
- Servidor HTTP multihilo compatible con RFC 7233 (Range Requests) para streaming 3D.
- Radar UDP broadcast (puerto 47777) para autodescubrimiento sin configuracion de red.
- Pipeline de optimizacion glTF 2.0 (meshopt / gltfpack) con presets adaptados a Meta Quest.
- Interfaz nativa desacoplada basada en el motor web del sistema operativo (pywebview).
"""

import os
import sys
import json
import time
import struct
import socket
import shutil
import zipfile
import threading
import subprocess
import webbrowser
import mimetypes
import urllib.request
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

# Metadatos del Software y Branding Institucional
APP_NAME = "Portal Arquitectura XR"
APP_VERSION = "1.2.0"
COMPANY_NAME = "roo | Soluciones Digitales"
SLOGAN = "Tecnología con Propósito — El futuro, simple"
AUTHORS = "Diego Joel Cuba Moya & Ronaldo Carlos Robles Romero"

HTTP_PORT_DEFAULT = 8000
UDP_RADAR_PORT = 47777
MAX_UPLOAD_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB maximo por modelo GLB


def carpeta_datos_usuario():
    """
    Determina la ruta del directorio de almacenamiento persistente del usuario
    segun el estandar de cada sistema operativo (evita escrituras en directorios
    restringidos como Program Files o paquetes .app en macOS).
    """
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, "RooSpatialPortal")


# Resolucion de rutas segun entorno (ejecucion directa vs empaquetado binario)
ES_EMPAQUETADO = getattr(sys, "frozen", False)
if ES_EMPAQUETADO:
    BASE_DIR = carpeta_datos_usuario()
    RECURSOS_DIR = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RECURSOS_DIR = BASE_DIR

CARPETA_STATIC = os.path.join(RECURSOS_DIR, "static")
CARPETA_TOOLS_INCLUIDAS = os.path.join(RECURSOS_DIR, "herramientas_vr")
CARPETA_MODELOS = os.path.join(BASE_DIR, "modelos_vr")
CARPETA_ORIGINALES = os.path.join(CARPETA_MODELOS, ".originales")
CARPETA_TOOLS = os.path.join(BASE_DIR, "herramientas_vr")
ARCHIVO_ESTADO = os.path.join(CARPETA_MODELOS, "_estado.json")

os.makedirs(CARPETA_MODELOS, exist_ok=True)
os.makedirs(CARPETA_TOOLS, exist_ok=True)

# Redireccion segura de flujos estandar en entornos sin terminal interactiva
if sys.stdout is None or sys.stderr is None:
    _log = open(os.path.join(BASE_DIR, "roo_portal.log"), "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stdout or _log
    sys.stderr = sys.stderr or _log

LOCK_ESTADO = threading.Lock()
PUERTO_HTTP = HTTP_PORT_DEFAULT
PUERTO_UDP_RADAR = UDP_RADAR_PORT


def obtener_ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def generar_codigo_pin(ip):
    partes = ip.split(".")
    if len(partes) == 4:
        subred = int(partes[2]) % 10
        host = int(partes[3])
        return f"{subred}{host:03d}"
    return "0000"


def iniciar_radar_udp():
    def bucle_radar():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        nombre_pc = socket.gethostname()
        while True:
            try:
                ip = obtener_ip_local()
                pin = generar_codigo_pin(ip)
                mensaje = json.dumps({
                    "tipo": "VISOR_ARQ_SERVER",
                    "app": APP_NAME,
                    "version": APP_VERSION,
                    "empresa": COMPANY_NAME,
                    "url": f"http://{ip}:{PUERTO_HTTP}",
                    "ip": ip,
                    "pin": pin,
                    "pc": nombre_pc,
                    "modelo_activo": obtener_modelo_activo()
                }).encode("utf-8")
                sock.sendto(mensaje, ("255.255.255.255", PUERTO_UDP_RADAR))
            except Exception:
                pass
            time.sleep(2.0)

    hilo = threading.Thread(target=bucle_radar, daemon=True)
    hilo.start()


def analizar_glb(ruta_glb):
    """Devuelve dict con draw_calls, mallas, triangulos, nodos_con_malla, texturas."""
    vacio = {"draw_calls": 0, "mallas": 0, "triangulos": 0, "instancias": 0, "texturas": 0}
    try:
        with open(ruta_glb, "rb") as f:
            cabecera = f.read(12)
            if len(cabecera) < 12:
                return vacio
            magic, _version, _length = struct.unpack("<III", cabecera)
            if magic != 0x46546C67:
                return vacio
            chunk_len, _chunk_type = struct.unpack("<II", f.read(8))
            datos = json.loads(f.read(chunk_len).decode("utf-8", errors="ignore"))

        mallas = datos.get("meshes", [])
        accesores = datos.get("accessors", [])
        draw_calls = 0
        triangulos = 0
        tri_por_malla = []
        for m in mallas:
            t_malla = 0
            for p in m.get("primitives", []):
                draw_calls += 1
                modo = p.get("mode", 4)
                idx = p.get("indices")
                if idx is not None and idx < len(accesores):
                    n = accesores[idx].get("count", 0)
                else:
                    pos = p.get("attributes", {}).get("POSITION")
                    n = accesores[pos].get("count", 0) if pos is not None and pos < len(accesores) else 0
                if modo == 4:
                    t_malla += n // 3
                elif modo in (5, 6):
                    t_malla += max(n - 2, 0)
            tri_por_malla.append(t_malla)
            triangulos += t_malla

        # Triangulos reales contando instancias (nodos que reutilizan una malla)
        instancias = 0
        triangulos_instanciados = 0
        for n in datos.get("nodes", []):
            mi = n.get("mesh")
            if mi is not None and mi < len(tri_por_malla):
                instancias += 1
                triangulos_instanciados += tri_por_malla[mi]

        return {
            "draw_calls": draw_calls,
            "mallas": len(mallas),
            "triangulos": triangulos_instanciados or triangulos,
            "instancias": instancias,
            "texturas": len(datos.get("images", []))
        }
    except Exception:
        return vacio


def contar_piezas_glb(ruta_glb):
    a = analizar_glb(ruta_glb)
    return a["draw_calls"], a["mallas"]


def obtener_ruta_gltfpack():
    nombre_bin = "gltfpack.exe" if os.name == "nt" else "gltfpack"
    for carpeta in (CARPETA_TOOLS_INCLUIDAS, CARPETA_TOOLS):
        ruta = os.path.join(carpeta, nombre_bin)
        if os.path.isfile(ruta):
            if os.name != "nt" and not os.access(ruta, os.X_OK):
                try:
                    os.chmod(ruta, 0o755)
                except OSError:
                    continue
            return ruta
    return shutil.which("gltfpack")


def descargar_optimizador_portable():
    """Usa gltfpack local; solo descarga si no existe (requiere internet una vez)."""
    ruta_existente = obtener_ruta_gltfpack()
    if ruta_existente:
        return ruta_existente
    try:
        url_api = "https://api.github.com/repos/zeux/meshoptimizer/releases/latest"
        req = urllib.request.Request(url_api, headers={"User-Agent": "VisorArquitecturaVR"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            release_info = json.loads(resp.read().decode("utf-8"))

        sufijo = "windows.zip" if os.name == "nt" else ("macos.zip" if sys.platform == "darwin" else "ubuntu.zip")
        url_descarga = None
        for asset in release_info.get("assets", []):
            if asset["name"].endswith(sufijo):
                url_descarga = asset["browser_download_url"]
                break
        if not url_descarga:
            return None

        zip_temp = os.path.join(CARPETA_TOOLS, "gltfpack_temp.zip")
        urllib.request.urlretrieve(url_descarga, zip_temp)
        with zipfile.ZipFile(zip_temp, "r") as z:
            for member in z.namelist():
                if "gltfpack" in os.path.basename(member):
                    nombre_final = "gltfpack.exe" if os.name == "nt" else "gltfpack"
                    destino = os.path.join(CARPETA_TOOLS, nombre_final)
                    with z.open(member) as origen, open(destino, "wb") as salida:
                        shutil.copyfileobj(origen, salida)
                    if os.name != "nt":
                        os.chmod(destino, 0o755)
                    break
        if os.path.exists(zip_temp):
            os.remove(zip_temp)
        return obtener_ruta_gltfpack()
    except Exception:
        return None


def _info_resultado(optimizado, mensaje, antes, despues, peso_antes, peso_despues):
    return {
        "optimizado": optimizado,
        "mensaje": mensaje,
        "nodos_antes": antes,
        "nodos_despues": despues,
        "peso_antes_mb": round(peso_antes / (1024 * 1024), 2),
        "peso_despues_mb": round(peso_despues / (1024 * 1024), 2)
    }


def calcular_almacenamiento():
    """Calcula el espacio ocupado por modelos y por respaldos/temporales residuales."""
    total_bytes = 0
    temporales_bytes = 0
    modelos_bytes = 0
    conteo_temporales = 0

    if os.path.exists(CARPETA_MODELOS):
        for raiz, _dirs, archivos in os.walk(CARPETA_MODELOS):
            for f in archivos:
                ruta = os.path.join(raiz, f)
                try:
                    tam = os.path.getsize(ruta)
                    total_bytes += tam
                    es_temp = (
                        os.path.basename(raiz) == ".originales"
                        or f.endswith((".bak", ".part", ".tmp", ".opt.glb"))
                    )
                    if es_temp:
                        temporales_bytes += tam
                        conteo_temporales += 1
                    elif f.lower().endswith(".glb"):
                        modelos_bytes += tam
                except OSError:
                    pass

    return {
        "total_mb": round(total_bytes / (1024 * 1024), 1),
        "temporales_mb": round(temporales_bytes / (1024 * 1024), 1),
        "modelos_mb": round(modelos_bytes / (1024 * 1024), 1),
        "conteo_temporales": conteo_temporales
    }


def limpiar_archivos_temporales():
    """Elimina copias viejas en .originales, archivos .bak, .part y .tmp para liberar espacio."""
    liberados = 0
    # 1. Borrar carpeta .originales si existe de versiones anteriores
    if os.path.exists(CARPETA_ORIGINALES):
        for raiz, _, archivos in os.walk(CARPETA_ORIGINALES):
            for f in archivos:
                try:
                    liberados += os.path.getsize(os.path.join(raiz, f))
                except OSError:
                    pass
        try:
            shutil.rmtree(CARPETA_ORIGINALES, ignore_errors=True)
        except Exception:
            pass

    # 2. Borrar .bak, .part, .tmp, .opt.glb dentro de CARPETA_MODELOS
    if os.path.exists(CARPETA_MODELOS):
        for f in os.listdir(CARPETA_MODELOS):
            if f.endswith((".bak", ".part", ".tmp", ".opt.glb")):
                rf = os.path.join(CARPETA_MODELOS, f)
                try:
                    liberados += os.path.getsize(rf)
                    os.remove(rf)
                except OSError:
                    pass

    return round(liberados / (1024 * 1024), 1)


def vaciar_todos_los_modelos():
    """Elimina todos los modelos alojados y resetea el visor."""
    liberados = 0
    if os.path.exists(CARPETA_MODELOS):
        for f in os.listdir(CARPETA_MODELOS):
            if f == "_estado.json":
                continue
            rf = os.path.join(CARPETA_MODELOS, f)
            try:
                if os.path.isfile(rf):
                    liberados += os.path.getsize(rf)
                    os.remove(rf)
                elif os.path.isdir(rf):
                    for raiz, _, archivos in os.walk(rf):
                        for a in archivos:
                            try:
                                liberados += os.path.getsize(os.path.join(raiz, a))
                            except OSError:
                                pass
                    shutil.rmtree(rf, ignore_errors=True)
            except OSError:
                pass

    def reset_est(est):
        est["modelo_activo"] = ""
        est["historial"] = {}
    modificar_estado(reset_est)

    return round(liberados / (1024 * 1024), 1)


def procesar_modelo_glb(ruta_entrada, modo_optimizacion):
    """Optimiza directamente el GLB sin duplicarlo en .originales (cero redundancia)."""
    piezas_antes, _ = contar_piezas_glb(ruta_entrada)
    peso_antes = os.path.getsize(ruta_entrada)

    if modo_optimizacion == "preservar":
        return _info_resultado(False, "Geometria original conservada", piezas_antes, piezas_antes, peso_antes, peso_antes)

    ejecutable = descargar_optimizador_portable()
    if not ejecutable:
        return _info_resultado(False, "Optimizador no disponible", piezas_antes, piezas_antes, peso_antes, peso_antes)

    ruta_temp = ruta_entrada + ".opt.glb"
    try:
        # Selección de flags según modo de optimización
        if modo_optimizacion in ("lujo", "max_quest", "fusionar"):
            cmd = [ejecutable, "-i", ruta_entrada, "-o", ruta_temp, "-noq", "-mm"]
            etiqueta = "Recorrido de Lujo VR (Geometria 100% Intacta, 90 FPS)"
        elif modo_optimizacion == "equilibrado":
            cmd = [ejecutable, "-i", ruta_entrada, "-o", ruta_temp, "-noq", "-mm", "-si", "0.85", "-slb"]
            etiqueta = "Equilibrado VR (Fusión + 15% reduccion con bordes seguros)"
        elif modo_optimizacion in ("ultra", "extremo"):
            cmd = [ejecutable, "-i", ruta_entrada, "-o", ruta_temp, "-noq", "-mm", "-si", "0.5", "-slb"]
            etiqueta = "Ultra Ligero VR (Fusión + 50% reduccion con bordes seguros)"
        elif modo_optimizacion == "compactar":
            cmd = [ejecutable, "-i", ruta_entrada, "-o", ruta_temp, "-kn", "-noq"]
            etiqueta = "Compactado de buffers"
        else:
            cmd = [ejecutable, "-i", ruta_entrada, "-o", ruta_temp, "-noq", "-mm"]
            etiqueta = "Recorrido de Lujo VR"

        extra = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=300, **extra)

        if res.returncode == 0 and os.path.exists(ruta_temp):
            piezas_despues, _ = contar_piezas_glb(ruta_temp)
            peso_despues = os.path.getsize(ruta_temp)
            shutil.move(ruta_temp, ruta_entrada)
            return _info_resultado(True, f"{etiqueta} ({piezas_antes} -> {piezas_despues} mallas)",
                                   piezas_antes, piezas_despues, peso_antes, peso_despues)
    except Exception as e:
        print(f"[ERROR] Fallo en optimizacion: {e}")
    finally:
        if os.path.exists(ruta_temp):
            os.remove(ruta_temp)

    return _info_resultado(False, "Sin cambios", piezas_antes, piezas_antes, peso_antes, peso_antes)


def leer_estado():
    if os.path.exists(ARCHIVO_ESTADO):
        try:
            with open(ARCHIVO_ESTADO, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"modelo_activo": "", "historial": {}}


def guardar_estado(datos):
    tmp = ARCHIVO_ESTADO + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    os.replace(tmp, ARCHIVO_ESTADO)


def modificar_estado(funcion):
    """Lectura-modificacion-escritura atomica protegida por lock."""
    with LOCK_ESTADO:
        est = leer_estado()
        est.setdefault("historial", {})
        funcion(est)
        guardar_estado(est)


def listar_glb():
    return [f for f in os.listdir(CARPETA_MODELOS) if f.lower().endswith(".glb")]


def obtener_modelo_activo():
    est = leer_estado()
    activo = est.get("modelo_activo", "")
    archivos = listar_glb()
    if activo in archivos:
        return activo
    return archivos[0] if archivos else ""


def listar_modelos_detallados():
    est = leer_estado()
    activo = obtener_modelo_activo()
    historial = est.get("historial", {})
    lista = []

    archivos = sorted(
        listar_glb(),
        key=lambda x: os.path.getmtime(os.path.join(CARPETA_MODELOS, x)),
        reverse=True
    )

    for nombre in archivos:
        ruta = os.path.join(CARPETA_MODELOS, nombre)
        peso_mb = round(os.path.getsize(ruta) / (1024 * 1024), 2)
        an = analizar_glb(ruta)
        info_hist = historial.get(nombre, {})
        lista.append({
            "nombre": nombre,
            "peso_mb": peso_mb,
            "piezas": an["draw_calls"],
            "mallas": an["mallas"],
            "triangulos": an["triangulos"],
            "instancias": an["instancias"],
            "texturas": an["texturas"],
            "nodos_antes": info_hist.get("nodos_antes", an["draw_calls"]),
            "optimizado": info_hist.get("optimizado", False),
            "activo": (nombre == activo),
            "fecha": time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(ruta)))
        })
    return lista


def nombre_modelo_seguro(nombre):
    """Solo permite .glb dentro de CARPETA_MODELOS (evita borrar _estado.json, etc.)."""
    n = os.path.basename(nombre or "")
    if not n or not n.lower().endswith(".glb"):
        return None
    return n


class ManejadorPortalVR(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "X-Filename, X-Mode, Content-Type")

    def enviar_json(self, datos, codigo=200):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def servir_estatico(self, ruta):
        rel = "index.html" if ruta in ("/", "") else ruta.lstrip("/")
        fisica = os.path.normpath(os.path.join(CARPETA_STATIC, rel))
        base = os.path.normpath(CARPETA_STATIC)
        if not (fisica == base or fisica.startswith(base + os.sep)) or not os.path.isfile(fisica):
            self.send_error(404)
            return
        tipo = mimetypes.guess_type(fisica)[0] or "application/octet-stream"
        if fisica.endswith(".js"):
            tipo = "application/javascript"
        with open(fisica, "rb") as f:
            cuerpo = f.read()
        self.send_response(200)
        self.send_header("Content-Type", tipo + ("; charset=utf-8" if tipo.startswith("text/") or tipo.endswith("javascript") else ""))
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(cuerpo)

    def servir_modelo(self, ruta):
        nombre = nombre_modelo_seguro(urllib.parse.unquote(ruta[len("/modelos/"):]))
        ruta_fisica = os.path.join(CARPETA_MODELOS, nombre) if nombre else None
        if not ruta_fisica or not os.path.isfile(ruta_fisica):
            self.send_error(404, "Modelo no encontrado")
            return

        total = os.path.getsize(ruta_fisica)
        inicio, fin = 0, total - 1
        codigo = 200
        rango = self.headers.get("Range")
        if rango and rango.startswith("bytes="):
            try:
                a, b = rango[6:].split(",")[0].split("-")
                if a == "":
                    inicio = max(total - int(b), 0)
                else:
                    inicio = int(a)
                    if b:
                        fin = min(int(b), total - 1)
                if inicio > fin or inicio >= total:
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{total}")
                    self.end_headers()
                    return
                codigo = 206
            except ValueError:
                inicio, fin, codigo = 0, total - 1, 200

        longitud = fin - inicio + 1
        self.send_response(codigo)
        self.send_header("Content-Type", "model/gltf-binary")
        self.send_header("Accept-Ranges", "bytes")
        self._cors()
        if codigo == 206:
            self.send_header("Content-Range", f"bytes {inicio}-{fin}/{total}")
        self.send_header("Content-Length", str(longitud))
        self.end_headers()
        try:
            with open(ruta_fisica, "rb") as f:
                f.seek(inicio)
                restante = longitud
                while restante > 0:
                    bloque = f.read(min(restante, 1024 * 1024))
                    if not bloque:
                        break
                    self.wfile.write(bloque)
                    restante -= len(bloque)
        except (ConnectionError, OSError):
            pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        ruta = parsed.path

        if ruta == "/api/estado" or ruta == "/lista":
            ip = obtener_ip_local()
            modelos_det = listar_modelos_detallados()
            almacenamiento = calcular_almacenamiento()
            self.enviar_json({
                "app": APP_NAME,
                "version": APP_VERSION,
                "empresa": COMPANY_NAME,
                "slogan": SLOGAN,
                "ip": ip,
                "pin": generar_codigo_pin(ip),
                "url": f"http://{ip}:{PUERTO_HTTP}",
                "pc": socket.gethostname(),
                "modelo_activo": obtener_modelo_activo(),
                "almacenamiento": almacenamiento,
                "modelos": [m["nombre"] for m in modelos_det] if ruta == "/lista" else modelos_det
            })
        elif ruta.startswith("/modelos/"):
            self.servir_modelo(ruta)
        else:
            self.servir_estatico(ruta)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        ruta = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if ruta == "/api/subir":
            longitud = int(self.headers.get("Content-Length", 0))
            if longitud <= 0 or longitud > TAMANO_MAX_SUBIDA:
                self.enviar_json({"ok": False, "error": "Tamano de archivo invalido"}, 400)
                return
            nombre_raw = urllib.parse.unquote_plus(self.headers.get("X-Filename", "modelo.glb"))
            modo = self.headers.get("X-Mode", "preservar")

            nombre_limpio = os.path.basename(nombre_raw)
            if not nombre_limpio.lower().endswith(".glb"):
                nombre_limpio += ".glb"

            ruta_destino = os.path.join(CARPETA_MODELOS, nombre_limpio)
            ruta_tmp = ruta_destino + ".part"
            try:
                with open(ruta_tmp, "wb") as f:
                    restante = longitud
                    while restante > 0:
                        bloque = self.rfile.read(min(restante, 1024 * 1024))
                        if not bloque:
                            break
                        f.write(bloque)
                        restante -= len(bloque)
                if restante > 0:
                    raise IOError("Subida incompleta")

                with open(ruta_tmp, "rb") as f:
                    if f.read(4) != b"glTF":
                        raise ValueError("El archivo no es un .glb valido")

                os.replace(ruta_tmp, ruta_destino)
            except Exception as e:
                if os.path.exists(ruta_tmp):
                    os.remove(ruta_tmp)
                self.enviar_json({"ok": False, "error": str(e)}, 400)
                return

            info_opt = procesar_modelo_glb(ruta_destino, modo)

            def aplicar(est):
                est["modelo_activo"] = nombre_limpio
                est["historial"][nombre_limpio] = info_opt
            modificar_estado(aplicar)

            print(f"[OK] Modelo registrado: {nombre_limpio} ({info_opt['peso_despues_mb']} MB | {info_opt['nodos_despues']} mallas)")
            self.enviar_json({"ok": True, "nombre": nombre_limpio, "info": info_opt})

        elif ruta == "/api/activar":
            nombre = nombre_modelo_seguro(urllib.parse.unquote_plus(params.get("nombre", [""])[0]))
            if not nombre or nombre not in listar_glb():
                self.enviar_json({"ok": False, "error": "Modelo no existe"}, 404)
                return
            modificar_estado(lambda est: est.__setitem__("modelo_activo", nombre))
            self.enviar_json({"ok": True})

        elif ruta == "/api/eliminar":
            nombre = nombre_modelo_seguro(urllib.parse.unquote_plus(params.get("nombre", [""])[0]))
            if not nombre:
                self.enviar_json({"ok": False, "error": "Nombre invalido"}, 400)
                return
            ruta_f = os.path.join(CARPETA_MODELOS, nombre)
            if os.path.isfile(ruta_f):
                os.remove(ruta_f)
            # Limpiar posibles copias o residuos (.originales, .bak, .part, .tmp)
            for carpeta in (CARPETA_ORIGINALES, CARPETA_MODELOS):
                for sufijo in ("", ".bak", ".part", ".tmp", ".opt.glb"):
                    r_extra = os.path.join(carpeta, nombre + sufijo) if sufijo else os.path.join(carpeta, nombre)
                    if os.path.isfile(r_extra):
                        try:
                            os.remove(r_extra)
                        except Exception:
                            pass

            def aplicar(est):
                est["historial"].pop(nombre, None)
                if est.get("modelo_activo") == nombre:
                    est["modelo_activo"] = ""
            modificar_estado(aplicar)
            self.enviar_json({"ok": True, "almacenamiento": calcular_almacenamiento()})

        elif ruta == "/api/limpiar_temporales":
            liberados_mb = limpiar_archivos_temporales()
            self.enviar_json({
                "ok": True,
                "liberados_mb": liberados_mb,
                "almacenamiento": calcular_almacenamiento()
            })

        elif ruta == "/api/vaciar_modelos":
            liberados_mb = vaciar_todos_los_modelos()
            self.enviar_json({
                "ok": True,
                "liberados_mb": liberados_mb,
                "almacenamiento": calcular_almacenamiento()
            })

        elif ruta == "/api/optimizar":
            nombre = nombre_modelo_seguro(urllib.parse.unquote_plus(params.get("nombre", [""])[0]))
            modo = params.get("modo", ["max_quest"])[0]
            if not nombre:
                self.enviar_json({"ok": False, "error": "Nombre invalido"}, 400)
                return
            ruta_f = os.path.join(CARPETA_MODELOS, nombre)
            if not os.path.isfile(ruta_f):
                self.enviar_json({"ok": False, "error": "Archivo no encontrado"}, 404)
                return
            info_opt = procesar_modelo_glb(ruta_f, modo)
            def aplicar(est):
                est["historial"][nombre] = info_opt
            modificar_estado(aplicar)
            self.enviar_json({"ok": True, "info": info_opt, "almacenamiento": calcular_almacenamiento()})

        elif ruta == "/api/abrir_carpeta":
            # Solo desde el propio PC: un visor en la red no debe abrir ventanas en este equipo.
            if self.client_address[0] not in ("127.0.0.1", "::1"):
                self.enviar_json({"ok": False, "error": "Solo disponible desde este equipo"}, 403)
                return
            if os.name == "nt":
                os.startfile(CARPETA_MODELOS)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", CARPETA_MODELOS])
            else:
                subprocess.Popen(["xdg-open", CARPETA_MODELOS])
            self.enviar_json({"ok": True, "ruta": CARPETA_MODELOS})
        else:
            self.send_error(404)


class ServidorPortal(ThreadingHTTPServer):
    # En Windows SO_REUSEADDR permite "robar" un puerto ya en uso; se desactiva alli.
    allow_reuse_address = os.name != "nt"
    daemon_threads = True


def crear_servidor():
    """Intenta el puerto 8000 y, si esta ocupado, los siguientes (el radar UDP anuncia el real)."""
    global PUERTO_HTTP
    ultimo_error = None
    for puerto in range(PUERTO_HTTP, PUERTO_HTTP + 10):
        try:
            servidor = ServidorPortal(("0.0.0.0", puerto), ManejadorPortalVR)
            PUERTO_HTTP = puerto
            return servidor
        except OSError as e:
            ultimo_error = e
    raise OSError(f"Puertos {PUERTO_HTTP}-{PUERTO_HTTP + 9} ocupados: {ultimo_error}")


def abrir_ventana_app(url):
    """
    Inicializa una ventana de escritorio nativa utilizando pywebview
    (aprovechando Microsoft Edge WebView2 en Windows o WebKit en macOS sin sobrecoste de memoria).
    Retorna True si la ventana se inicializo correctamente, o False si se debe recurrir al navegador del sistema.
    """
    try:
        import webview
    except ImportError:
        return False
    try:
        webview.create_window(APP_NAME, url, width=1340, height=880, min_size=(460, 600))
        webview.start()
        return True
    except Exception as e:
        print(f"[AVISO] No se pudo inicializar la interfaz nativa ({e}). Iniciando en navegador predeterminado.")
        return False


def main():
    try:
        servidor = crear_servidor()
    except OSError as e:
        print(f"[ERROR CRITICO] {e}")
        if not ES_EMPAQUETADO:
            input("Presione Enter para salir...")
        return

    ip_actual = obtener_ip_local()
    pin_actual = generar_codigo_pin(ip_actual)
    print("=" * 64)
    print(f" {APP_NAME} v{APP_VERSION} - {COMPANY_NAME}")
    print(f" {SLOGAN}")
    print(f" Autores: {AUTHORS}")
    print("=" * 64)
    print(f" Servidor Activo : http://{ip_actual}:{PUERTO_HTTP}")
    print(f" PIN de Enlace   : {pin_actual}")
    print(f" Almacenamiento  : {CARPETA_MODELOS}")
    print("=" * 64)

    iniciar_radar_udp()
    threading.Thread(target=servidor.serve_forever, daemon=True).start()

    url_local = f"http://127.0.0.1:{PUERTO_HTTP}"
    if "--navegador" not in sys.argv and abrir_ventana_app(url_local):
        servidor.shutdown()
        return

    webbrowser.open(url_local)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print(f"\n[{COMPANY_NAME}] Servidor detenido.")
        servidor.shutdown()


if __name__ == "__main__":
    main()