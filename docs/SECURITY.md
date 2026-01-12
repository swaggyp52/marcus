# Marcus Security Model

## Overview

Marcus is designed with **security by default** and **privacy first**. This document outlines the security architecture, threat model, and safety guarantees.

## Core Security Principles

### 1. Offline-First

**Default State**: All operations run locally without network access.

**Rationale**:
- Your coursework is private
- No data leaves your machine without explicit permission
- No dependency on external services
- No telemetry or tracking

**Implementation**:
- Online mode OFF by default
- Gated by explicit user toggle
- All online activity logged

### 2. Explicit Trust Boundaries

**Offline Zone** (Trusted):
- File system access
- Local database
- Text extraction
- Plan generation

**Online Zone** (Requires Permission):
- Web requests
- API calls to external services
- Future: LLM API access

**Crossing the Boundary**:
- User must toggle online mode ON
- Every online action logged with:
  - Timestamp
  - Event type
  - Query/action
  - Domains accessed
  - Results summary

### 3. Audit Logging

Every significant action creates an immutable audit log entry:

```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    event_type TEXT,        -- e.g., "file_uploaded", "online_query"
    online_mode TEXT,       -- "offline" or "online"
    query TEXT,             -- What was requested
    domains_accessed TEXT,  -- Which external domains (JSON array)
    results_summary TEXT,   -- What was returned
    citations TEXT,         -- Source URLs (JSON array)
    user_action TEXT,       -- Human-readable description
    metadata TEXT           -- Additional context (JSON)
)
```

**Logged Events**:
- File uploads
- Text extraction
- Plan generation
- Online mode toggles
- Online queries (when implemented)
- Assignment exports

**Audit Log Access**:
- View in UI: Audit Log tab
- Query DB: `SELECT * FROM audit_logs ORDER BY timestamp DESC`
- Export for compliance/review

## Threat Model

### What Marcus Protects Against

#### 1. Unauthorized Data Exfiltration

**Threat**: Files or content leaving your machine without permission

**Mitigations**:
- Offline by default
- Online mode requires explicit toggle
- All network activity logged
- No background uploads
- No telemetry

#### 2. Accidental Exposure

**Threat**: Uploading sensitive files to cloud services accidentally

**Mitigations**:
- Local processing only
- Clear UI indicators (OFFLINE/ONLINE badge)
- Warnings when enabling online mode
- File extensions checked (.env files flagged in future versions)

#### 3. Malicious File Processing

**Threat**: Uploaded files contain exploits

**Mitigations**:
- Text extraction only, no execution
- Code files read as plain text
- PDF parsing via safe library (pypdf)
- Image processing via Pillow (sandboxed)
- No macros, scripts, or active content executed

#### 4. Data Tampering

**Threat**: Modification of uploaded files or generated plans

**Mitigations**:
- Files in vault/ are content-addressed (SHA-256)
- Original files never modified
- Database integrity via SQLite constraints
- Future: digital signatures on exports

### What Marcus Does NOT Protect Against

Marcus is a **local application** and does not protect against:

1. **Physical Access**: If someone has access to your computer, they can access Marcus data
2. **Operating System Compromise**: If your OS is compromised, Marcus data is accessible
3. **Database Direct Access**: Anyone with file system access can read `marcus.db`
4. **Backup Exposure**: If you backup `vault/` to cloud, files are in the cloud
5. **Screen Capture**: Marcus doesn't prevent screenshots or recording

**Recommendation**: Use full-disk encryption (BitLocker on Windows) for physical security.

## File Security

### Upload Process

1. File received as bytes
2. SHA-256 hash computed
3. File type determined from extension
4. Stored as `{hash}.{extension}` in vault/
5. Metadata in database (original name, size, type)

### Content-Addressed Storage

**Benefits**:
- Deduplication: Same file uploaded twice = one copy
- Integrity: Filename is the content hash
- Immutability: Files never overwritten

**Tradeoffs**:
- Filenames not human-readable in vault/
- Original names stored in DB only

### Extraction Safety

**PDF Extraction** (pypdf):
- Text-only extraction
- No JavaScript execution
- No form processing
- No embedded file extraction

**Image OCR** (Tesseract):
- OCR runs in separate process
- No code execution risk
- Errors isolated

**DOCX Extraction** (python-docx):
- Text and paragraph extraction only
- No macro execution
- No embedded object processing

**Code Files**:
- Read as plain text
- Syntax highlighting: NO
- Execution: NO
- Linting: NO

## Online Mode Security

### Current State (v0.1)

Online mode is **infrastructure only** in v0.1:
- Toggle exists
- Audit logging works
- No actual online features yet

### Future Online Features (v0.2+)

When implemented, online features will:

#### Web Search
- **Domain Allowlist**: Only approved domains (e.g., wikipedia.org, official docs)
- **Query Logging**: Every search logged with timestamp
- **Result Citations**: All sources tracked
- **User Review**: Results shown before incorporation

#### LLM API Calls
- **API Key Required**: User provides own key
- **Logged Requests**: Every prompt and response logged
- **Token Tracking**: Usage monitored
- **Opt-in Only**: Never required, always optional

#### Online Research
- **Rate Limiting**: Prevent runaway API usage
- **Domain Restrictions**: No unrestricted web access
- **Citation Required**: All facts must cite sources
- **Confidence Scores**: Mark AI-generated vs. retrieved

### Online Mode Audit Trail

Example audit log entry:

```json
{
  "id": 42,
  "timestamp": "2026-01-10T14:23:45",
  "event_type": "online_query",
  "online_mode": "online",
  "query": "What is the formula for calculating voltage in Ohm's Law?",
  "domains_accessed": ["en.wikipedia.org", "hyperphysics.phy-astr.gsu.edu"],
  "results_summary": "V = I × R (Voltage = Current × Resistance)",
  "citations": [
    {
      "url": "https://en.wikipedia.org/wiki/Ohm%27s_law",
      "title": "Ohm's Law - Wikipedia",
      "snippet": "Ohm's law states that the current through a conductor..."
    }
  ],
  "user_action": "Researched Ohm's Law formula",
  "metadata": {
    "confidence": "high",
    "sources_count": 2
  }
}
```

## Permissions Model

### File System Permissions

Marcus requires:
- **Read/Write**: `marcus/` directory and subdirectories
- **Read**: Uploaded files (user-provided paths)

Marcus does NOT require:
- System-wide file access
- Registry access (Windows)
- Network access (unless online mode enabled)
- Elevated privileges / admin rights

### Network Permissions

**Offline Mode**:
- Binds to localhost:8000 only
- No outbound connections

**Online Mode** (future):
- Outbound HTTPS to allowed domains
- Still binds to localhost only
- No listening on network interfaces

## Data Privacy

### What Marcus Stores

**In Database** (`storage/marcus.db`):
- Class codes and names
- Assignment titles and descriptions
- File metadata (name, size, type, hash)
- Extracted text content
- Generated plans
- Audit logs

**In Filesystem**:
- Uploaded files in `vault/`
- Export bundles in `exports/`

### What Marcus Does NOT Store

- Passwords or credentials
- API keys (user provides at runtime)
- Personal identifiers beyond what you enter
- Usage telemetry
- Crash reports

### Data Deletion

**Delete Assignment**:
```sql
DELETE FROM assignments WHERE id = ?;
-- Cascades to artifacts, plans, extracted_texts
```

**Delete All Data**:
1. Delete `storage/marcus.db`
2. Delete `vault/*`
3. Delete `exports/*`
4. Restart Marcus (will create new empty DB)

**Secure Deletion**:
- Marcus uses standard file deletion
- For secure deletion, use OS-level tools:
  - Windows: `cipher /w:vault`
  - Or use third-party secure delete tools

## Code Security

### Dependencies

All dependencies are open-source and vetted:
- FastAPI: Web framework
- SQLAlchemy: ORM
- Pydantic: Validation
- pypdf: PDF parsing
- Pillow: Image processing
- pytesseract: OCR wrapper
- python-docx: DOCX parsing

**Vulnerability Management**:
- Dependencies pinned in requirements.txt
- Future: Dependabot alerts
- Future: Regular dependency updates

### No Remote Code Execution

Marcus does NOT:
- Execute uploaded code files
- Evaluate user input as code
- Run shell commands from user input
- Process templated code (Jinja only for exports)

### Input Validation

- All API inputs validated via Pydantic schemas
- File types checked by extension
- SQL injection prevented by SQLAlchemy ORM
- Path traversal prevented (files stored by hash)

## Sandboxing

### Process Isolation

**Current**: Marcus runs as single Python process
**Future** (v0.3+):
- OCR in separate subprocess
- File extraction in subprocess
- Timeouts on all subprocesses

### Resource Limits

**Current**: No enforced limits
**Future**:
- Max file size for uploads (e.g., 100MB)
- Timeout on extraction (e.g., 30s per file)
- Rate limiting on plan generation

## Compliance Considerations

### FERPA (Family Educational Rights and Privacy Act)

Marcus is **FERPA-friendly** because:
- All data stored locally
- No third-party access
- No cloud storage by default
- Student controls all data

**Important**: If you enable online mode and use cloud LLM APIs, you are responsible for FERPA compliance.

### GDPR (General Data Protection Regulation)

Marcus supports GDPR principles:
- **Data Minimization**: Stores only what you upload
- **Purpose Limitation**: Data used only for stated purpose
- **Right to Erasure**: Delete DB and files
- **Data Portability**: Export as ZIP bundles

### Academic Integrity

Marcus is a **planning and organization tool**, not a cheating tool.

**Acceptable Use**:
- Organizing coursework
- Extracting text from your own materials
- Generating study plans
- Structuring your work

**Prohibited Use**:
- Submitting Marcus-generated content as your own work
- Using for exams without instructor permission
- Violating course collaboration policies

**Your Responsibility**:
- Follow your institution's academic integrity policies
- Cite AI assistance if required by your institution
- Use Marcus as a tool, not a replacement for learning

## Incident Response

### If You Suspect a Security Issue

1. **Stop Using Online Mode** (if enabled)
2. **Review Audit Logs** in Audit Log tab
3. **Check Database**: Open `storage/marcus.db` with SQLite viewer
4. **Report Issue**: File issue on GitHub (if open-sourced)

### Data Breach Response

If your computer is compromised:
1. **Change Passwords**: Any accounts mentioned in files
2. **Review Vault**: Check `vault/` for sensitive uploads
3. **Delete if Needed**: Remove `marcus/` directory
4. **Notify**: If course materials compromised, notify instructor

## Recommendations

### For Maximum Security

1. **Use Full-Disk Encryption**: BitLocker (Windows), FileVault (Mac)
2. **Keep Offline Mode**: Only enable online when absolutely needed
3. **Regular Backups**: But encrypt backups if stored in cloud
4. **Review Audit Logs**: Periodically check for unexpected activity
5. **Update Dependencies**: When new versions released

### For Shared Computers

**Do NOT use Marcus on shared/public computers** unless:
- You have full-disk encryption
- You log out after each session
- You trust all users with physical access

**Better**: Use Marcus only on your personal device.

### For Sensitive Coursework

If working with sensitive data (research, proprietary info):
- Keep offline mode ON
- Encrypt exports before cloud upload
- Use strong file system permissions
- Consider air-gapped machine

## Future Security Enhancements

### v0.2
- File type allowlist
- Max file size limits
- Extraction timeouts

### v0.3
- Export encryption (password-protected ZIPs)
- API key management for LLMs
- Domain allowlist configuration UI

### v0.4
- Multi-profile support (separate DBs per course)
- Automatic backup encryption
- Audit log export

### v0.5
- End-to-end encryption for exports
- Digital signatures on plans
- Tamper detection for database

---

**Remember**: Marcus is as secure as your computer. Use good security hygiene:
- Keep OS updated
- Use antivirus
- Don't click suspicious links
- Encrypt your disk
- Use strong passwords
