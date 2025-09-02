# Choclotube

Choclotube es una aplicación web sencilla que te permite crear y reproducir una lista de videos de YouTube. Extrae el audio de los enlaces de YouTube y te permite gestionar la cola de reproducción.

## Características

*   **Crear listas de reproducción desde enlaces**: Pega múltiples enlaces de YouTube para construir una lista de reproducción.
*   **Reproducción de audio**: Reproduce el stream de audio de los videos de YouTube sin el video.
*   **Controles de reproducción**: Controles estándar que incluyen reproducir/pausar, siguiente, anterior y detener.
*   **Lista de reproducción ordenable**: Arrastra y suelta para reordenar las pistas en la lista de reproducción.
*   **Control de volumen** y **Barra de progreso**.
*   **Interfaz con tema oscuro**.
*   **Duración total de la lista**: Ve el tiempo total de todas las pistas en la lista.

## Cómo ejecutar

Hay dos formas de ejecutar Choclotube.

### 1. Ejecutar desde el código fuente (Todas las plataformas)

Este método requiere Python 3.

1.  **Clona el repositorio:**
    ```bash
    git clone https://github.com/your-username/choclotube.git
    cd choclotube
    ```

2.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```
    *Nota: También necesitas tener FFmpeg instalado en tu sistema. Puedes descargarlo desde [ffmpeg.org](https://ffmpeg.org/download.html).*

3.  **Ejecuta la aplicación:**
    ```bash
    uvicorn choclotube:app --host 0.0.0.0 --port 7860
    ```

4.  Abre tu navegador web y ve a `http://localhost:7860`.

### 2. Ejecutar el ejecutable de Windows

Un archivo `.exe` independiente se compila automáticamente a través de GitHub Actions.

1.  Ve a la pestaña "Actions" de este repositorio.
2.  Encuentra la última ejecución de flujo de trabajo exitosa para la rama `main`.
3.  Descarga el artefacto `choclotube-exe`.
4.  Descomprime el archivo descargado y ejecuta `choclotube.exe`. Esto abrirá la aplicación en tu navegador web predeterminado.

## Tecnologías utilizadas

*   **Backend**: FastAPI, Uvicorn
*   **Extracción de audio**: yt-dlp
*   **Frontend**: HTML5, CSS3, JavaScript
*   **Componentes de UI**: SortableJS para la lista de reproducción arrastrable.
*   **Empaquetado**: PyInstaller (para el ejecutable de Windows).
