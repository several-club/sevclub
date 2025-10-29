# Several.Club Local Development Server

## 🚀 Quick Start

### Option 1: Python Script (Recommended)
```bash
python3 start_server.py
```

### Option 2: Bash Script
```bash
./start_local.sh
```

### Option 3: Simple HTTP Server
```bash
python3 -m http.server 8000
```

## 🌐 Access Your Site

Once the server is running, open your browser and go to:
- **Main site**: http://localhost:8000
- **Index page**: http://localhost:8000/index.html
- **Case studies**: http://localhost:8000/remm.html, http://localhost:8000/bailet.html, etc.

## 🔄 Auto-Reload Features

The server includes:
- **No-cache headers**: Ensures fresh content on every reload
- **Auto-browser opening**: Automatically opens your default browser
- **File watching**: Monitors file changes (with live_server.py)

## 📁 File Structure

```
Several.Club/
├── index.html              # Main landing page
├── remm.html               # REMM case study
├── bailet.html             # Bailet case study
├── hyper-island.html       # Hyper Island case study
├── ...                     # Other case studies
├── css/                    # Stylesheets
├── images/                 # Images and assets
├── start_server.py         # Main server script
├── live_server.py          # Live-reload server
└── start_local.sh          # Bash launcher
```

## 🛠️ Development Workflow

1. **Start server**: `python3 start_server.py`
2. **Edit files**: Make changes to HTML, CSS, or images
3. **Refresh browser**: Changes appear immediately
4. **Stop server**: Press `Ctrl+C` in terminal

## 🎯 Case Study Navigation

All case study pages include:
- **Index/Next navigation** with SVG arrows
- **Sticky positioning** that follows scroll
- **Responsive design** for all screen sizes
- **Auto-linking** between case studies

## 🔧 Troubleshooting

### Port Already in Use
If port 8000 is busy, change the PORT variable in `start_server.py`:
```python
PORT = 8001  # or any other available port
```

### Python Not Found
Install Python 3:
```bash
# macOS
brew install python3

# Ubuntu/Debian
sudo apt install python3

# Windows
# Download from python.org
```

### Browser Doesn't Open
Manually navigate to: http://localhost:8000

## 📱 Mobile Testing

To test on mobile devices on the same network:
1. Find your computer's IP address
2. Access: http://[YOUR_IP]:8000
3. Example: http://192.168.1.100:8000

## 🎨 Features Included

- ✅ **Responsive design** for all devices
- ✅ **SVG navigation arrows** with correct ordering
- ✅ **Sticky navigation** that follows scroll
- ✅ **Max-width constraints** (1600px)
- ✅ **Auto-reload** on file changes
- ✅ **Cross-browser compatibility**
- ✅ **SEO-optimized** meta tags
- ✅ **Performance optimized** images

## 🚀 Production Deployment

For production deployment, consider:
- **Webflow hosting** (current setup)
- **Netlify** for static sites
- **Vercel** for JAMstack
- **GitHub Pages** for open source

---

**Happy coding! 🎉**
