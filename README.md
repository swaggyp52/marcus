# Marcus - Local-First Academic Operating Environment

**Version 0.1.0 MVP**

Marcus is a privacy-first, offline-capable academic assistant designed to help you organize coursework, manage assignments, extract information from files, and generate structured work plans. Think of it as your personal Jarvis for classwork.

## Key Features

- **Local-First**: Everything runs on your machine by default. Your data stays private.
- **Offline-Capable**: Core functionality works without internet connection
- **File Processing**: Upload PDFs, images, DOCX, code files and extract text automatically
- **OCR Support**: Extract text from screenshots and scanned documents
- **Plan Generation**: Get structured, step-by-step plans for assignments
- **Trust Boundary**: Explicit online mode with full audit logging
- **Export Bundles**: Package assignments with plans, files, and extracted text

## Quick Start

### Prerequisites

- Python 3.12 or higher
- Windows 11 (or Windows 10 with minor adjustments)
- For OCR: Tesseract OCR (optional but recommended)

### Installation

1. **Navigate to the marcus directory:**
   ```bash
   cd marcus
   ```

2. **Run the startup script:**
   ```bash
   run.bat
   ```

   This will:
   - Create a virtual environment
   - Install dependencies
   - Start the Marcus server

3. **Open your browser:**
   ```
   http://localhost:8000
   ```

### Installing Tesseract OCR (Optional)

For image OCR capabilities:

1. Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install and add to PATH
3. Restart Marcus

Without Tesseract, image text extraction will fail gracefully with a helpful error message.

## Usage Guide

### 1. Create Classes

Based on your courses (e.g., "26SPECE34701: 26SP Embedded System Design 01"):

1. Click "Create Class"
2. Enter class code and name
3. Click "Create"

### 2. Create Assignments

1. Switch to "Assignments" tab
2. Click "Create Assignment"
3. Select class, enter title, description, and due date
4. Click "Create"

### 3. Upload Files

1. Click on an assignment
2. Select a file (PDF, image, DOCX, code, etc.)
3. Click "Upload File"
4. Click "Extract Text" to process the file

### 4. Generate Plans

1. Open an assignment
2. Click "Generate Plan"
3. Review the structured plan with:
   - Step-by-step breakdown
   - Required materials
   - Output formats
   - Draft outline
   - Effort estimates
   - Assumptions and risks

### 5. Online Mode (When Needed)

By default, Marcus runs offline. If you need online features:

1. Toggle "Online Mode" in the status bar
2. All online activity is logged in the Audit Log tab
3. Toggle off when done

### 6. Export Assignments

Export assignment bundles (coming soon in UI):
- Plans as markdown
- Original files
- Extracted text
- Manifest JSON
- All bundled in a ZIP file

## File Structure

```
marcus/
├── marcus_app/
│   ├── backend/         # FastAPI application
│   ├── frontend/        # Web UI (HTML/JS)
│   ├── core/            # Data models and database
│   ├── services/        # Business logic
│   ├── prompts/         # Future: LLM prompts
│   └── tests/           # Future: Test suite
├── vault/               # Immutable uploaded files
├── projects/            # Class workspaces
├── exports/             # Generated export bundles
├── storage/             # SQLite database
└── docs/                # Documentation
```

## Database Schema

- **classes**: Course information
- **assignments**: Assignment tracking
- **artifacts**: Uploaded files with metadata
- **extracted_texts**: Text extracted from files
- **plans**: Generated work plans
- **audit_logs**: Security and activity logging
- **system_config**: Application settings

## Security & Privacy

### Offline-First Philosophy

- All core features work without internet
- Files never leave your machine unless you explicitly enable online mode
- No telemetry or tracking

### Online Mode

When enabled:
- Logged in audit_logs table
- Timestamped with event type
- Can be reviewed in Audit Log tab
- Must be explicitly toggled

### File Safety

- Files stored with SHA-256 hash naming
- Original files immutable in vault
- Extraction errors don't expose file contents
- No automatic execution of code files

## Troubleshooting

### Server won't start

- Ensure Python 3.12+ is installed: `python --version`
- Check if port 8000 is available
- Try running directly: `python main.py`

### OCR not working

- Install Tesseract OCR
- Verify it's in PATH: `tesseract --version`
- Restart Marcus

### Files not uploading

- Check file size (very large files may timeout)
- Ensure vault directory has write permissions
- Check browser console for errors

### Database errors

- Delete `storage/marcus.db` to reset (WARNING: loses all data)
- Restart Marcus to recreate database

## Development

### Running in Development Mode

```bash
# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run with hot reload
python main.py
```

### API Documentation

Once running, view interactive API docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for the development roadmap from v0.1 to v0.5.

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for system architecture details.

## Security Model

See [docs/SECURITY.md](docs/SECURITY.md) for detailed security documentation.

## Contributing

This is a personal project for academic use. If you find it useful and want to extend it, feel free to fork and customize.

## License

MIT License - See LICENSE file

## Acknowledgments

Built with:
- FastAPI - Backend framework
- SQLAlchemy - ORM
- Tesseract - OCR engine
- pypdf - PDF processing
- python-docx - DOCX processing

---

**Marcus v0.1.0** - Your local-first academic operating environment
