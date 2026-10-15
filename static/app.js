(() => {
    // Por encima de este peso se pide confirmacion antes de cargar en WebGL.
    const UMBRAL_PESADO_MB = 40;
    const UMBRAL_TRIS_PESADO = 1500000;

    const $ = id => document.getElementById(id);
    const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    const fmt = n => Number(n).toLocaleString('es');

    let modelos = [];
    let modeloEnVisor = null; // nombre del modelo montado en el visor, o null
    const optimizando = new Set(); // modelos con optimizacion en curso (sobrevive al refresco)
    let firmaEstado = '';          // evita re-renderizar la tabla si nada cambio
    const ES_LOCAL = ['localhost', '127.0.0.1', '[::1]', '::1'].includes(location.hostname);
    const NOMBRES_MODO = {
        lujo: 'Recorrido de Lujo', equilibrado: 'Equilibrado (-15%)',
        ultra: 'Ultra Ligero (-50%)', preservar: 'Restaurar original'
    };

    // ---------- VISOR 3D (montaje bajo demanda para liberar GPU) ----------
    function cerrarVisor() {
        const host = $('viewer-host');
        const mv = host.querySelector('model-viewer');
        if (mv) {
            mv.removeAttribute('src');
            mv.remove(); // al destruir el elemento se libera el contexto WebGL y la VRAM
        }
        const barra = host.querySelector('.viewer-loading');
        if (barra) barra.remove();
        $('viewer-idle').style.display = 'flex';
        $('preview-name').textContent = 'Vista 3D apagada';
        $('preview-meta').textContent = '';
        $('btn-cerrar-visor').style.display = 'none';
        modeloEnVisor = null;
        renderTabla();
    }

    function abrirVisor(m) {
        const esPesado = m.peso_mb >= UMBRAL_PESADO_MB || m.triangulos >= UMBRAL_TRIS_PESADO;
        if (esPesado) {
            const ok = confirm(
                `Este modelo pesa ${m.peso_mb} MB y tiene ~${fmt(m.triangulos)} triangulos.\n` +
                `Puede ralentizar el navegador y saturar la GPU.\n\n¿Cargar la vista previa de todos modos?`
            );
            if (!ok) return;
        }
        cerrarVisorSilencioso();

        const host = $('viewer-host');
        $('viewer-idle').style.display = 'none';

        const mv = document.createElement('model-viewer');
        mv.setAttribute('camera-controls', '');
        mv.setAttribute('shadow-intensity', '0.8');
        mv.setAttribute('exposure', '0.95');
        mv.setAttribute('loading', 'eager');
        mv.setAttribute('src', `/modelos/${encodeURIComponent(m.nombre)}?t=${Date.now()}`);
        host.appendChild(mv);

        const barra = document.createElement('div');
        barra.className = 'viewer-loading';
        barra.innerHTML = '<div></div>';
        host.appendChild(barra);
        mv.addEventListener('progress', e => { barra.firstChild.style.width = Math.round(e.detail.totalProgress * 100) + '%'; });
        mv.addEventListener('load', () => barra.remove());
        mv.addEventListener('error', () => {
            barra.remove();
            $('preview-meta').textContent = 'Error al cargar el modelo';
        });

        modeloEnVisor = m.nombre;
        $('preview-name').textContent = m.nombre;
        $('preview-meta').textContent = `${m.peso_mb} MB | ${fmt(m.triangulos)} tris | ${m.piezas} mallas`;
        $('btn-cerrar-visor').style.display = 'inline-flex';
        renderTabla();
    }

    function cerrarVisorSilencioso() {
        const mv = $('viewer-host').querySelector('model-viewer');
        if (mv) { mv.removeAttribute('src'); mv.remove(); }
        const barra = $('viewer-host').querySelector('.viewer-loading');
        if (barra) barra.remove();
    }

    function alternarVisor(nombre) {
        if (modeloEnVisor === nombre) { cerrarVisor(); return; }
        const m = modelos.find(x => x.nombre === nombre);
        if (m) abrirVisor(m);
    }

    // ---------- ESTADO Y TABLA ----------
    async function cargarEstado() {
        try {
            const res = await fetch('/api/estado');
            const data = await res.json();
            $('pin-display').textContent = data.pin;
            $('ip-display').textContent = `${data.url} (${data.pc})`;

            if (data.almacenamiento) {
                const alm = data.almacenamiento;
                $('storage-badge').textContent = `${alm.total_mb} MB en disco`;
                const btnLimpiar = $('btn-limpiar-temporales');
                if (alm.temporales_mb > 0) {
                    btnLimpiar.style.display = 'inline-flex';
                    $('btn-limpiar-label').textContent = `Liberar copias (${alm.temporales_mb} MB)`;
                    btnLimpiar.title = `Eliminar ${alm.temporales_mb} MB en copias de respaldo (.originales, .bak) que ya no son necesarias`;
                } else {
                    btnLimpiar.style.display = 'none';
                }
                $('btn-vaciar-todo').style.display = (data.modelos.length > 0 || alm.total_mb > 0.5) ? 'inline-flex' : 'none';
            }

            const firma = JSON.stringify({ modelos: data.modelos, alm: data.almacenamiento });
            if (firma === firmaEstado) return; // nada cambio: no tocar el DOM
            firmaEstado = firma;
            modelos = data.modelos;
            if (modeloEnVisor && !modelos.some(m => m.nombre === modeloEnVisor)) cerrarVisor();
            renderTabla();
        } catch (e) {
            $('ip-display').textContent = 'Sin conexion con el servidor';
        }
    }

    function renderTabla() {
        $('count-badge').textContent = `${modelos.length} archivo(s)`;
        const wrapper = $('table-wrapper');
        if (modelos.length === 0) {
            wrapper.innerHTML = '<div class="empty-state">No hay archivos .glb todavia. Sube uno arriba o copialo con "Abrir carpeta".</div>';
            return;
        }
        const modoSel = $('sel-modo').value;
        const tipOptimizar = esc(`Optimiza este modelo usando "${NOMBRES_MODO[modoSel] || modoSel}". Reduce draw calls para Meta Quest sin guardar copias duplicadas.`);
        const filas = modelos.map(m => {
            const viendo = m.nombre === modeloEnVisor;
            const ocupado = optimizando.has(m.nombre);
            const pesado = m.peso_mb >= UMBRAL_PESADO_MB || m.triangulos >= UMBRAL_TRIS_PESADO;
            const n = esc(m.nombre);
            return `
            <tr class="${m.activo ? 'active-row' : ''} ${viendo ? 'viewing-row' : ''}">
                <td class="cell-name">
                    <span style="font-weight:500;">${n}</span>
                    ${m.activo ? '<span class="badge" title="Este es el modelo que cargara el Meta Quest al conectarse">Activo</span>' : ''}
                    ${viendo ? '<span class="badge view">En visor</span>' : ''}
                </td>
                <td class="mono-cell ${pesado ? 'heavy' : ''}" data-label="Tamano" ${pesado ? 'title="Modelo pesado: conviene optimizarlo para el Quest"' : ''}>${m.peso_mb} MB${pesado ? ' !' : ''}</td>
                <td class="mono-cell" data-label="Tris" title="Triangulos totales">${fmt(m.triangulos)}</td>
                <td class="mono-cell" data-label="Mallas" title="Draw calls: menos es mas fluido en VR">${m.piezas}</td>
                <td class="mono-cell col-fecha" data-label="Modificado">${esc(m.fecha)}</td>
                <td class="cell-actions">
                    <div class="actions-cell">
                        <button class="btn" data-accion="ver" data-nombre="${n}" title="${viendo ? 'Cierra la vista 3D y libera la GPU' : 'Muestra el modelo en 3D en el panel de inspeccion'}">${viendo ? 'Ocultar' : 'Inspeccionar'}</button>
                        <button class="btn btn-dark" data-accion="optimizar" data-nombre="${n}" title="${tipOptimizar}" ${ocupado ? 'disabled' : ''}>${ocupado ? 'Optimizando...' : 'Optimizar VR'}</button>
                        ${!m.activo ? `<button class="btn" data-accion="activar" data-nombre="${n}" title="Marca este modelo como el que cargara el Meta Quest">Activar</button>` : ''}
                        <button class="btn btn-ghost-danger" data-accion="eliminar" data-nombre="${n}" title="Borra el archivo del disco de forma definitiva">Eliminar</button>
                    </div>
                </td>
            </tr>`;
        }).join('');

        wrapper.innerHTML = `
            <table class="table-container">
                <thead><tr>
                    <th>Archivo</th><th>Tamano</th><th>Tris</th><th>Mallas</th><th class="col-fecha">Modificado</th>
                    <th style="text-align:right;">Acciones</th>
                </tr></thead>
                <tbody>${filas}</tbody>
            </table>`;
    }

    // Delegacion de eventos: evita inyectar nombres de archivo en atributos onclick.
    $('table-wrapper').addEventListener('click', async e => {
        const btn = e.target.closest('button[data-accion]');
        if (!btn) return;
        const nombre = btn.dataset.nombre;
        const accion = btn.dataset.accion;
        if (accion === 'ver') alternarVisor(nombre);
        else if (accion === 'activar') {
            await fetch('/api/activar?nombre=' + encodeURIComponent(nombre), { method: 'POST' });
            cargarEstado();
        } else if (accion === 'optimizar') {
            if (optimizando.has(nombre)) return;
            optimizando.add(nombre);
            renderTabla();
            const modoSel = $('sel-modo') ? $('sel-modo').value : 'lujo';
            try {
                const res = await fetch('/api/optimizar?nombre=' + encodeURIComponent(nombre) + '&modo=' + encodeURIComponent(modoSel), { method: 'POST' });
                if (!res.ok) {
                    mostrarMsg(`Error del servidor (${res.status}): por favor reinicia portal_arquitecto.py para aplicar la actualización`, 'error');
                } else {
                    const dat = await res.json();
                    if (dat.ok) {
                        const msg = (dat.info && dat.info.mensaje) ? dat.info.mensaje : 'Optimizado con éxito';
                        mostrarMsg(`¡${nombre}: ${msg}!`, 'ok');
                    } else {
                        mostrarMsg(`Error al optimizar: ${dat.error || 'desconocido'}`, 'error');
                    }
                }
            } catch (err) {
                mostrarMsg('Error de conexión con el servidor: ' + err.message, 'error');
            }
            optimizando.delete(nombre);
            firmaEstado = ''; // forzar re-render aunque el servidor devuelva lo mismo
            cargarEstado();
        } else if (accion === 'eliminar') {
            if (!confirm(`Confirmar eliminacion de ${nombre}?`)) return;
            if (modeloEnVisor === nombre) cerrarVisor();
            await fetch('/api/eliminar?nombre=' + encodeURIComponent(nombre), { method: 'POST' });
            cargarEstado();
        }
    });

    // ---------- SUBIDA ----------
    function mostrarMsg(texto, tipo) {
        const el = $('upload-msg');
        el.className = 'msg ' + tipo;
        el.textContent = texto;
    }

    function subirArchivo(archivo) {
        if (!archivo || !archivo.name.toLowerCase().endsWith('.glb')) {
            mostrarMsg('Selecciona un archivo con extension .glb', 'error');
            return;
        }
        $('upload-msg').className = 'msg';
        const wrap = $('progress-wrap');
        const fill = $('progress-fill');
        const pct = $('progress-percent');
        const texto = $('progress-text');
        const modo = $('sel-modo').value;

        wrap.style.display = 'block';
        fill.style.width = '0%';
        pct.textContent = '0%';
        texto.textContent = 'Subiendo archivo...';

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/subir', true);
        xhr.setRequestHeader('X-Filename', encodeURIComponent(archivo.name));
        xhr.setRequestHeader('X-Mode', modo);

        xhr.upload.onprogress = e => {
            if (e.lengthComputable) {
                const p = Math.round((e.loaded / e.total) * 100);
                fill.style.width = p + '%';
                pct.textContent = p + '%';
                if (p >= 100) texto.textContent = 'Procesando en el servidor...';
            }
        };
        const terminar = () => setTimeout(() => { wrap.style.display = 'none'; }, 400);
        xhr.onload = () => {
            terminar();
            let resp = {};
            try { resp = JSON.parse(xhr.responseText); } catch (_) { }
            if (xhr.status === 200 && resp.ok) {
                mostrarMsg(`Modelo "${resp.nombre}" publicado (${resp.info.peso_despues_mb} MB).`, 'ok');
                cargarEstado();
            } else {
                mostrarMsg('Error al subir: ' + (resp.error || `HTTP ${xhr.status}`), 'error');
            }
        };
        xhr.onerror = () => { terminar(); mostrarMsg('Error de red durante la subida.', 'error'); };
        xhr.onabort = () => { terminar(); mostrarMsg('Subida cancelada.', 'error'); };
        xhr.send(archivo);
        // NO se carga el modelo en el visor automaticamente: se hace con "Inspeccionar".
    }

    // ---------- EVENTOS ----------
    const dropZone = $('drop-zone');
    dropZone.addEventListener('click', () => $('file-input').click());
    $('file-input').addEventListener('change', e => { subirArchivo(e.target.files[0]); e.target.value = ''; });
    ['dragenter', 'dragover'].forEach(ev => dropZone.addEventListener(ev, e => { e.preventDefault(); dropZone.classList.add('dragover'); }));
    ['dragleave', 'drop'].forEach(ev => dropZone.addEventListener(ev, e => { e.preventDefault(); dropZone.classList.remove('dragover'); }));
    dropZone.addEventListener('drop', e => { if (e.dataTransfer.files.length > 0) subirArchivo(e.dataTransfer.files[0]); });

    $('btn-actualizar').addEventListener('click', () => { firmaEstado = ''; cargarEstado(); });
    // Abrir carpeta abre el explorador del PC servidor: solo tiene sentido desde ese mismo PC.
    if (!ES_LOCAL) $('btn-carpeta').style.display = 'none';
    $('btn-carpeta').addEventListener('click', async () => {
        try {
            const r = await (await fetch('/api/abrir_carpeta', { method: 'POST' })).json();
            if (!r.ok) mostrarMsg(r.error || 'No se pudo abrir la carpeta', 'error');
        } catch (_) { mostrarMsg('No se pudo abrir la carpeta', 'error'); }
    });
    $('btn-limpiar-temporales').addEventListener('click', async () => {
        try {
            const res = await (await fetch('/api/limpiar_temporales', { method: 'POST' })).json();
            if (res.ok) {
                mostrarMsg(`¡Se liberaron ${res.liberados_mb} MB eliminando copias de respaldo viejas!`, 'ok');
                firmaEstado = '';
                cargarEstado();
            }
        } catch (e) {
            mostrarMsg('Error al limpiar copias temporales: ' + e.message, 'error');
        }
    });

    $('btn-vaciar-todo').addEventListener('click', async () => {
        if (!confirm('¿Deseas eliminar TODOS los modelos alojados en el servidor para liberar todo el espacio en disco?')) return;
        cerrarVisor();
        try {
            const res = await (await fetch('/api/vaciar_modelos', { method: 'POST' })).json();
            if (res.ok) {
                mostrarMsg(`Directorio limpio. Se liberaron ${res.liberados_mb} MB.`, 'ok');
                firmaEstado = '';
                cargarEstado();
            }
        } catch (e) {
            mostrarMsg('Error al vaciar modelos: ' + e.message, 'error');
        }
    });

    $('btn-cerrar-visor').addEventListener('click', cerrarVisor);
    $('sel-modo').addEventListener('change', renderTabla); // actualiza el tooltip de "Optimizar VR"

    // Refresco automatico (detecta .glb copiados a mano). Pausado si la ventana esta oculta.
    setInterval(() => { if (!document.hidden) cargarEstado(); }, 8000);
    document.addEventListener('visibilitychange', () => { if (!document.hidden) cargarEstado(); });

    cargarEstado();
})();
