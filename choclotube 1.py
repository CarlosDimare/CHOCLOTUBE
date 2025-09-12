
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import nest_asyncio
import yt_dlp
import os
import re
from datetime import datetime
try:
    import ffmpeg
except ImportError:
    ffmpeg = None

app = FastAPI()
nest_asyncio.apply()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos descargados
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")

# Reproductor YouTube con diseño de 2 columnas
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>Choclotube</title>
  <style>
    body { 
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
      background: #212121; 
      color: #e0e0e0; 
      padding: 20px; 
      font-size: 14px; 
      margin: 0;
    }
    .container { 
      display: flex; 
      gap: 20px; 
      max-width: 1400px; 
      margin: 0 auto; 
    }
    .left-column, .center-column, .right-column { 
      flex: 1; 
      min-width: 300px;
    }
    .panel { 
      background: #2f2f2f; 
      border: 1px solid #404040; 
      border-radius: 8px; 
      padding: 20px; 
      margin-bottom: 20px; 
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    .title { 
      background: #1a1a1a; 
      color: #f0f0f0; 
      padding: 12px 16px; 
      margin: -20px -20px 16px -20px; 
      font-weight: 600; 
      font-size: 16px;
      border-radius: 8px 8px 0 0;
      border-bottom: 1px solid #404040;
    }
    .playlist { 
      max-height: 500px; 
      overflow-y: auto; 
      border: 1px solid #404040; 
      border-radius: 6px;
      padding: 0; 
      background: #1a1a1a; 
      margin: 0;
    }
    .playlist::-webkit-scrollbar {
      width: 8px;
    }
    .playlist::-webkit-scrollbar-track {
      background: #2f2f2f;
    }
    .playlist::-webkit-scrollbar-thumb {
      background: #555;
      border-radius: 4px;
    }
    .track {
      padding: 12px 16px; 
      border-bottom: 1px solid #333; 
      cursor: pointer; 
      user-select: none; 
      display: flex; 
      align-items: center; 
      justify-content: space-between; 
      color: #e0e0e0;
      transition: background-color 0.2s;
    }
    .track:hover {
      background: #333;
    }
    .track.playing { 
      background: #0066cc; 
      font-weight: 600; 
      color: white; 
    }
    .track.next { 
      background: #006600; 
      font-weight: 600; 
      color: white; 
    }
    .track.queued { 
      background: #2a2a2a; 
      color: #e0e0e0; 
    }
    .controls { 
      display: flex; 
      justify-content: center; 
      gap: 12px; 
      margin-top: 16px; 
    }
    .controls button {
      font-size: 18px; 
      padding: 12px 16px; 
      cursor: pointer;
      background: #404040; 
      border: 1px solid #555; 
      border-radius: 8px;
      color: #e0e0e0;
      min-width: 50px; 
      height: 48px;
      transition: all 0.2s;
    }
    .controls button:hover { 
      background: #555; 
      border-color: #666;
    }
    .track-title {
      flex-grow: 1;
      margin-right: 12px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    textarea { 
      width: 100%; 
      height: 200px; 
      resize: vertical; 
      font-family: 'Courier New', monospace; 
      font-size: 13px; 
      background: #1a1a1a;
      color: #e0e0e0;
      border: 1px solid #404040;
      border-radius: 6px;
      padding: 12px;
      box-sizing: border-box;
    }
    textarea::placeholder {
      color: #888;
    }
    .info { 
      margin-top: 12px; 
      padding: 12px;
      background: #1a1a1a;
      border-radius: 6px;
      border: 1px solid #404040;
    }
    .info input[type="range"] {
      background: #404040;
      margin: 0 8px;
    }
    .info label {
      margin-left: 16px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .total-time { 
      font-weight: 600; 
      padding: 12px; 
      background: #1a1a1a; 
      text-align: right; 
      border-radius: 0 0 6px 6px;
      border-top: 1px solid #404040;
      color: #f0f0f0;
    }
    .add-button { 
      font-size: 14px; 
      padding: 12px 20px; 
      margin-top: 16px; 
      cursor: pointer;
      background: #10a37f; 
      color: white; 
      border: none; 
      border-radius: 6px;
      width: 100%;
      font-weight: 500;
      transition: background-color 0.2s;
    }
    .add-button:hover { 
      background: #0d8f6f; 
    }
    .current-info {
      background: #1a1a1a;
      padding: 16px;
      border-radius: 6px;
      border: 1px solid #404040;
      margin-bottom: 16px;
    }
    .duration-text {
      font-size: 18px; 
      font-weight: 600;
    }
    .remaining-text {
      font-size: 32px; 
      font-weight: 700;
    }
    .progress-container {
      width: 100%;
      height: 10px;
      background: #404040;
      border-radius: 5px;
      margin-bottom: 12px;
      position: relative;
      cursor: pointer;
    }
    .progress-bar {
      height: 100%;
      background: #10a37f;
      border-radius: 5px;
      width: 0%;
      transition: width 0.2s;
    }
    .progress-handle {
      width: 16px;
      height: 16px;
      background: #e0e0e0;
      border-radius: 50%;
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
      left: 0%;
      cursor: grab;
    }
    .progress-handle:active {
      cursor: grabbing;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="left-column">
      <div class="panel">
        <div class="title">Agregar enlaces de YouTube</div>
        <textarea id="url" placeholder="Pega acá varios links o texto con links de YouTube..."></textarea>
        <button class="add-button" onclick="add()">Agregar a lista</button>
      </div>
    </div>

    <div class="center-column">
      <div class="panel">
        <div class="title">Lista de reproducción</div>
        <ul id="sortable" class="playlist"></ul>
        <div class="total-time" id="totaltime">Duración total: --:--</div>
        <div class="controls">
          <button onclick="prev()">⏮️</button>
          <button onclick="togglePlay()">⏯️</button>
          <button onclick="stop()">⏹️</button>
          <button onclick="next()">⏭️</button>
        </div>
      </div>
    </div>

    <div class="right-column">
      <div class="panel">
        <div class="title">Pista actual</div>
        <div class="current-info">
          <div class="progress-container" id="progress-container">
            <div class="progress-bar" id="progress-bar">
              <div class="progress-handle" id="progress-handle"></div>
            </div>
          </div>
          <div id="current" style="font-size: 16px; font-weight: 500; margin-bottom: 8px;">Ninguna pista</div>
          <div class="info">
            <span><b>Duración:</b> <span id="dur" class="duration-text">--:--</span></span> |
            <span><b>Restante:</b> <span id="left" class="remaining-text">--:--</span></span> |
            <span><b>Volumen:</b> <input type="range" id="vol" min="0" max="100" value="100" oninput="setVolume(this.value)" /></span>
            <label><input type="checkbox" id="auto" checked> Reproducir lista completa</label>
          </div>
        </div>
      </div>
      <div class="panel">
        <div class="title">Pista siguiente</div>
        <div class="current-info">
          <div id="nexttrack">Ninguna pista seleccionada</div>
        </div>
      </div>
    </div>
  </div>

  <div id="player"></div>

  <script src="https://www.youtube.com/iframe_api"></script>
  <script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
  <script>
    let playlist = [];
    let current = -1;
    let nextTrack = -1;
    let player;
    let paused = false;
    let timer;
    let isDragging = false;

    function formatTime(t) {
      let m = Math.floor(t / 60), s = Math.floor(t % 60);
      return String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
    }

    function updateTotalTime() {
      let sum = playlist.reduce((acc, t) => acc + (t.duration || 0), 0);
      document.getElementById("totaltime").innerText = "Duración total: " + formatTime(sum);
    }

    function extractYouTubeIDs(text) {
      let regex = /(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([\w-]{11})/g;
      let matches = [...text.matchAll(regex)];
      return matches.map(m => m[1]);
    }

    function add() {
      const input = document.getElementById("url");
      const ids = extractYouTubeIDs(input.value.trim());
      if (ids.length === 0) return alert("No se detectaron enlaces válidos de YouTube.");
      ids.forEach(id => {
        if (!playlist.some(t => t.id === id)) {
          let trackIndex = playlist.length;
          playlist.push({ id, title: `Cargando... (${id})`, duration: 0 });
          render();

          fetch('/extract_audio', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: `https://youtube.com/watch?v=${id}` })
          })
          .then(res => res.json())
          .then(data => {
            if (!data.error) {
              playlist[trackIndex].title = data.title || id;
              playlist[trackIndex].duration = data.duration || 0;
            } else {
              playlist[trackIndex].title = `Error: ${id}`;
            }
            render();
          })
          .catch(err => {
            playlist[trackIndex].title = `Error de conexión: ${id}`;
            render();
          });
        }
      });
      input.value = "";
    }

    function render() {
      const ul = document.getElementById("sortable");
      ul.innerHTML = "";
      playlist.forEach((track, i) => {
        let li = document.createElement("li");
        li.className = "track";
        if (i === current && !paused) li.classList.add("playing");
        else if (i === nextTrack) li.classList.add("next");
        else if (i > current) li.classList.add("queued");

        let durText = track.duration > 0 ? formatTime(track.duration) : "--:--";

        const spanText = document.createElement("span");
        spanText.className = "track-title";
        spanText.textContent = `${track.title} (${durText})`;
        spanText.onclick = () => { nextTrack = i; render(); };
        spanText.ondblclick = () => play(i);

        li.appendChild(spanText);
        ul.appendChild(li);
      });
      document.getElementById("current").innerText = current >= 0 ? playlist[current].title : "Ninguna pista";
      document.getElementById("nexttrack").innerText = nextTrack >= 0 ? playlist[nextTrack].title : "Ninguna pista seleccionada";
      updateTotalTime();
    }

    function onYouTubeIframeAPIReady() {
      player = new YT.Player("player", {
        height: "0", width: "0", 
        playerVars: { 'autoplay': 0, 'controls': 0 },
        events: {
          onReady: (event) => console.log("YouTube player ready"),
          onStateChange: e => {
            if (e.data === YT.PlayerState.ENDED && document.getElementById("auto").checked) next();
            if(e.data === YT.PlayerState.PLAYING) { paused = false; updateTimer(); render(); }
            if(e.data === YT.PlayerState.PAUSED) { paused = true; stopTimer(); render(); }
          }
        }
      });
    }

    function play(i) {
      if (i < 0 || i >= playlist.length || !player) return;
      current = i;
      paused = false;
      player.loadVideoById(playlist[i].id);
      updateTimer();
      render();
    }

    function togglePlay() {
      if (!player) return;
      const state = player.getPlayerState();
      if (state === YT.PlayerState.PLAYING) { 
        paused = true; 
        player.pauseVideo(); 
      } else if (state === YT.PlayerState.PAUSED) { 
        paused = false; 
        player.playVideo(); 
      } else if (playlist.length > 0) {
        play(current >= 0 ? current : 0);
      }
      render();
    }

    function stop() {
      paused = false; 
      current = -1;
      if (player) player.stopVideo();
      stopTimer(); 
      render();
    }

    function next() {
      if (nextTrack >= 0) {
        play(nextTrack);
        nextTrack = -1;
      } else if (current + 1 < playlist.length) {
        play(current + 1);
      } else {
        stop();
      }
    }

    function prev() {
      if (current > 0) play(current - 1);
    }

    function updateTimer() {
      stopTimer();
      timer = setInterval(() => {
        if (!player) return;
        try {
          let dur = Math.floor(player.getDuration());
          let cur = Math.floor(player.getCurrentTime());
          if (dur > 0 && cur >= 0) {
            document.getElementById("dur").innerText = formatTime(dur);
            document.getElementById("left").innerText = formatTime(Math.max(0, dur - cur));
            const progress = (cur / dur) * 100;
            document.getElementById("progress-bar").style.width = `${progress}%`;
            document.getElementById("progress-handle").style.left = `${progress}%`;
          }
        } catch (error) {
          console.error("Timer error:", error);
        }
      }, 1000);
    }

    function stopTimer() {
      clearInterval(timer);
      document.getElementById("progress-bar").style.width = "0%";
      document.getElementById("progress-handle").style.left = "0%";
    }

    function setVolume(v) {
      if (player) player.setVolume(parseInt(v));
    }

    // Progress bar interaction
    const progressContainer = document.getElementById("progress-container");
    const progressHandle = document.getElementById("progress-handle");

    progressContainer.addEventListener("click", (e) => {
      if (!player) return;
      const rect = progressContainer.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const width = rect.width;
      const seekTo = (clickX / width) * player.getDuration();
      player.seekTo(seekTo, true);
      if (player.getPlayerState() !== YT.PlayerState.PLAYING) {
        player.playVideo();
        paused = false;
      }
    });

    progressHandle.addEventListener("mousedown", () => {
      isDragging = true;
    });

    document.addEventListener("mousemove", (e) => {
      if (isDragging && player) {
        const rect = progressContainer.getBoundingClientRect();
        let newX = e.clientX - rect.left;
        newX = Math.max(0, Math.min(newX, rect.width));
        const seekTo = (newX / rect.width) * player.getDuration();
        const progress = (newX / rect.width) * 100;
        document.getElementById("progress-bar").style.width = `${progress}%`;
        document.getElementById("progress-handle").style.left = `${progress}%`;
        player.seekTo(seekTo, true);
      }
    });

    document.addEventListener("mouseup", () => {
      if (isDragging && player && player.getPlayerState() !== YT.PlayerState.PLAYING) {
        player.playVideo();
        paused = false;
      }
      isDragging = false;
    });

    new Sortable(document.getElementById("sortable"), {
      animation: 150,
      onEnd: function (evt) {
        const moved = playlist.splice(evt.oldIndex, 1)[0];
        playlist.splice(evt.newIndex, 0, moved);
        if (current === evt.oldIndex) current = evt.newIndex;
        else if (evt.oldIndex < current && evt.newIndex >= current) current--;
        else if (evt.oldIndex > current && evt.newIndex <= current) current++;
        render();
      }
    });
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(content=HTML_PAGE)

@app.post("/extract_audio")
async def extract_audio(request: Request):
    data = await request.json()
    url = data.get("url")
    if not url:
        return JSONResponse({"error": "URL vacía"}, status_code=400)

    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "extract_flat": False,
        "forcejson": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title", "Sin título"),
                "duration": int(info.get("duration", 0)),
                "audio_url": info.get("url", "")
            }
    except Exception as e:
        return JSONResponse({"error": f"Error: {str(e)}"}, status_code=500)

# Los endpoints de Instagram fueron eliminados para simplificar la aplicación

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
