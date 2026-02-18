# 🎬 YouTube Downloader

Aplicación web para descargar videos y audio de YouTube. Soporta MP4 en múltiples calidades (360p hasta 4K) y MP3.

## 🚀 Deploy en Railway

### Opción 1: Desde GitHub (recomendado)

1. **Sube el código a GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/yt-downloader.git
   git push -u origin main
   ```

2. **Crea un proyecto en Railway:**
   - Ve a [railway.app](https://railway.app) y crea una cuenta
   - Haz clic en **"New Project"**
   - Selecciona **"Deploy from GitHub repo"**
   - Conecta tu cuenta de GitHub y selecciona el repositorio

3. **Railway detecta automáticamente:**
   - Python + Flask
   - Instala `ffmpeg` (definido en `railway.toml`)
   - Usa Gunicorn para producción

4. ¡Listo! Railway genera una URL pública automáticamente.

---

### Opción 2: Railway CLI

```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

---

## 🛠️ Uso local

```bash
pip install -r requirements.txt
python app.py
```

Abre `http://localhost:5000`

## 📁 Estructura

```
yt-downloader/
├── app.py              # Backend Flask
├── templates/
│   └── index.html      # Frontend
├── requirements.txt
├── Procfile
├── railway.toml        # Config de Railway (incluye ffmpeg)
├── runtime.txt
└── .gitignore
```

## ⚠️ Notas

- Los archivos se eliminan automáticamente 30 segundos después de descargarse.
- Railway tiene un plan gratuito con 500 horas/mes.
- `ffmpeg` es necesario para combinar video+audio y extraer MP3.
