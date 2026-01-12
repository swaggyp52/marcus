# Marcus v0.42 — Online Operations Complete

## Overview

v0.42 implements the missing push and PR backend routes that were stubbed in v0.41's frontend.

---

## Push to Remote

**Endpoint:** `POST /api/projects/{project_id}/git/push`

**Request:**
```json
{
  "branch_name": "feature-branch",  // optional, defaults to current branch
  "force": false                     // optional, default false
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Successfully pushed 'feature-branch' to origin",
  "branch": "feature-branch",
  "remote": "origin"
}
```

**Response (Error - Not Online):**
```json
{
  "detail": "Online Mode not enabled. Enable Online Mode to use network operations."
}
```
HTTP 403 Forbidden

---

## Create Pull Request

**Endpoint:** `POST /api/projects/{project_id}/github/create-pr`

**Request:**
```json
{
  "title": "Fix authentication bug",
  "body": "This PR fixes the auth issue in #123",
  "base_branch": "main"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Pull request created successfully",
  "pr_url": "https://github.com/owner/repo/pull/456",
  "title": "Fix authentication bug",
  "base": "main",
  "head": "fix/auth"
}
```

**Method Priority:**
1. **gh CLI** (if installed and authenticated) - Preferred
2. **GitHub API** (with token from TokenService) - Fallback

---

## Audit Log Examples

**Push Operation:**
```json
{
  "id": 142,
  "timestamp": "2026-01-11T14:32:10Z",
  "event_type": "git_push",
  "user_action": "Pushed branch 'feature-x' to origin",
  "online_mode": "online",
  "metadata": "{\"project_id\": 1, \"branch\": \"feature-x\", \"remote\": \"origin\", \"force\": false}"
}
```

**PR Creation:**
```json
{
  "id": 143,
  "timestamp": "2026-01-11T14:35:22Z",
  "event_type": "github_pr_created",
  "user_action": "Created PR: Fix auth bug",
  "online_mode": "online",
  "metadata": "{\"project_id\": 1, \"title\": \"Fix auth bug\", \"base_branch\": \"main\", \"head_branch\": \"fix/auth\", \"pr_url\": \"https://github.com/owner/repo/pull/123\"}"
}
```

---

## Frontend Usage

**Push:**
```javascript
// In app.js performPush()
await devModeUI.pushBranch();  // Uses current branch
// or
await devModeUI.pushBranch('feature-x', false);  // Specific branch, no force
```

**PR:**
```javascript
// In app.js performCreatePR()
const title = document.getElementById('prTitle').value;
const description = document.getElementById('prDescription').value;
await devModeUI.createPR(title, description, 'main');
```

---

## Security Guarantees

1. **Online Mode Required** - Both endpoints return 403 if Online Mode disabled
2. **Confirmation Modals** - Frontend shows summary before calling API
3. **Audit Logged** - All operations logged with timestamp + metadata
4. **No Auto-Push** - User must explicitly click confirm button
5. **Token Security** - GitHub tokens encrypted with AES-256-GCM, never sent to frontend

---

**v0.42 Online Operations: COMPLETE**
