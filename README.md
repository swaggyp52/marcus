# Marcus v0.5.2

A FastAPI + PyInstaller Windows desktop application with a neon Web UI (vanilla ES modules + canvas globe), backed by SQLModel/SQLite, packaged with PyInstaller/pywebview, and automation scripts for build/smoke-test on Windows.

## Features

- 🚀 **FastAPI Backend**: High-performance REST API built with FastAPI
- 💾 **SQLModel/SQLite Database**: Type-safe ORM with SQLite for data persistence
- 🎨 **Neon Web UI**: Cyberpunk-themed interface with glowing neon effects
- 🌍 **Interactive 3D Globe**: Canvas-based globe visualization with location markers
- 🖥️ **Desktop Application**: Native-looking desktop app using pywebview
- 📦 **PyInstaller Packaging**: Single-executable distribution
- 🔧 **Automation Scripts**: Build and smoke-test scripts for Windows and Unix

## Technology Stack

- **Backend**: FastAPI, SQLModel, Uvicorn
- **Frontend**: Vanilla JavaScript (ES Modules), HTML5 Canvas
- **Database**: SQLite
- **Desktop**: pywebview
- **Packaging**: PyInstaller
- **Styling**: Pure CSS with neon theme

## Project Structure

```
marcus/
├── backend/
│   ├── __init__.py
│   ├── api.py          # FastAPI application and routes
│   ├── database.py     # Database connection and initialization
│   └── models.py       # SQLModel data models
├── frontend/
│   ├── index.html      # Main HTML page
│   └── static/
│       ├── css/
│       │   └── styles.css    # Neon-themed styles
│       └── js/
│           ├── main.js       # Main application logic
│           ├── api.js        # API client module
│           └── globe.js      # 3D globe rendering
├── scripts/
│   ├── build.bat       # Windows build script
│   ├── build.sh        # Unix/Linux/Mac build script
│   ├── smoke-test.bat  # Windows smoke test
│   └── smoke-test.sh   # Unix/Linux/Mac smoke test
├── main.py             # Application entry point
├── marcus.spec         # PyInstaller specification
├── requirements.txt    # Python dependencies
├── pyproject.toml      # Project metadata
└── README.md          # This file
```

## Installation & Setup

### Prerequisites

- Python 3.9 or higher
- Windows OS (for full desktop app experience)
- Git

### Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/swaggyp52/marcus.git
   cd marcus
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**:
   - Windows: `venv\Scripts\activate`
   - Unix/Linux/Mac: `source venv/bin/activate`

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**:
   ```bash
   python main.py
   ```

## Building the Application

### Windows

Run the automated build script:
```bash
scripts\build.bat
```

This will:
1. Create/verify virtual environment
2. Install dependencies
3. Clean previous builds
4. Build the application with PyInstaller

The executable will be created at: `dist\Marcus\Marcus.exe`

### Unix/Linux/Mac

Run the automated build script:
```bash
./scripts/build.sh
```

The executable will be created at: `dist/Marcus/Marcus`

## Testing

### Smoke Tests

After building, run the smoke test to verify the application:

**Windows**:
```bash
scripts\smoke-test.bat
```

**Unix/Linux/Mac**:
```bash
./scripts/smoke-test.sh
```

The smoke test will:
1. Verify the executable exists
2. Check file sizes
3. Validate required files
4. Launch the application for manual verification

### Manual Testing Checklist

When the application launches, verify:
- ✅ Window opens successfully
- ✅ Neon UI is displayed with glowing effects
- ✅ Globe animation is working smoothly
- ✅ API status shows "✓ Online"
- ✅ Can add new items with the "Add New Item" button
- ✅ Items appear in the list
- ✅ Items with coordinates appear as markers on the globe
- ✅ Can delete items
- ✅ Refresh button updates the display

## API Endpoints

The application exposes the following REST API endpoints:

- `GET /api/health` - Health check
- `GET /api/items` - List all items
- `POST /api/items` - Create a new item
- `GET /api/items/{id}` - Get a specific item
- `PUT /api/items/{id}` - Update an item
- `DELETE /api/items/{id}` - Delete an item

## Database

The application uses SQLite with SQLModel for the ORM layer. The database includes:

### Tables

**Items**:
- `id` (Integer, Primary Key)
- `name` (String, Indexed)
- `description` (String, Optional)
- `latitude` (Float, Optional)
- `longitude` (Float, Optional)
- `created_at` (DateTime)
- `updated_at` (DateTime)

**AppSettings**:
- `id` (Integer, Primary Key)
- `key` (String, Indexed, Unique)
- `value` (String)
- `updated_at` (DateTime)

When running as a compiled executable, the database is stored in:
- `%USERPROFILE%\Marcus\marcus.db` (Windows)
- `~/Marcus/marcus.db` (Unix/Linux/Mac)

## UI Features

### Neon Theme
- Cyberpunk-inspired color scheme
- Glowing text effects with CSS animations
- Purple, blue, pink, and green neon colors
- Animated title with flickering effect
- Custom scrollbars with neon styling

### Interactive Globe
- Real-time 3D globe rotation
- Latitude and longitude grid lines
- Location markers for items with coordinates
- Smooth canvas-based animation
- Neon glow effects

### Data Management
- Add items with name, description, and coordinates
- View all items in a scrollable list
- Delete items with confirmation
- Real-time item count display
- System status indicators

## Development

### Running in Development Mode

```bash
python main.py
```

This starts:
1. FastAPI server on `http://127.0.0.1:8052`
2. pywebview window displaying the UI

### Project Architecture

The application follows a clean architecture:
- **Backend**: FastAPI handles HTTP requests and database operations
- **Frontend**: Vanilla JS modules for clean, maintainable code
- **Desktop**: pywebview wraps the web UI in a native window
- **Build**: PyInstaller packages everything into a single executable

## Troubleshooting

### Application won't start
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that port 8052 is not in use by another application
- Verify Python 3.9+ is installed

### Build fails
- Ensure PyInstaller is installed: `pip install pyinstaller`
- Check that all frontend files exist in the `frontend/` directory
- Review the build output for specific error messages

### Globe not rendering
- Check browser console for JavaScript errors
- Ensure canvas element is properly initialized
- Verify static files are being served correctly

## License

This project is provided as-is for educational and demonstration purposes.

## Version History

- **v0.5.2** (Current): Initial release with full feature set
  - FastAPI backend with SQLModel/SQLite
  - Neon-themed Web UI
  - 3D canvas globe visualization
  - pywebview desktop integration
  - PyInstaller packaging
  - Build and smoke-test automation

## Contributing

This is a demonstration project. Feel free to fork and modify for your own use.

## Author

Marcus Team