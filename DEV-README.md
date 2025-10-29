# Several Club - Development Server

## 🚀 Start Development Server with Live Reload

### Option 1: Using Node.js (Recommended)
```bash
./start-live-server.sh
```

### Option 2: Using Python
```bash
./start-dev-server.sh
```

### Option 3: Manual Installation
```bash
# Install live-server globally
npm install -g live-server

# Start server
live-server --port=3000 --open=/index.html --watch=.
```

## 📁 What it does:
- ✅ Serves your website at `http://localhost:3000`
- ✅ Automatically opens your browser
- ✅ Watches for file changes in HTML, CSS, JS files
- ✅ Auto-reloads browser when you save changes
- ✅ No need to manually refresh!

## 🛠️ Development Workflow:
1. Run the development server
2. Open your browser to `http://localhost:3000`
3. Edit your HTML/CSS files
4. Save changes
5. Browser automatically reloads! 🎉

## 📝 Notes:
- The server watches all files in the current directory
- Changes to HTML, CSS, and JS files trigger automatic reload
- Press `Ctrl+C` to stop the server
- The server will automatically open your default browser
