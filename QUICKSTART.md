# Marcus Quick Start Guide

## 5-Minute Setup

### Step 1: Start Marcus

Open PowerShell or Command Prompt and run:

```bash
cd C:\Users\conno\marcus
run.bat
```

Wait for the server to start. You'll see:
```
Marcus server started successfully
Open your browser to: http://localhost:8000
```

### Step 2: Open Your Browser

Navigate to: **http://localhost:8000**

You should see the Marcus interface with:
- Header: "Marcus - Local-First Academic Operating Environment"
- Status bar showing: "0 Classes | 0 Assignments | 0 Files"
- Online Mode toggle (should show "OFFLINE")
- Three tabs: Classes, Assignments, Audit Log

### Step 3: Create Your First Class

Based on your screenshot showing your courses:

1. Click the **"+ Create Class"** button
2. Fill in the form:
   - **Class Code**: `26SPECE34701`
   - **Class Name**: `26SP Embedded System Design 01`
3. Click **"Create Class"**

Repeat for your other classes:
- `26SPBIOL10302` - `26SP Environmental Issues 02`
- `26SPORTS26001` - `26SP Music and Media 01`
- `26SPECE35801` - `26SP Sr Design Lab & Sem 01`

### Step 4: Create an Assignment

1. Click the **"Assignments"** tab
2. Click **"+ Create Assignment"**
3. Fill in the form:
   - **Class**: Select one of your classes
   - **Title**: e.g., "Lab 1: Introduction to Embedded Systems"
   - **Description**: Add any details
   - **Due Date**: Select date and time
4. Click **"Create Assignment"**

### Step 5: Upload a File

1. Click on your assignment (it will appear in the list)
2. A modal will open showing assignment details
3. In the **Files** section:
   - Click "Choose File" and select a PDF, image, or document
   - Click **"Upload File"**
4. Once uploaded, click **"Extract Text"** to process it

### Step 6: Generate a Plan

1. In the same assignment modal, scroll down to the **Plans** section
2. Click **"Generate Plan"**
3. Wait a few seconds
4. A structured plan will appear with:
   - Steps (numbered breakdown)
   - Required materials
   - Output formats
   - Draft outline
   - Effort estimate (S/M/L)
   - Confidence level

### Step 7: Review the Plan

The plan will show:
- **Steps**: Sequential tasks to complete the assignment
- **Assumptions**: What the plan assumes
- **Risks & Unknowns**: What might be unclear
- **Confidence**: How confident the plan is (based on available info)

## Common Workflows

### Workflow 1: Organizing a Lab Assignment

```
1. Create Class (if not already created)
2. Create Assignment with lab title and due date
3. Upload lab manual PDF
4. Extract text from PDF
5. Upload any starter code files
6. Generate plan
7. Review plan and start working
```

### Workflow 2: Research Paper

```
1. Create Assignment for the paper
2. Upload research papers (PDFs)
3. Upload screenshots of key figures
4. Extract text from all materials
5. Generate plan (will suggest outline)
6. Work through steps
7. Export bundle when done
```

### Workflow 3: Problem Set

```
1. Create Assignment
2. Upload problem set PDF
3. Extract text to see problems
4. Upload any reference materials
5. Generate plan (breaks down problems)
6. Work through each step
```

## Tips & Tricks

### File Types Supported

- **PDFs**: Text extraction works automatically
- **Images** (PNG, JPG): OCR if Tesseract is installed
- **DOCX**: Text extraction works automatically
- **Code files**: Read as plain text
- **Markdown/Text**: Direct text storage

### Online Mode

- Default is **OFFLINE** (safe, private)
- Toggle ON only if you need future online features
- All online activity is logged in Audit Log tab
- Toggle back OFF when done

### Viewing Audit Logs

1. Click **"Audit Log"** tab
2. See all actions:
   - File uploads
   - Text extractions
   - Plan generations
   - Online mode toggles
3. Each log shows timestamp and details

### Export (Coming Soon in UI)

Currently export works via API:
```bash
curl -O http://localhost:8000/api/assignments/1/export
```

Will download a ZIP with:
- Plans (markdown)
- Uploaded files
- Extracted text
- Manifest JSON

## Troubleshooting

### Server won't start

**Problem**: `run.bat` shows errors

**Solutions**:
1. Check Python version: `python --version` (need 3.12+)
2. Delete `venv` folder and try again
3. Run manually: `python main.py`

### OCR not working

**Problem**: Image uploads don't extract text

**Solution**:
1. Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
2. Add to PATH
3. Restart Marcus

### Page won't load

**Problem**: Browser shows "Can't connect"

**Solution**:
1. Check if server is running (see terminal output)
2. Try: http://127.0.0.1:8000 instead
3. Check if port 8000 is blocked by firewall

### Files not uploading

**Problem**: Upload fails or times out

**Solutions**:
1. Check file size (very large files may timeout)
2. Try a smaller file first
3. Check browser console for errors (F12)

## Next Steps

Once comfortable with the basics:

1. **Organize all your classes** - Add all 4 courses
2. **Add all current assignments** - Track everything in one place
3. **Upload course materials** - Syllabi, lecture notes, etc.
4. **Generate plans** - For each major assignment
5. **Review Audit Logs** - See what Marcus is doing

## Keyboard Shortcuts (Future)

Not yet implemented, but planned for v0.2:
- `Ctrl+N`: New assignment
- `Ctrl+U`: Upload file
- `Ctrl+P`: Generate plan
- `Esc`: Close modal

## Getting Help

- Check [README.md](README.md) for detailed docs
- See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how it works
- Read [docs/SECURITY.md](docs/SECURITY.md) for privacy info
- Review [docs/ROADMAP.md](docs/ROADMAP.md) for future features

## Stopping Marcus

To stop the server:
1. Go back to the terminal/PowerShell window
2. Press `Ctrl+C`
3. Server will shut down gracefully

To restart:
```bash
run.bat
```

---

**You're all set!** Marcus is now running and ready to help you organize your coursework.

Remember: Marcus is a **local-first tool**. Your data stays on your machine. Work offline by default, and only enable online mode if you need it for future features.
