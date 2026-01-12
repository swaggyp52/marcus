# Marcus v0.36 - Auth Wall COMPLETE ✅

**Date:** 2026-01-10
**Status:** Operational
**Focus:** Password authentication + session management + auto-lock

---

## What Was Built

### 1. Authentication Service

**File:** [marcus_app/services/auth_service.py](marcus_app/services/auth_service.py)

**Features:**
- ✅ Argon2id password hashing (OWASP recommended)
- ✅ Secure session tokens (32-byte URL-safe)
- ✅ Session expiry tracking (15-minute idle timeout)
- ✅ Password verification with automatic rehashing
- ✅ First-time setup support
- ✅ Password change functionality

**Key Methods:**
```python
setup_password(password, db)          # First-time setup
verify_password(password, db)         # Login verification
create_session(user_id)               # Create session token
validate_session(token)               # Check session validity + update activity
invalidate_session(token)             # Logout/lock
change_password(old, new, db)         # Change password
```

---

### 2. API Endpoints

**Authentication Endpoints (Public):**
```
GET  /api/auth/status          # Check if authenticated
POST /api/auth/setup           # First-time password setup
POST /api/auth/login           # Login with password
POST /api/auth/logout          # Logout and clear session
POST /api/auth/lock            # Lock session (same as logout)
POST /api/auth/change-password # Change password (requires old password)
```

**Protected Endpoints:**
- ✅ All `/api/*` endpoints now require authentication
- ✅ Exceptions: `/api/auth/*` and `/api/health` (if added)
- ✅ Returns `401 Unauthorized` if not authenticated

---

### 3. Login Page

**File:** [marcus_app/frontend/login.html](marcus_app/frontend/login.html)

**Features:**
- ✅ Clean, professional UI
- ✅ First-time setup flow (create password)
- ✅ Login flow (enter password)
- ✅ Error/success messages
- ✅ Enter key support
- ✅ Auto-redirect if already logged in
- ✅ Security badge (shows encrypted storage status)

**Screenshots:**
- Setup mode: Password + Confirm Password fields
- Login mode: Single password field
- Both modes: Clear error messages, gradient design

---

### 4. Session Management

**Cookie Details:**
- Name: `marcus_session`
- HttpOnly: `true` (prevents JavaScript access)
- SameSite: `Strict` (CSRF protection)
- Secure: `false` (set to `true` in production with HTTPS)

**Session Timeout:**
- Idle timeout: **15 minutes**
- Auto-extends on activity
- Automatically clears expired sessions

---

### 5. Auto-Lock Implementation

**How it works:**
1. Every API call validates session
2. Session validation checks idle time
3. If idle > 15 minutes → session invalidated
4. Next API call returns `401`
5. Frontend redirects to login

**Manual Lock:**
- 🔒 Lock button in UI (top-right)
- Click → Confirms → Invalidates session → Redirects to `/login`

---

### 6. Route Protection

**Frontend Protection:**
- Custom `AuthStaticFiles` class wraps static file serving
- Checks session cookie before serving any page
- Redirects unauthenticated users to `/login`
- Allows `login.html` without auth

**API Protection:**
- `get_current_session()` dependency on protected routes
- Raises `HTTPException(401)` if not authenticated
- All routes except auth endpoints are protected

---

## Security Features

| Feature | Status | Details |
|---------|--------|---------|
| Password hashing | ✅ | Argon2id (OWASP recommended) |
| Session tokens | ✅ | 32-byte cryptographically secure |
| HttpOnly cookies | ✅ | Prevents XSS session theft |
| SameSite cookies | ✅ | Prevents CSRF attacks |
| Auto-lock on idle | ✅ | 15-minute timeout |
| Manual lock button | ✅ | Instant session invalidation |
| Protected routes | ✅ | All UI + API require auth |
| First-time setup | ✅ | Guided password creation |

---

## Usage Workflow

### First-Time Setup

1. **Start Marcus**: `python main.py`
2. **Navigate**: http://localhost:8000 → Auto-redirects to `/login`
3. **Setup Mode**: Shows "Create Password" form
4. **Create Password**: 8+ characters, confirm password
5. **Auto-Login**: Automatically logs in after setup
6. **Redirect**: Goes to main app (`/`)

### Daily Login

1. **Start Marcus**: `python main.py`
2. **Navigate**: http://localhost:8000 → Redirects to `/login` if not authenticated
3. **Enter Password**: Type password, press Enter or click "Login"
4. **Redirect**: Goes to main app (`/`)

### Locking Marcus

**Option 1: Manual Lock**
- Click **🔒 Lock** button (top-right of UI)
- Confirm prompt
- Redirects to login page

**Option 2: Auto-Lock**
- Leave Marcus idle for 15 minutes
- Next action triggers `401` error
- Redirects to login page

**Option 3: Close Browser**
- Session cookie persists (browser-session scoped)
- But idle timeout still applies

---

## Testing Checklist

### ✅ Acceptance Criteria

**Authentication:**
- [x] Cannot load `/` without logging in → Redirects to `/login`
- [x] Cannot load `/static/search.html` without session → Redirects to `/login`
- [x] `/api/search` returns `401` if not authenticated
- [x] `/api/classes` returns `401` if not authenticated

**Login Flow:**
- [x] First-time setup shows password creation form
- [x] Password must be 8+ characters
- [x] Passwords must match
- [x] Auto-login after setup
- [x] Correct password → Login succeeds
- [x] Incorrect password → Error message

**Session Management:**
- [x] Session created on successful login
- [x] Session cookie is HttpOnly
- [x] Session cookie is SameSite=Strict
- [x] Session validates on every API call

**Auto-Lock:**
- [x] Idle for 15+ minutes → Session expires
- [x] Next API call returns `401`
- [x] UI redirects to login

**Manual Lock:**
- [x] Lock button visible in UI
- [x] Lock button triggers confirmation
- [x] Lock invalidates session
- [x] Redirects to login page

---

## Configuration

### Session Timeout

**Default:** 15 minutes

**To change:**
```python
# In auth_service.py
self.session_timeout = timedelta(minutes=30)  # 30 minutes
```

### Cookie Security

**For production with HTTPS:**
```python
# In api.py, login/setup endpoints
response.set_cookie(
    key="marcus_session",
    value=token,
    httponly=True,
    samesite="strict",
    secure=True  # <- Change this to True
)
```

---

## Files Created/Modified

### Created:
- [marcus_app/services/auth_service.py](marcus_app/services/auth_service.py) - Auth logic
- [marcus_app/frontend/login.html](marcus_app/frontend/login.html) - Login UI

### Modified:
- [marcus_app/core/schemas.py](marcus_app/core/schemas.py) - Added auth schemas
- [marcus_app/backend/api.py](marcus_app/backend/api.py) - Added auth endpoints + middleware
- [marcus_app/frontend/index.html](marcus_app/frontend/index.html) - Added Lock button
- [marcus_app/frontend/app.js](marcus_app/frontend/app.js) - Added `lockSession()` function

---

## Security Model Summary

### Threat Coverage

| Threat | v0.35 (Encrypted Storage) | v0.36 (+ Auth Wall) |
|--------|---------------------------|---------------------|
| Stolen laptop | ✅ Protected | ✅ Protected |
| Boot-from-USB | ✅ Protected | ✅ Protected |
| File copying | ✅ Protected | ✅ Protected |
| Casual snooping | ⚠️ Partial | ✅ Protected |
| Roommate browsing | ❌ Vulnerable | ✅ Protected |
| Unlocked laptop | ❌ Vulnerable | ✅ Protected (auto-lock) |
| Malware (while mounted) | ⚠️ Partial | ⚠️ Partial |

**Complete Coverage Now:**
- Encrypted storage (at-rest security)
- Password authentication (access control)
- Auto-lock on idle (operational security)
- Session management (stateful access)

---

## Known Limitations

### 1. Single-User Only
- Only one password (no multi-user support yet)
- `user_id` hardcoded to `"default"`
- Future: Add user management

### 2. In-Memory Sessions
- Sessions stored in RAM (lost on server restart)
- Alternative: Use JWT tokens or Redis
- Current implementation: Simple, stateless-ready

### 3. No HTTPS Enforcement
- `secure` cookie flag is `false` (localhost doesn't use HTTPS)
- For production: Enable HTTPS + set `secure=True`

### 4. No Rate Limiting
- Login attempts not rate-limited
- Could add: Max 5 failed attempts → 5-minute lockout
- Current: Argon2id makes brute-force slow anyway

### 5. No "Remember Me"
- Session lasts only while browser is open
- Could add: Long-lived "remember me" token option

---

## Next Steps (Optional Enhancements)

### Immediate (if needed):
- [ ] Add rate limiting on login endpoint
- [ ] Add "Remember Me" checkbox (30-day session)
- [ ] Add session management UI (view active sessions)
- [ ] Add 2FA support (TOTP)

### Later (nice-to-have):
- [ ] Multi-user support
- [ ] Role-based access control (admin, user, guest)
- [ ] Password reset flow (email-based or recovery key)
- [ ] Session persistence across server restarts (Redis/database)

---

## API Documentation

### POST /api/auth/setup

**Description:** First-time password setup (only works if no password exists)

**Request:**
```json
{
  "password": "my-strong-password",
  "confirm_password": "my-strong-password"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Password set up successfully",
  "session_token": "abc123..."
}
```

**Errors:**
- `400` - Password already set up
- `400` - Passwords do not match
- `400` - Password too short (< 8 chars)

---

### POST /api/auth/login

**Description:** Login with password

**Request:**
```json
{
  "password": "my-strong-password"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Login successful",
  "session_token": "abc123..."
}
```

**Errors:**
- `400` - Password not set up
- `401` - Incorrect password

---

### POST /api/auth/lock

**Description:** Lock session (invalidate current session)

**Headers:** Requires `marcus_session` cookie

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Session locked"
}
```

---

### GET /api/auth/status

**Description:** Check authentication status

**Response (200 OK) - Authenticated:**
```json
{
  "authenticated": true,
  "user_id": "default",
  "idle_seconds": 45.2,
  "session_timeout_minutes": 15
}
```

**Response (200 OK) - Not Authenticated:**
```json
{
  "authenticated": false,
  "user_id": null,
  "idle_seconds": null,
  "session_timeout_minutes": 15
}
```

---

## Conclusion

**Marcus v0.36 Auth Wall is COMPLETE and OPERATIONAL.**

You now have:
1. ✅ Encrypted storage (VeraCrypt)
2. ✅ Password authentication (Argon2id)
3. ✅ Session management (secure cookies)
4. ✅ Auto-lock on idle (15 minutes)
5. ✅ Manual lock button
6. ✅ Protected routes (all UI + API)

**This completes the security baseline.**

Marcus is now safe to:
- Store real academic materials
- Use daily as your primary academic workspace
- Expand with Study Packs, Topic Graphs, etc.

**Next recommended step:** Search quality upgrades (tokenization, FTS5, BM25) or Study Packs development.

---

**Version:** v0.36
**Security Status:** Production-Ready (for local use)
**Last Updated:** 2026-01-10
