# Marcus Development Roadmap

## Vision

Transform Marcus from a functional MVP into a robust, intelligent academic operating environment while maintaining local-first architecture and privacy guarantees.

---

## v0.1 - MVP (Current Release)

**Status**: ✅ Complete

**Goal**: Working end-to-end system for basic academic workflow

### Features
- ✅ Class management (create, list)
- ✅ Assignment tracking (create, update, view)
- ✅ File upload and storage (content-addressed vault)
- ✅ Text extraction (PDF, images via OCR, DOCX, plain text)
- ✅ Template-based plan generation
- ✅ Online mode toggle infrastructure
- ✅ Audit logging system
- ✅ Export to ZIP bundles
- ✅ Web UI (HTML/JS)
- ✅ FastAPI backend
- ✅ SQLite database
- ✅ Windows startup script

### Limitations
- No LLM integration
- No actual online features (just infrastructure)
- Basic UI (functional but not polished)
- No export button in UI yet
- No OCR if Tesseract not installed
- No tests
- No multi-file plan analysis

---

## v0.2 - Intelligence Layer

**Target**: 2-3 weeks after v0.1

**Goal**: Add local LLM support and improve plan quality

### Features

#### LLM Integration
- [ ] Ollama integration for local LLM
- [ ] Model selection UI (choose from available models)
- [ ] Prompt templates for plan generation
- [ ] Structured output parsing
- [ ] Fallback to template mode if LLM unavailable

#### Enhanced Plan Generation
- [ ] Multi-file context aggregation
- [ ] Analyze all extracted text together
- [ ] Detect assignment type (essay, problem set, code project, etc.)
- [ ] Custom plan templates per assignment type
- [ ] Confidence scoring based on available context

#### UI Improvements
- [ ] Export button in assignment view
- [ ] Plan comparison (compare multiple generated plans)
- [ ] Markdown preview for plans
- [ ] File preview (images, PDFs in browser)
- [ ] Drag-and-drop file upload

#### Quality of Life
- [ ] Assignment status workflow (todo → in progress → done)
- [ ] Due date reminders
- [ ] Search assignments and files
- [ ] Filter by class, status, date
- [ ] Bulk file upload

### Technical Improvements
- [ ] Error handling and user-friendly error messages
- [ ] Loading states for long operations
- [ ] Progress bars for file extraction
- [ ] Retry logic for failed extractions
- [ ] Database migrations (Alembic)

---

## v0.3 - Online Intelligence

**Target**: 1-2 months after v0.2

**Goal**: Implement safe, audited online research capabilities

### Features

#### Web Search Integration
- [ ] Web search API integration (DuckDuckGo or similar)
- [ ] Domain allowlist configuration
- [ ] Search result caching
- [ ] Citation extraction and formatting
- [ ] Source credibility scoring

#### Research Assistant
- [ ] "Research this topic" feature
- [ ] Automated fact-checking with citations
- [ ] Multi-source verification
- [ ] Confidence intervals on facts
- [ ] Link preservation for future reference

#### Cloud LLM Support (Optional)
- [ ] API key management (secure storage)
- [ ] Provider selection (OpenAI, Anthropic, etc.)
- [ ] Token usage tracking
- [ ] Cost estimation
- [ ] Rate limiting

#### Enhanced Audit Logging
- [ ] Audit log export (CSV, JSON)
- [ ] Audit log visualization
- [ ] Filter logs by event type, date, online/offline
- [ ] Audit alerts (notify on online mode use)

### Security Enhancements
- [ ] Encrypted API key storage
- [ ] Domain allowlist UI
- [ ] Max tokens per session limit
- [ ] Online mode auto-timeout
- [ ] Sensitive data detection (warn before upload)

---

## v0.4 - Collaboration & Export

**Target**: 2-3 months after v0.3

**Goal**: Better exports, sharing, and collaboration features

### Features

#### Enhanced Exports
- [ ] PDF generation from plans (reportlab)
- [ ] DOCX generation from plans (python-docx)
- [ ] Custom export templates
- [ ] Export profiles (minimal, standard, comprehensive)
- [ ] Password-protected ZIP exports
- [ ] Digital signatures on exports

#### Collaboration Features
- [ ] Export shareable assignment bundle (anonymized)
- [ ] Import assignment bundle
- [ ] Peer review mode (import others' work)
- [ ] Study group workspace
- [ ] Shared vault (optional, explicit)

#### Assignment Templates
- [ ] Assignment type templates
  - Essay template
  - Problem set template
  - Code project template
  - Research paper template
- [ ] Custom template creation
- [ ] Template library

#### Study Tools
- [ ] Flashcard generation from extracted text
- [ ] Quiz generation (multiple choice, fill-in-blank)
- [ ] Study schedule planner
- [ ] Review tracker (spaced repetition)

### UI/UX Improvements
- [ ] Dark/light theme toggle
- [ ] Keyboard shortcuts
- [ ] Mobile-responsive design
- [ ] Accessibility improvements (ARIA labels)
- [ ] Better typography and spacing

---

## v0.5 - Advanced Features

**Target**: 3-4 months after v0.4

**Goal**: Power user features and system robustness

### Features

#### Advanced File Processing
- [ ] PowerPoint/slide extraction
- [ ] Excel/CSV parsing
- [ ] Audio transcription (Whisper)
- [ ] Video frame extraction
- [ ] Handwriting recognition (IAM dataset)
- [ ] Table extraction from PDFs

#### Intelligent Workflows
- [ ] Assignment dependency tracking (A depends on B)
- [ ] Auto-schedule based on due dates
- [ ] Task time estimation (ML-based)
- [ ] Progress tracking with burndown charts
- [ ] Procrastination alerts

#### Knowledge Graph
- [ ] Build knowledge graph from extracted text
- [ ] Concept linking across assignments
- [ ] Prerequisites detection
- [ ] Related materials suggestions
- [ ] Concept mastery tracking

#### Integrations
- [ ] Canvas LMS integration (import assignments)
- [ ] Google Calendar sync
- [ ] Notion export
- [ ] Obsidian markdown export
- [ ] Git repository export

### System Improvements
- [ ] Full test suite (pytest)
  - Unit tests for all services
  - Integration tests for API
  - E2E tests for critical flows
- [ ] Performance optimization
  - Database indexing
  - Lazy loading for large files
  - Caching for frequent queries
- [ ] Deployment options
  - Docker container
  - Desktop app (Tauri)
  - Portable executable (PyInstaller)

---

## Future Ideas (v1.0+)

### Academic Writing Assistant
- Grammar and style checking
- Citation management (BibTeX)
- Plagiarism detection (local)
- Writing analytics

### Advanced Analytics
- Study time tracking
- Productivity insights
- Assignment difficulty prediction
- Grade prediction based on effort

### Multi-User Features
- Team projects mode
- Shared assignment workspaces
- Role-based access (student, TA, professor)
- Comment threads on artifacts

### Platform Expansion
- Mobile app (React Native)
- Browser extension
- VS Code extension
- Command-line interface

### AI Tutoring
- Interactive Q&A on assignment topics
- Step-by-step problem solving
- Concept explanations with examples
- Practice problem generation

---

## Principles Guiding Development

Throughout all versions, Marcus will maintain:

1. **Local-First Architecture**
   - Core features always work offline
   - Online features are optional enhancements
   - Data stored locally by default

2. **Privacy by Default**
   - No telemetry
   - No required accounts
   - No data sent to external services without explicit permission

3. **Transparency**
   - Audit logs for all significant actions
   - Clear indicators of online/offline state
   - Open source (if released publicly)

4. **Academic Integrity**
   - Tool assists, doesn't replace learning
   - Encourages citation and attribution
   - Promotes understanding over answers

5. **Simplicity**
   - Easy to install and run
   - Clear, intuitive UI
   - Minimal dependencies

6. **Reliability**
   - Graceful degradation (LLM unavailable? Use templates)
   - Clear error messages
   - Data integrity guarantees

---

## How to Contribute to the Roadmap

If you have ideas or want to prioritize features:

1. **Feature Requests**: Open an issue describing the use case
2. **Bug Reports**: Report issues with steps to reproduce
3. **Pull Requests**: Implement features from the roadmap
4. **User Feedback**: Share your experience using Marcus

---

## Release Schedule

- **v0.1**: January 2026 (✅ Released)
- **v0.2**: February 2026 (target)
- **v0.3**: March-April 2026 (target)
- **v0.4**: May-June 2026 (target)
- **v0.5**: August 2026 (target)
- **v1.0**: End of 2026 (aspirational)

Schedule is flexible and depends on:
- User feedback
- Feature complexity
- Available development time

---

**Marcus is a living project.** This roadmap will evolve based on real-world usage and community input.

*Last Updated: January 10, 2026*
