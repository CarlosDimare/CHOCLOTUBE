#!/usr/bin/env python3
# Choclotube Optimizado - Versión Mejorada
import os, re, threading, signal, sys, base64, subprocess, platform
import nest_asyncio; nest_asyncio.apply()
import yt_dlp
import webview
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from urllib.parse import urlparse, parse_qs

# Ocultar terminal al abrir la ventana (solo Windows)
if platform.system() == "Windows":
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# Verificar e instalar dependencias necesarias
def install_dependencies():
    required_packages = {
        'yt_dlp': 'yt-dlp',
        'webview': 'pywebview',
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'nest_asyncio': 'nest-asyncio'
    }
    
    for module, package in required_packages.items():
        try:
            __import__(module)
        except ImportError:
            print(f"Instalando {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Instalar dependencias antes de continuar
install_dependencies()

# Configuración inicial
os.makedirs("downloads", exist_ok=True)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")
app.mount("/static", StaticFiles(directory="."), name="static")  # Para servir archivos locales

# Convertir logo.jpg a base64 para el favicon
def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/jpeg;base64,{encoded_string}"
    except Exception as e:
        print(f"Error al procesar la imagen {image_path}: {e}")
        return ""

# Obtener la imagen del logo en base64
logo_image = get_image_base64("logo.jpg")

# Funciones auxiliares
def fmt(t): 
    m, s = divmod(int(t), 60)
    return f"{m:02d}:{s:02d}"

def sanitize(raw: str) -> str:
    raw = raw.strip()
    
    # Manejar URLs de YouTube Music
    if raw.startswith("https://music.youtube.com"):
        v = parse_qs(urlparse(raw).query).get("v")
        if not v: 
            raise ValueError("Sin 'v' en Music URL")
        return f"https://www.youtube.com/watch?v={v[0]}"
    
    # Patrones para diferentes formatos de URL de YouTube
    patterns = [
        r"(?:v=|/)([\w-]{11})(?:\?|&|/|$)", 
        r"youtu\.be/([\w-]{11})", 
        r"shorts/([\w-]{11})", 
        r"embed/([\w-]{11})",
        r"live/([\w-]{11})"
    ]
    
    for pat in patterns:
        if (m := re.search(pat, raw)):
            return f"https://www.youtube.com/watch?v={m.group(1)}"
    
    # Si no coincide con ningún patrón pero tiene 11 caracteres, asumir que es un ID
    if re.match(r'^[\w-]{11}$', raw):
        return f"https://www.youtube.com/watch?v={raw}"
    
    raise ValueError(f"ID de YouTube no detectado en: {raw}")

def ydl_get(url: str, opts: dict):
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)

HTML = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Choclotube</title>
    <link rel="icon" type="image/jpeg" href="{logo_image}">
    <style>
        :root {{
            --primary: #FFD700;         /* Amarillo maíz */
            --primary-light: #FFEA00;   /* Amarillo más claro */
            --primary-dark: #D4AF37;    /* Amarillo más oscuro para contraste */
            --secondary: #4CAF50;       /* Verde hojas de maíz */
            --secondary-light: #81C784; /* Verde más claro */
            --background: rgba(0, 0, 0, 0.85);      /* Fondo negro con transparencia */
            --surface: rgba(26, 26, 26, 0.8);         /* Gris muy oscuro con transparencia */
            --surface-alt: rgba(45, 45, 45, 0.8);     /* Gris oscuro con transparencia */
            --text: #e0e0e0;            /* Texto gris claro */
            --text-secondary: #aaaaaa;  /* Texto secundario */
            --text-on-yellow: #333333;  /* Texto sobre fondo amarillo */
            --text-on-green: #FFFFFF;   /* Texto sobre fondo verde */
            --error: #FFA000;           /* Amarillo oscuro para errores */
            --success: #4CAF50;         /* Verde para éxito */
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--background);
            color: var(--text);
            padding: 20px;
            margin: 0;
            display: flex;
            justify-content: center;
            min-height: 100vh;
            position: relative;
            padding-bottom: 80px; /* Espacio para el logo */
            user-select: text; /* Permitir selección de texto */
        }}
        
        /* Imagen de fondo con transparencia */
        body::before {{
            content: "";
            background-image: url("/static/fondo.jpg");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            opacity: 0.2; /* Ajusta la transparencia según sea necesario */
        }}
        
        .logo-container {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 10px;
            background: var(--surface);
            padding: 10px 15px;
            border-radius: 16px;
            box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
            transition: transform 0.3s ease;
        }}
        
        .logo-container:hover {{
            transform: translateY(-5px);
        }}
        
        .logo {{
            height: 50px;
            width: auto;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease;
        }}
        
        .logo:hover {{
            transform: scale(1.05);
        }}
        
        .logo-text {{
            font-size: 20px;
            font-weight: 700;
            color: var(--primary-light);
            text-shadow: 0 2px 5px rgba(255, 215, 0, 0.3);
        }}
        
        .container {{
            display: flex;
            gap: 25px;
            max-width: 1400px;
            width: 100%;
        }}
        
        .column {{
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        
        .panel {{
            background: var(--surface);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .panel:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
        }}
        
        .title {{
            color: var(--primary-light);
            font-weight: 600;
            font-size: 18px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--surface-alt);
        }}
        
        .playlist {{
            max-height: 400px;
            overflow-y: auto;
            border-radius: 12px;
            background: var(--surface-alt);
            padding: 0;
            margin: 0;
        }}
        
        .track {{
            padding: 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: var(--text);
            transition: background 0.2s ease;
        }}
        
        .track:hover {{
            background: rgba(255, 215, 0, 0.2);
        }}
        
        .track.playing {{
            background: var(--primary);
            font-weight: 600;
            color: var(--text-on-yellow);
        }}
        
        .track.next {{
            background: var(--secondary);
            font-weight: 600;
            color: var(--text-on-green);
        }}
        
        .track.loading {{
            background: var(--secondary-light);
            font-weight: 600;
            color: var(--text-on-green);
        }}
        
        .controls {{
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 20px;
        }}
        
        .controls button {{
            font-size: 20px;
            padding: 12px 20px;
            cursor: pointer;
            background: var(--surface-alt);
            border: none;
            border-radius: 50%;
            color: var(--text);
            width: 60px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        }}
        
        .controls button:hover {{
            background: var(--primary);
            color: var(--text-on-yellow);
            transform: scale(1.1);
        }}
        
        textarea {{
            width: 100%;
            height: 120px;
            resize: vertical;
            font-family: 'Courier', monospace, console;
            font-size: 14px;
            background: var(--surface-alt);
            color: var(--text);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 15px;
            box-sizing: border-box;
            transition: border 0.3s ease;
        }}
        
        textarea:focus {{
            outline: none;
            border: 1px solid var(--primary-light);
        }}
        
        .add-button {{
            font-size: 16px;
            padding: 15px;
            margin-top: 15px;
            cursor: pointer;
            background: var(--secondary);
            color: var(--text-on-yellow);
            border: none;
            border-radius: 12px;
            width: 100%;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
        }}
        
        .add-button:hover {{
            background: var(--primary-light);
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(255, 215, 0, 0.4);
        }}
        
        .search-box {{
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }}
        
        .search-box input {{
            flex: 1;
            padding: 12px 15px;
            font-size: 16px;
            background: var(--surface-alt);
            color: var(--text);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            transition: border 0.3s ease;
        }}
        
        .search-box input:focus {{
            outline: none;
            border: 1px solid var(--primary-light);
        }}
        
        .search-box button {{
            padding: 12px 20px;
            font-size: 16px;
            cursor: pointer;
            background: var(--secondary);
            color: var(--text-on-yellow);
            border: none;
            border-radius: 12px;
            font-weight: 500;
            transition: all 0.3s ease;
        }}
        
        .search-box button:hover {{
            background: var(--primary-light);
        }}
        
        .results {{
            max-height: 300px;
            overflow-y: auto;
            border-radius: 12px;
            background: var(--surface-alt);
        }}
        
        .result-item {{
            display: flex;
            align-items: center;
            padding: 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            gap: 15px;
            transition: background 0.2s ease;
        }}
        
        .result-item:hover {{
            background: rgba(255, 215, 0, 0.1);
        }}
        
        .result-item img {{
            width: 80px;
            height: 45px;
            object-fit: cover;
            border-radius: 8px;
            flex-shrink: 0;
        }}
        
        .result-info {{
            flex: 1;
            overflow: hidden;
        }}
        
        .result-title {{
            font-size: 15px;
            font-weight: 500;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-bottom: 5px;
            color: var(--text);
        }}
        
        .result-duration {{
            font-size: 13px;
            color: var(--text-secondary);
        }}
        
        .result-add {{
            background: var(--secondary);
            color: var(--text-on-green);
            border: none;
            border-radius: 8px;
            padding: 8px 12px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s ease;
        }}
        
        .result-add:hover {{
            background: var(--secondary-light);
            transform: scale(1.05);
        }}
        
        .current-info {{
            margin-top: 20px;
        }}
        
        #audioPlayer {{
            width: 100%;
            margin-top: 20px;
            border-radius: 12px;
            height: 40px;
        }}
        
        .progress-container {{
            width: 100%;
            height: 12px;
            background: var(--surface-alt);
            border-radius: 10px;
            margin: 20px 0;
            position: relative;
            cursor: pointer;
            overflow: hidden;
        }}
        
        .progress-bar {{
            height: 100%;
            background: var(--primary);
            border-radius: 10px;
            width: 0%;
            transition: width 0.3s ease;
        }}
        
        .time-info {{
            display: flex;
            justify-content: space-between;
            font-size: 16px;
            margin-bottom: 15px;
            font-weight: 400;
            color: var(--text);
        }}
        
        .delete-btn {{
            background: var(--error);
            color: var(--text-on-yellow);
            border: none;
            border-radius: 8px;
            padding: 5px 8px;
            cursor: pointer;
            font-size: 14px;
            margin-left: 10px;
            transition: all 0.3s ease;
        }}
        
        .delete-btn:hover {{
            background: var(--primary-dark);
            transform: scale(1.1);
        }}
        
        .loading {{
            text-align: center;
            padding: 30px;
            color: var(--text-secondary);
            font-size: 16px;
        }}
        
        .now-playing {{
            background: var(--surface-alt);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        
        .now-playing-title {{
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 15px;
            color: var(--primary-light);
        }}
        
        .now-playing-time {{
            font-size: 20px;
            font-weight: 700;
            color: var(--secondary);
            text-align: center;
            margin: 20px 0;
        }}
        
        .next-track {{
            background: var(--surface-alt);
            border-radius: 16px;
            padding: 20px;
        }}
        
        .next-track-title {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 10px;
            color: var(--primary-light);
        }}
        
        .next-track-info {{
            font-size: 18px;
            color: var(--text);
        }}
        
        .time-remaining {{
            font-size: 32px;
            font-weight: 700;
            color: var(--secondary);
            text-align: center;
            margin: 20px 0;
        }}
        
        /* Menú contextual */
        .context-menu {{
            display: none;
            position: fixed;
            background: var(--surface);
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            z-index: 1000;
            padding: 5px 0;
            min-width: 150px;
        }}
        
        .context-menu-item {{
            padding: 8px 20px;
            cursor: pointer;
            color: var(--text);
            transition: background 0.2s ease;
        }}
        
        .context-menu-item:hover {{
            background: var(--primary);
            color: var(--text-on-yellow);
        }}
        
        /* Responsive Design */
        @media (max-width: 1200px) {{
            .container {{
                flex-direction: column;
            }}
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}
            
            .logo-container {{
                bottom: 10px;
                left: 10px;
                padding: 8px 12px;
            }}
            
            .logo {{
                height: 40px;
            }}
            
            .logo-text {{
                font-size: 16px;
            }}
            
            .panel {{
                padding: 15px;
            }}
            
            .controls button {{
                width: 50px;
                height: 50px;
                font-size: 18px;
            }}
            
            .now-playing-title {{
                font-size: 20px;
            }}
            
            .now-playing-time {{
                font-size: 20px;
            }}
            
            .time-remaining {{
                font-size: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Columna Izquierda: Búsqueda y Agregador -->
        <div class="column">
            <div class="panel">
                <div class="title">Buscar en YT</div>
                <div class="search-box">
                    <input id="searchInput" placeholder="Buscar canciones..." onkeypress="if(event.key==='Enter') search()">
                    <button onclick="search()">Buscar</button>
                </div>
                <div id="searchResults" class="results" style="display:none"></div>
            </div>
            
            <div class="panel">
                <div class="title">Pegar Enlaces</div>
                <textarea id="url" placeholder="Podés pegar un choclo de enlaces..."></textarea>
                <button class="add-button" onclick="add()">Agregar</button>
            </div>
        </div>
        
        <!-- Columna Derecha: Lista y Reproductor -->
        <div class="column">
            <div class="panel">
                <div class="title">Lista de Reproducción</div>
                <ul id="sortable" class="playlist"></ul>
                <div class="time-info">
                    <span id="totaltime">Total: --:--</span>
                    <span id="lefttime">Restante: --:--</span>
                </div>
                <div class="controls">
                    <button onclick="prev()">⏮️</button>
                    <button onclick="togglePlay()">⏯️</button>
                    <button onclick="stop()">⏹️</button>
                    <button onclick="next()">⏭️</button>
                </div>
            </div>
            
            <div class="now-playing">
                <div class="title">Reproducción Actual</div>
                <div id="current" class="now-playing-title">Ninguna pista</div>
                <div id="timeRemaining" class="time-remaining">--:--</div>
                <div class="progress-container" id="progress-container">
                    <div class="progress-bar" id="progress-bar"></div>
                </div>
                <audio id="audioPlayer" controls></audio>
            </div>
            
            <div class="next-track">
                <div class="title">Pista Siguiente</div>
                <div id="nexttrack" class="next-track-info">Ninguna pista seleccionada</div>
            </div>
        </div>
    </div>

    <div class="logo-container">
        <img src="/static/logo.jpg" alt="Choclotube Logo" class="logo">
        <div class="logo-text">Choclotube</div>
    </div>
    
    <!-- Menú contextual para copiar/pegar -->
    <div id="contextMenu" class="context-menu">
        <div class="context-menu-item" id="copyOption">Copiar</div>
        <div class="context-menu-item" id="pasteOption">Pegar</div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
    <script>
        let playlist = [], current = -1, nextTrack = -1;
        let audio = document.getElementById("audioPlayer");
        let paused = false;
        
        // Sistema de estados del reproductor
        const PlayerState = {{
            IDLE: 'idle',
            LOADING: 'loading',
            PLAYING: 'playing',
            ERROR: 'error'
        }};
        
        let playerState = PlayerState.IDLE;
        
        // Formateo de tiempo
        function fmt(t) {{
            let m = Math.floor(t / 60), s = Math.floor(t % 60);
            return String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
        }}
        
        // Extraer IDs de YouTube (corregido)
        function extractYouTubeIDs(text) {{
            // Expresión regular mejorada para detectar todos los formatos de URL de YouTube
            const regex = /(?:youtube\\.com\\/watch\\?v=|youtu\\.be\\/|youtube\\.com\\/embed\\/|youtube\\.com\\/shorts\\/|youtube\\.com\\/live\\/)([a-zA-Z0-9_-]{{11}})/g;
            const ids = [];
            let match;
            
            while ((match = regex.exec(text)) !== null) {{
                // Evitar duplicados
                if (!ids.includes(match[1])) {{
                    ids.push(match[1]);
                }}
            }}
            
            return ids;
        }}
        
        // Función para agregar video por ID - MEJORADA
        function addVideoById(id) {{
            if (!playlist.some(t => t.id === id)) {{
                let idx = playlist.length;
                playlist.push({{
                    id, 
                    title: `Cargando... (${{id}})`, 
                    duration: 0, 
                    audio_url: ""
                }});
                render();
                
                // Usar el endpoint combinado como en c0.py
                fetch("/extract_audio", {{
                    method: "POST",
                    headers: {{"Content-Type": "application/json"}},
                    body: JSON.stringify({{url: `https://youtube.com/watch?v=${{id}}`}})
                }})
                .then(r => r.json())
                .then(d => {{
                    if (d.error) {{
                        playlist[idx].title = `Error: ${{id}}`;
                        console.error(`Error al procesar video ${{id}}:`, d.error);
                    }} else {{
                        playlist[idx].title = d.title;
                        playlist[idx].duration = d.duration;
                        playlist[idx].audio_url = d.audio_url;
                    }}
                    render();
                    updateTotalTime();
                    
                    // Actualizar siguiente pista si es necesario
                    if (nextTrack === -1 && playlist.length > 1) {{
                        if (current === playlist.length - 2) {{
                            nextTrack = playlist.length - 1;
                            document.getElementById("nexttrack").textContent = playlist[nextTrack].title;
                        }} else if (current === -1) {{
                            nextTrack = 0;
                            document.getElementById("nexttrack").textContent = playlist[nextTrack].title;
                        }}
                    }}
                }})
                .catch(error => {{
                    console.error(`Error de red al agregar video ${{id}}:`, error);
                    playlist[idx].title = `Error de red: ${{id}}`;
                    render();
                }});
            }}
        }}
        
        // Agregar enlaces
        function add() {{
            const input = document.getElementById("url");
            const text = input.value.trim();
            
            if (!text) {{
                alert("Por favor, ingresa al menos un enlace o ID de YouTube");
                return;
            }}
            
            // Si es un ID directo (11 caracteres), agregarlo directamente
            if (/^[a-zA-Z0-9_-]{{11}}$/.test(text)) {{
                addVideoById(text);
                input.value = "";
                return;
            }}
            
            // Extraer IDs de URLs completas
            const ids = extractYouTubeIDs(text);
            
            if (ids.length === 0) {{
                alert("No se detectaron enlaces válidos de YouTube. Por favor, verifica los enlaces.");
                return;
            }}
            
            // Mostrar mensaje de carga
            const originalText = input.value;
            input.value = `Agregando ${{ids.length}} video(s)...`;
            input.disabled = true;
            
            let addedCount = 0;
            
            // Procesar cada ID
            ids.forEach(id => {{
                if (!playlist.some(t => t.id === id)) {{
                    let idx = playlist.length;
                    playlist.push({{
                        id, 
                        title: `Cargando... (${{id}})`, 
                        duration: 0, 
                        audio_url: ""
                    }});
                    addedCount++;
                    render();
                    
                    // Usar el endpoint combinado como en c0.py
                    fetch("/extract_audio", {{
                        method: "POST",
                        headers: {{"Content-Type": "application/json"}},
                        body: JSON.stringify({{url: `https://youtube.com/watch?v=${{id}}`}})
                    }})
                    .then(r => r.json())
                    .then(d => {{
                        if (d.error) {{
                            playlist[idx].title = `Error: ${{id}}`;
                            console.error(`Error al procesar video ${{id}}:`, d.error);
                        }} else {{
                            playlist[idx].title = d.title;
                            playlist[idx].duration = d.duration;
                            playlist[idx].audio_url = d.audio_url;
                        }}
                        render();
                        updateTotalTime();
                        
                        // Actualizar siguiente pista si es necesario
                        if (nextTrack === -1 && playlist.length > 1) {{
                            if (current === playlist.length - 2) {{
                                nextTrack = playlist.length - 1;
                                document.getElementById("nexttrack").textContent = playlist[nextTrack].title;
                            }} else if (current === -1) {{
                                nextTrack = 0;
                                document.getElementById("nexttrack").textContent = playlist[nextTrack].title;
                            }}
                        }}
                        
                        // Si es el último video, restaurar el input
                        addedCount--;
                        if (addedCount === 0) {{
                            input.value = "";
                            input.disabled = false;
                            input.focus();
                        }}
                    }})
                    .catch(error => {{
                        console.error(`Error de red al agregar video ${{id}}:`, error);
                        playlist[idx].title = `Error de red: ${{id}}`;
                        render();
                        
                        // Si es el último video, restaurar el input
                        addedCount--;
                        if (addedCount === 0) {{
                            input.value = "";
                            input.disabled = false;
                            input.focus();
                        }}
                    }});
                }} else {{
                    // El video ya está en la lista
                    addedCount--;
                    if (addedCount === 0) {{
                        input.value = "";
                        input.disabled = false;
                        input.focus();
                    }}
                }}
            }});
            
            // Si no se agregó ningún video nuevo (todos ya existían)
            if (addedCount === 0) {{
                input.value = "";
                input.disabled = false;
                input.focus();
            }}
        }}
        
        // Búsqueda en YouTube optimizada
        document.getElementById("searchInput").addEventListener("keypress", function(e) {{
            if (e.key === "Enter") search();
        }});
        
        function search() {{
            let q = document.getElementById("searchInput").value.trim();
            if (!q) return;
            
            let results = document.getElementById("searchResults");
            results.style.display = "block";
            results.innerHTML = "<div class='loading'>Cargando...</div>";
            
            fetch("/search_yt", {{
                method: "POST",
                headers: {{"Content-Type": "application/json"}},
                body: JSON.stringify({{query: q}})
            }})
            .then(r => r.json())
            .then(d => {{
                console.log("Respuesta de búsqueda:", d); // Debug en consola
                results.innerHTML = "";
                
                if (d.error) {{
                    results.innerHTML = `<div style='padding:20px;color:var(--error)'>Error: ${{d.error}}</div>`;
                    return;
                }}
                
                if (!d || !Array.isArray(d) || d.length === 0) {{
                    results.innerHTML = "<div style='padding:20px;color:var(--text-secondary)'>No se encontraron resultados.</div>";
                    return;
                }}
                
                d.forEach(item => {{
                    let div = document.createElement("div");
                    div.className = "result-item";
                    div.innerHTML = `
                        <img src="${{item.thumbnail}}">
                        <div class="result-info">
                            <div class="result-title">${{item.title}}</div>
                            <div class="result-duration">${{item.duration_string || fmt(item.duration)}}</div>
                        </div>
                        <button class="result-add" onclick="addFromSearch('${{item.id}}')">Agregar</button>
                    `;
                    results.appendChild(div);
                }});
            }})
            .catch(error => {{
                console.error("Error en búsqueda:", error);
                results.innerHTML = `<div style='padding:20px;color:var(--error)'>Error de red: ${{error}}</div>`;
            }});
        }}
        
        function addFromSearch(id) {{
            // Agregar directamente por ID en lugar de construir URL
            addVideoById(id);
        }}
        
        // Renderizar lista
        function render() {{
            let ul = document.getElementById("sortable");
            ul.innerHTML = "";
            
            playlist.forEach((t, i) => {{
                let li = document.createElement("li");
                li.className = "track";
                
                // Asignar clases según el estado
                if (i === current && playerState === PlayerState.PLAYING) {{
                    li.classList.add("playing");
                }} else if (i === current && playerState === PlayerState.LOADING) {{
                    li.classList.add("loading");
                }} else if (i === nextTrack) {{
                    li.classList.add("next");
                }}
                
                li.innerHTML = `
                    <span>${{t.title}}</span>
                    <span>${{fmt(t.duration)}}
                        <button class="delete-btn" onclick="removeTrack(${{i}})">🗑️</button>
                    </span>
                `;
                
                // Un click: seleccionar como siguiente
                li.onclick = function(e) {{
                    if (e.detail === 1) {{ // Single click
                        setTimeout(() => {{
                            if (e.detail === 1) {{ // Still single click after delay
                                setNextTrack(i);
                            }}
                        }}, 200);
                    }}
                }};
                
                // Doble click: reproducir
                li.ondblclick = function(e) {{
                    e.stopPropagation(); // Prevent single click handler
                    playTrack(i);
                }};
                
                ul.appendChild(li);
            }});
            
            updateCurrentInfo();
        }}
        
        function setNextTrack(index) {{
            nextTrack = index;
            document.getElementById("nexttrack").textContent = playlist[nextTrack].title;
            render();
        }}
        
        // Función playTrack mejorada - SIMPLIFICADA COMO EN C0.PY
        function playTrack(index) {{
            // Si ya estamos reproduciendo esta pista, no hacer nada
            if (current === index && playerState === PlayerState.PLAYING) {{
                return;
            }}

            // Actualizar estado
            current = index;
            playerState = PlayerState.LOADING;
            render();
            
            let track = playlist[index];
            
            // Mostrar estado de carga
            document.getElementById("current").textContent = `Cargando audio... (${{track.title}})`;
            
            // Verificar si tenemos la URL del audio
            if (!track.audio_url) {{
                // Si no tenemos la URL, obtenerla primero
                fetch("/extract_audio", {{
                    method: "POST",
                    headers: {{"Content-Type": "application/json"}},
                    body: JSON.stringify({{url: `https://youtube.com/watch?v=${{track.id}}`}})
                }})
                .then(r => r.json())
                .then(d => {{
                    if (d.error) {{
                        playerState = PlayerState.ERROR;
                        document.getElementById("current").textContent = `Error: ${{track.title}}`;
                        console.error(`Error al obtener audio: ${{d.error}}`);
                        return;
                    }}
                    
                    // Actualizar la URL del audio en la playlist
                    track.audio_url = d.audio_url;
                    
                    // Ahora reproducir
                    playAudio(track);
                }})
                .catch(error => {{
                    playerState = PlayerState.ERROR;
                    document.getElementById("current").textContent = `Error de red: ${{track.title}}`;
                    console.error(`Error al obtener audio: ${{error}}`);
                }});
            }} else {{
                // Si ya tenemos la URL, reproducir directamente
                playAudio(track);
            }}
        }}
        
        // Función para reproducir audio - SIMPLIFICADA COMO EN C0.PY
        function playAudio(track) {{
            // Limpiar completamente el reproductor
            audio.pause();
            audio.removeAttribute('src');
            audio.load();
            
            // Configurar event listeners
            const onCanPlay = () => {{
                audio.play()
                    .then(() => {{
                        playerState = PlayerState.PLAYING;
                        paused = false;
                        document.getElementById("current").textContent = track.title;
                        updateCurrentInfo();
                    }})
                    .catch(error => {{
                        playerState = PlayerState.ERROR;
                        console.error("Error al reproducir audio:", error);
                        document.getElementById("current").textContent = `Error al reproducir: ${{track.title}}`;
                    }})
                    .finally(() => {{
                        // Limpiar event listeners
                        audio.removeEventListener('canplay', onCanPlay);
                        audio.removeEventListener('error', onError);
                        clearTimeout(timeout);
                    }});
            }};
            
            const onError = () => {{
                playerState = PlayerState.ERROR;
                console.error("Error al cargar audio");
                document.getElementById("current").textContent = `Error al cargar: ${{track.title}}`;
                clearTimeout(timeout);
            }};
            
            // Timeout para evitar que la promesa quede pendiente para siempre
            const timeout = setTimeout(() => {{
                playerState = PlayerState.ERROR;
                console.error("Timeout al cargar audio");
                document.getElementById("current").textContent = `Timeout: ${{track.title}}`;
                audio.removeEventListener('canplay', onCanPlay);
                audio.removeEventListener('error', onError);
            }}, 10000); // 10 segundos
            
            audio.addEventListener('canplay', onCanPlay);
            audio.addEventListener('error', onError);
            
            // Cargar la nueva fuente
            audio.src = track.audio_url;
            audio.load();
        }}
        
        function removeTrack(i) {{
            playlist.splice(i, 1);
            if (current === i) stop();
            if (current > i) current--;
            if (nextTrack === i) nextTrack = -1;
            if (nextTrack > i) nextTrack--;
            render();
            updateTotalTime();
        }}
        
        function updateTotalTime() {{
            let sum = playlist.reduce((a, b) => a + b.duration, 0);
            document.getElementById("totaltime").textContent = "Total: " + fmt(sum);
        }}
        
        function togglePlay() {{
            if (playerState !== PlayerState.PLAYING) {{
                return;
            }}
            
            if (paused) {{
                audio.play()
                    .then(() => {{
                        paused = false;
                    }})
                    .catch(error => {{
                        console.error("Error al reanudar reproducción:", error);
                        alert(`Error al reanudar reproducción: ${{error}}`);
                    }});
            }} else {{
                audio.pause();
                paused = true;
            }}
        }}
        
        function stop() {{
            if (playerState === PlayerState.IDLE) return;
            
            audio.pause();
            audio.currentTime = 0;
            playerState = PlayerState.IDLE;
            current = -1;
            paused = true;
            updateCurrentInfo();
            render();
        }}
        
        function next() {{
            if (current + 1 < playlist.length) {{
                playTrack(current + 1);
            }} else if (nextTrack >= 0) {{
                playTrack(nextTrack);
            }}
        }}
        
        function prev() {{
            if (current - 1 >= 0) {{
                playTrack(current - 1);
            }}
        }}
        
        function updateCurrentInfo() {{
            if (current >= 0) {{
                document.getElementById("current").textContent = playlist[current].title;
            }} else {{
                document.getElementById("current").textContent = "Ninguna pista";
                document.getElementById("timeRemaining").textContent = "--:--";
            }}
        }}
        
        function updateNextTrack() {{
            if (current + 1 < playlist.length) {{
                nextTrack = current + 1;
                document.getElementById("nexttrack").textContent = playlist[nextTrack].title;
            }} else {{
                nextTrack = -1;
                document.getElementById("nexttrack").textContent = "Ninguna pista seleccionada";
            }}
            render();
        }}
        
        // Actualizar tiempo restante
        audio.ontimeupdate = function() {{
            if (!audio.duration) return;
            
            // Actualizar tiempo restante grande
            const remaining = Math.max(0, audio.duration - audio.currentTime);
            document.getElementById("timeRemaining").textContent = fmt(remaining);
            
            // Actualizar tiempo restante pequeño
            document.getElementById("lefttime").textContent = "Restante: " + fmt(remaining);
            
            // Actualizar barra de progreso
            const progress = (audio.currentTime / audio.duration) * 100;
            document.getElementById("progress-bar").style.width = progress + "%";
        }};
        
        // Manejar el final de la reproducción para pasar a la siguiente pista
        audio.onended = function() {{
            if (playerState === PlayerState.PLAYING) {{
                next();
            }}
        }};
        
        // Hacer lista ordenable
        new Sortable(document.getElementById("sortable"), {{
            animation: 150,
            onEnd: function(evt) {{
                const moved = playlist.splice(evt.oldIndex, 1)[0];
                playlist.splice(evt.newIndex, 0, moved);
                
                if (evt.oldIndex === current) current = -1;
                else if (evt.oldIndex < current) current--;
                
                if (evt.oldIndex === nextTrack) nextTrack = -1;
                else if (evt.oldIndex < nextTrack) nextTrack--;
                
                render();
            }}
        }});
        
        // Funcionalidad del menú contextual (clic derecho)
        const contextMenu = document.getElementById('contextMenu');
        let selectedText = '';
        
        // Evento para mostrar el menú contextual
        document.addEventListener('contextmenu', function(e) {{
            e.preventDefault();
            
            // Obtener el texto seleccionado
            selectedText = window.getSelection().toString();
            
            // Mostrar el menú en la posición del ratón
            contextMenu.style.display = 'block';
            contextMenu.style.left = e.pageX + 'px';
            contextMenu.style.top = e.pageY + 'px';
            
            // Deshabilitar la opción de copiar si no hay texto seleccionado
            document.getElementById('copyOption').style.opacity = selectedText ? '1' : '0.5';
            document.getElementById('copyOption').style.pointerEvents = selectedText ? 'auto' : 'none';
        }});
        
        // Ocultar el menú al hacer clic en cualquier parte
        document.addEventListener('click', function() {{
            contextMenu.style.display = 'none';
        }});
        
        // Función para copiar
        document.getElementById('copyOption').addEventListener('click', function() {{
            if (selectedText) {{
                navigator.clipboard.writeText(selectedText).then(function() {{
                    console.log('Texto copiado');
                }}).catch(function(err) {{
                    console.error('Error al copiar: ', err);
                }});
            }}
        }});
        
        // Función para pegar
        document.getElementById('pasteOption').addEventListener('click', function() {{
            navigator.clipboard.readText().then(function(text) {{
                // Intentar pegar en el elemento activo (input o textarea)
                let activeElement = document.activeElement;
                if (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA') {{
                    let start = activeElement.selectionStart;
                    let end = activeElement.selectionEnd;
                    activeElement.value = activeElement.value.substring(0, start) + text + activeElement.value.substring(end);
                    activeElement.selectionStart = activeElement.selectionEnd = start + text.length;
                }}
            }}).catch(function(err) {{
                console.error('Error al pegar: ', err);
            }});
        }});
    </script>
</body>
</html>
"""

# Endpoints de la API
@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(HTML)

@app.post("/extract_audio")
async def extract_audio(request: Request):
    try:
        data = await request.json()
        url = data.get("url")
        print(f"URL recibida en extract_audio: {url}")  # Debug
        
        # Si ya es una URL de YouTube válida, usarla directamente
        if url.startswith(("https://www.youtube.com/watch?v=", "https://youtube.com/watch?v=", 
                          "https://youtu.be/", "https://www.youtube.com/embed/", 
                          "https://www.youtube.com/shorts/", "https://www.youtube.com/live/")):
            sanitized_url = sanitize(url)
        else:
            # Si no es una URL reconocida, intentar procesarla como un ID directo
            if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
                sanitized_url = f"https://www.youtube.com/watch?v={url}"
            else:
                raise ValueError(f"URL no válida: {url}")
        
        print(f"URL sanitizada: {sanitized_url}")  # Debug
        
        # Opciones optimizadas para velocidad (como en c0.py)
        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "skip_download": True,
            "outtmpl": "-",
            "postprocessors": [],
            "noprogress": True,
            "nocheckcertificate": True,
            "cachedir": False,
            "socket_timeout": 10,
            "retries": 1,
            "fragment_retries": 1
        }
        
        info = ydl_get(sanitized_url, ydl_opts)
        
        return JSONResponse({
            "title": info.get("title", "Sin título"),
            "duration": int(info.get("duration", 0)),
            "audio_url": info["url"]
        })
    except Exception as e:
        print(f"Error en extract_audio: {e}")  # Debug
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/search_yt")
async def search_yt(request: Request):
    try:
        data = await request.json()
        query = data.get("query")
        print(f"Buscando: {query}")  # Debug
        
        # Configuración optimizada para búsqueda rápida con duración
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "extract_flat": "in_playlist",  # Método intermedio que incluye duración
            "skip_download": True,
            "playlistend": 5,
            "cachedir": False,
            "socket_timeout": 10,
            "retries": 1,
            "fragment_retries": 1,
            "noprogress": True,
            "nocheckcertificate": True
        }
        
        # Realizar la búsqueda con el prefijo correcto
        search_query = f"ytsearch5:{query}"
        print(f"Consulta de búsqueda: {search_query}")  # Debug
        info = ydl_get(search_query, ydl_opts)
        print(f"Resultados obtenidos: {len(info.get('entries', []))}")  # Debug
        
        results = []
        for entry in info.get("entries", []):
            # Con extract_flat='in_playlist', tenemos acceso a la duración
            duration = entry.get("duration", 0)
            duration_string = fmt(int(duration)) if duration else "--:--"
            
            # Generar thumbnail automáticamente
            thumbnail = f"https://i.ytimg.com/vi/{entry['id']}/default.jpg"
            
            results.append({
                "id": entry["id"],
                "title": entry.get("title", "Sin título"),
                "duration": duration,
                "duration_string": duration_string,
                "thumbnail": thumbnail
            })
        
        print(f"Resultados procesados: {len(results)}")  # Debug
        return JSONResponse(results)
    except Exception as e:
        print(f"Error en search_yt: {e}")  # Debug
        return JSONResponse({"error": str(e)}, status_code=500)

# Función para ejecutar el servidor
def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

# Función para ejecutar la interfaz gráfica
def run_gui():
    webview.create_window(
        "Choclotube",
        "http://127.0.0.1:8000",
        width=1400,
        height=800,
        resizable=True,
        min_size=(800, 500)
    )
    webview.start()

# Punto de entrada principal
if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    threading.Thread(target=run_server, daemon=True).start()
    run_gui()