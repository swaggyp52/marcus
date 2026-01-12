# Marcus v052 - UI Architecture Guide

## Visual Layout

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                         NAVBAR (60px)                                    ║
║  ◉ Marcus  | Your offline AI research agent  |  🟢 Online   | ⚙️ Settings  ║
╠══════════════════╦═════════════════════════════════════╦══════════════════╣
║                  ║                                     ║                  ║
║   LEFT SIDEBAR   ║      CENTER SECTION                ║   RIGHT SIDEBAR  ║
║    (280px)       ║         (1fr)                       ║      (360px)     ║
║                  ║                                     ║                  ║
║ Knowledge Graph  ║  ╭─────────────────────────────╮   ║  Chat Messages   ║
║ ┌──────────────┐ ║  │   ADD DOCUMENTS              │   ║  ╭────────────┐  ║
║ │   Legend     │ ║  │   Drag files here or click   │   ║  │ Marcus: Hi! │  ║
║ │ • Classes    │ ║  │        to browse             │   ║  ╰────────────╯  ║
║ │ • Tasks      │ ║  ╰─────────────────────────────╯   ║  ╭────────────┐  ║
║ │ • Files      │ ║                                     ║  │ User: Help  │  ║
║ └──────────────┘ ║  UPLOAD PROGRESS                    ║  ╰────────────╯  ║
║                  ║  📄 file1.pdf        [████░░] 60%   ║                  ║
║ STATISTICS       ║  📄 file2.docx       [██░░░░░] 25%   ║  Input with hints║
║ • Documents: 3   ║                                     ║  [What is this?] ║
║ • Concepts: 12   ║  DOCUMENTS                          ║  [Summarize]     ║
║ • Relations: 8   ║  ╭────────────┬────────────┐        ║  [Find patterns] ║
║                  ║  │ 📄 Doc1    │ 📄 Doc2    │        ║  [Study guide]   ║
║ 🔄 Refresh       ║  │ 125 KB     │ 89 KB      │        ║                  ║
║                  ║  ├────────────┼────────────┤        ║  [⚙️ Settings ▲]  ║
║                  ║  │ 📄 Doc3    │            │        ║                  ║
║                  ║  │ 42 KB      │            │        ║                  ║
║                  ║  ╰────────────┴────────────╯        ║                  ║
║                  ║                                     ║                  ║
║ 🖱️ Canvas        ║  ACTIVITY LOG                       ║                  ║
║ (Force-directed) ║  11:45 Marcus initialized          ║                  ║
║                  ║  11:46 Uploaded: report.pdf        ║                  ║
║  ⊙─────⊙         ║  11:47 Processed: 3 documents      ║                  ║
║   \ | /          ║  11:48 Chat created class TEST101  ║                  ║
║    \|/           ║                                     ║                  ║
║   ──⊙──          ║                                     ║                  ║
║   / | \          ║                                     ║                  ║
║  ⊙─────⊙         ║                                     ║                  ║
║                  ║                                     ║                  ║
╚═════════════════════════════════════════════════════════════════════════════╝
```

## Component Breakdown

### Navbar
```
┌─────────────────────────────────────────┐
│  ◉ Marcus (pulse-glow)                 │
│  Your offline AI research agent         │
│                      🟢 Online ⚙️ Settings
└─────────────────────────────────────────┘
```
- **Brand Icon**: ◉ with animated pulse-glow effect
- **Status**: Real-time online/offline indicator (green dot)
- **Settings**: Click to open settings modal

### Left Sidebar - Knowledge Graph
```
┌─────────────────────────┐
│ KNOWLEDGE GRAPH STATS   │
├─────────────────────────┤
│                         │
│  Documents    3         │
│  Concepts     12        │
│  Connections  8         │
│                         │
├─────────────────────────┤
│ GRAPH LEGEND            │
├─────────────────────────┤
│ ⊙ Classes (blue)       │
│ ⊙ Tasks (yellow)       │
│ ⊙ Files (cyan)         │
│                         │
│ ━ Assignment relation   │
│ ━ Reference relation    │
├─────────────────────────┤
│                         │
│  [Canvas Visualization] │
│                         │
│  ⊙────⊙────⊙            │
│   \  |  /               │
│    ──⊙──                │
│   /  |  \               │
│  ⊙────⊙────⊙            │
│                         │
├─────────────────────────┤
│ 🔄 Refresh Graph        │
└─────────────────────────┘
```

### Center Section - Document Management
```
┌────────────────────────────────────┐
│ ADD DOCUMENTS                      │
│ ╭────────────────────────────────┐ │
│ │  Drag files here or click      │ │
│ │       to browse                │ │
│ │                                │ │
│ │     Supports: PDF, DOCX,       │ │
│ │     TXT, MD, and more          │ │
│ ╰────────────────────────────────╯ │
├────────────────────────────────────┤
│ UPLOAD PROGRESS                    │
│ 📄 research_paper.pdf              │
│ ████████░░░░░░░░░░░░ 40%           │
│                                    │
│ 📄 notes.docx                      │
│ ████████████░░░░░░░░ 60%           │
├────────────────────────────────────┤
│ YOUR DOCUMENTS                     │
│ ┌──────────────┬──────────────┐    │
│ │   📄 Doc1    │   📄 Doc2    │    │
│ │   123 KB     │   89 KB      │    │
│ │              │              │    │
│ │ research.pdf │ notes.docx   │    │
│ ├──────────────┼──────────────┤    │
│ │   📄 Doc3    │              │    │
│ │   42 KB      │              │    │
│ │              │              │    │
│ │ summary.pdf  │              │    │
│ └──────────────┴──────────────┘    │
├────────────────────────────────────┤
│ ACTIVITY LOG (Last 10 events)      │
│                                    │
│ 14:32 Marcus initialized           │
│ 14:33 ↓ Uploaded: research.pdf    │
│ 14:34 ↓ Uploaded: notes.docx      │
│ 14:35 ✓ Processed: 2 documents    │
│ 14:36 💬 Created class CS101      │
│ 14:37 💬 Found 4 relationships    │
│ 14:38 ↓ Uploaded: summary.pdf     │
│ 14:40 🔄 Graph updated            │
│                                    │
└────────────────────────────────────┘
```

### Right Sidebar - Chat
```
┌────────────────────────────┐
│ CHAT WITH MARCUS           │
├────────────────────────────┤
│                            │
│ Marcus: Hi! I'm your      │
│ research assistant.        │
│                            │
│ User: What's in the       │
│ documents?                 │
│                            │
│ Marcus: I found three     │
│ research papers on        │
│ machine learning...       │
│                            │
├────────────────────────────┤
│ [What is this?]            │
│ [Summarize]                │
│ [Find patterns]            │
│ [Study guide]              │
│                            │
│ ┌──────────────────────┐   │
│ │ Ask Marcus...        │ → │
│ └──────────────────────┘   │
│                            │
│ [⚙️ Settings ▼]           │
│                            │
│ Settings Modal:            │
│ ┌──────────────────────┐   │
│ │ API Port: 8000       │   │
│ │ Model: llama2        │   │
│ │ ☑ Auto-summarize     │   │
│ │ ☑ Show reasoning     │   │
│ │                      │   │
│ │ [Save]  [Reset]      │   │
│ └──────────────────────┘   │
│                            │
└────────────────────────────┘
```

## Color Reference

### Primary Colors
```
Navy (#0a0e27)        ■ Main background
Light Navy (#0f1535)  ■ Secondary background  
Dark Navy (#1a1f3a)   ■ Tertiary/hover state
```

### Accent Colors
```
Cyan (#00e6ff)       ■ Primary interactive elements
Magenta (#7c00ff)    ■ Secondary accents
Pink (#ff006e)       ■ Connection highlights
```

### Text Colors
```
Light (#e8eaff)      ■ Primary text
Medium (#b0b4cc)     ■ Secondary text
Muted (#7b7f9b)      ■ Disabled/muted text
```

## Animation Effects

### Pulse Glow
```
Navbar icon cycles:
  Start: box-shadow: 0 0 4px cyan
  Peak:  box-shadow: 0 0 12px cyan
  End:   box-shadow: 0 0 4px cyan
  Duration: 2 seconds, infinite loop
```

### Slide In (Messages)
```
Message enters from top:
  Start: translateY(-10px), opacity: 0
  End:   translateY(0), opacity: 1
  Duration: 0.3 seconds, ease-in-out
```

### Fade In (Modals)
```
Modal appears:
  Start: opacity: 0, scale: 0.95
  End:   opacity: 1, scale: 1
  Duration: 0.3 seconds
```

### Blink (Status Indicator)
```
Status dot cycles:
  Start: opacity: 1
  Mid:   opacity: 0.4
  End:   opacity: 1
  Duration: 1 second, infinite
```

## Responsive Breakpoints

### Desktop (1920px+)
- 3-column layout visible (280px | 1fr | 360px)
- Full graph visualization
- All features enabled

### Laptop (1200-1920px)
- 3-column layout
- Graph visible but may need scrolling
- All features enabled

### Tablet (768-1200px)
- Left sidebar hides
- 2-column layout (center | right)
- Graph access via icon toggle
- Touch-optimized spacing

### Mobile (<768px)
- Single column stack
- Sidebar toggles with hamburger menu
- Full-width chat and documents
- Optimized touch targets

## Interactive States

### Button States
```
Normal:   border: 1px cyan, bg: transparent
Hover:   border: 1px cyan, bg: rgba(0,230,255,0.1), box-shadow: 0 0 8px cyan
Active:  border: 1px cyan, bg: rgba(0,230,255,0.2)
Disabled: opacity: 0.5, cursor: not-allowed
```

### Upload Area States
```
Normal:    border: 2px dashed #7b7f9b
Hover:     border: 2px dashed #00e6ff, bg: rgba(0,230,255,0.05)
Dragging:  border: 2px solid #7c00ff, bg: rgba(124,0,255,0.1)
Uploading: border: 2px solid #00e6ff, progress bar visible
```

### Document Card States
```
Normal:   bg: rgba(15,21,53,0.5), border: 1px #1a1f3a
Hover:    bg: rgba(15,21,53,0.8), transform: translateY(-2px), 
          box-shadow: 0 8px 16px rgba(0,230,255,0.15)
Active:   border: 1px #00e6ff, box-shadow: 0 0 8px #00e6ff
```

## Usage Flow

1. **User launches app**
   - Navbar appears with pulse-glow icon
   - Status indicator shows "Initializing"
   - Left sidebar loads with graph (may be empty)
   - Center shows upload prompt
   - Right sidebar ready for chat

2. **User uploads documents**
   - Drag files to center section
   - Progress bars appear with filenames
   - Activity log shows "Uploaded: filename"
   - Documents grid populates with cards
   - Graph updates with new nodes

3. **User asks questions**
   - Types in chat input or clicks hints
   - Message appears in chat history (user role)
   - Marcus responds (assistant role)
   - Graph may refresh with new connections
   - Activity log records interaction

4. **User explores knowledge**
   - Clicks on document cards for details
   - Views graph relationships in left sidebar
   - Searches within documents
   - Reviews activity log for context
   - Adjusts settings via modal

## Styling Architecture

### CSS Variable Organization
```css
:root {
  /* Colors */
  --bg-primary: #0a0e27;
  --bg-secondary: #0f1535;
  --accent-cyan: #00e6ff;
  
  /* Effects */
  --shadow-md: 0 4px 12px rgba(0,0,0,0.3);
  --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  
  /* Spacing */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
}
```

### Component CSS Structure
```css
/* Navbar */
.navbar { /* layout */ }
.navbar-left { /* brand section */ }
.navbar-right { /* status & settings */ }

/* Sidebar */
.sidebar { /* common styles */ }
.sidebar-left { /* graph section */ }
.sidebar-right { /* chat section */ }

/* Main Content */
.main-container { /* 3-column grid */ }
.upload-box { /* drag-drop zone */ }
.documents-grid { /* card layout */ }

/* Chat */
.chat-messages { /* message container */ }
.message { /* individual message */ }
.message.user { /* user message style */ }
.message.assistant { /* assistant message style */ }

/* Modals */
.modal { /* modal overlay */ }
.modal-content { /* modal dialog */ }

/* Animations */
@keyframes pulse-glow { /* icon animation */ }
@keyframes slideIn { /* message animation */ }
@keyframes fadeIn { /* modal animation */ }
```

This architecture ensures consistency, maintainability, and excellent user experience across all device sizes and interaction patterns.
