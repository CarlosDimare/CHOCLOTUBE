# Choclotube

Choclotube is a simple web application that allows you to create and play a playlist of YouTube videos. It extracts the audio from YouTube links and lets you manage the playback queue.

## Features

*   **Create Playlists from Links**: Paste multiple YouTube links to build a playlist.
*   **Audio Playback**: Plays the audio stream from YouTube videos without the video.
*   **Playback Controls**: Standard controls including play/pause, next, previous, and stop.
*   **Sortable Playlist**: Drag and drop to reorder tracks in the playlist.
*   **Volume Control** and **Progress Bar**.
*   **Dark-themed UI**.
*   **Total Playlist Duration**: See the total time for all tracks in the list.

## How to Run

There are two ways to run Choclotube.

### 1. Running from Source (All Platforms)

This method requires Python 3.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/choclotube.git
    cd choclotube
    ```

2.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: You also need to have FFmpeg installed on your system. You can download it from [ffmpeg.org](https://ffmpeg.org/download.html).*

3.  **Run the application:**
    ```bash
    uvicorn choclotube:app --host 0.0.0.0 --port 7860
    ```

4.  Open your web browser and go to `http://localhost:7860`.

### 2. Running the Windows Executable

A standalone `.exe` file is built automatically via GitHub Actions.

1.  Go to the "Actions" tab of this repository.
2.  Find the latest successful workflow run for the `main` branch.
3.  Download the `choclotube-exe` artifact.
4.  Unzip the downloaded file and run `choclotube.exe`. This will open the application in your default web browser.

## Technologies Used

*   **Backend**: FastAPI, Uvicorn
*   **Audio Extraction**: yt-dlp
*   **Frontend**: HTML5, CSS3, JavaScript
*   **UI Components**: SortableJS for the draggable playlist.
*   **Packaging**: PyInstaller (for the Windows executable).
