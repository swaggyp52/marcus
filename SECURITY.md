# Marcus Security Setup

## Current Security Status: ENCRYPTED STORAGE ENABLED ✓

Your Marcus data is now protected by VeraCrypt encryption.

---

## What's Protected

**Encrypted (on M: drive):**
- `M:\Marcus\storage\marcus.db` - All your classes, assignments, metadata
- `M:\Marcus\vault\` - All uploaded files, textbooks, PDFs, documents

**Not Encrypted (safe to leave unencrypted):**
- `C:\Users\conno\marcus\` - Marcus application code only
- Configuration files
- Scripts and frontend UI

---

## Threat Model

| Threat | Protected? | How |
|--------|-----------|-----|
| Stolen laptop | ✅ Yes | Encrypted drive is unreadable without password |
| Boot-from-USB attack | ✅ Yes | VeraCrypt container appears as random noise |
| File copying attack | ✅ Yes | Cannot copy readable files without mounting |
| Casual snooping | ✅ Yes | Must mount drive and know password |
| Malware (while mounted) | ⚠️ Partial | Data readable while drive is mounted |

---

## Daily Usage

### Starting Marcus (4 steps)

1. **Open VeraCrypt**
2. **Mount the encrypted container:**
   - Select drive letter: **M:**
   - Click "Select File..."
   - Choose: `C:\Users\conno\MarcusSecure\marcus_vault.hc`
   - Click "Mount"
   - Enter your password
3. **Verify M:\Marcus exists** in Windows Explorer
4. **Start Marcus:** `python main.py`

### Stopping Marcus (2 steps)

1. **Stop the server** (Ctrl+C in terminal)
2. **Dismount the encrypted drive:**
   - Open VeraCrypt
   - Select the M: drive
   - Click "Dismount"

⚠️ **IMPORTANT:** Always dismount when you're done. If your laptop is stolen while the drive is mounted, the encryption does nothing.

---

## What Happens If...

### "I forgot to mount the drive and tried to start Marcus"

Marcus will refuse to start and show:

```
======================================================================
[SECURITY] Marcus encrypted storage NOT MOUNTED
======================================================================
Expected encrypted drive at: M:\Marcus

To start Marcus:
1. Open VeraCrypt
2. Mount your marcus_vault.hc encrypted container
3. Verify M:\Marcus\ exists
4. Restart Marcus
======================================================================
```

This is intentional. Marcus will **never** create unencrypted data by accident.

### "I forgot my VeraCrypt password"

Your data is **permanently lost**. There is no recovery mechanism. This is a feature, not a bug.

**Recommendation:** Store your password in a password manager or write it down and keep it in a safe place.

### "Someone steals my laptop while the drive is mounted"

They can read your Marcus data. Always dismount when:
- Leaving your laptop unattended
- Traveling
- Not actively using Marcus

### "My laptop crashes while Marcus is running"

Your data is safe. VeraCrypt automatically protects the container. When you remount, everything will be there.

---

## Configuration Files

### marcus.env

Location: `C:\Users\conno\marcus\marcus.env`

```env
MARCUS_DATA_ROOT=M:\Marcus
MARCUS_STORAGE_PATH=M:\Marcus\storage
MARCUS_VAULT_PATH=M:\Marcus\vault
MARCUS_DB_PATH=M:\Marcus\storage\marcus.db
```

**Do not modify** unless you're moving the encrypted container.

---

## Backup Strategy

### What to back up

1. **The encrypted container:** `C:\Users\conno\MarcusSecure\marcus_vault.hc`
   - This file contains ALL your Marcus data
   - Back up regularly (weekly recommended)
   - Store backups offsite (cloud storage is safe - it's encrypted)

2. **Your password** (securely)
   - Password manager
   - Printed copy in a safe
   - **Do NOT** store it in a plaintext file

3. **VeraCrypt recovery key** (if you created one during setup)

### What NOT to back up

- The Marcus application code (it's on GitHub)
- Configuration files (you can recreate them)

### Recommended backup schedule

- **Daily:** Automatic cloud sync of `marcus_vault.hc` (optional)
- **Weekly:** Manual backup to external drive
- **Monthly:** Verify backup integrity (try mounting it)

---

## Advanced: Moving the Encrypted Container

If you need to move `marcus_vault.hc` to a different location:

1. **Dismount the drive** in VeraCrypt
2. **Move the file** to the new location
3. **Update marcus.env** if you changed the drive letter
4. **Remount** and verify Marcus works

---

## Next Security Steps (Not Yet Implemented)

The following features are planned for v0.35+:

- [ ] Login screen (password-protect the UI)
- [ ] Session auto-lock after inactivity
- [ ] Online Mode permission controls
- [ ] Audit log viewer in UI
- [ ] File type validation on upload

---

## Emergency: "I Need to Decrypt Everything"

If you want to export all your data in plaintext:

1. Mount the encrypted drive
2. Copy `M:\Marcus\` to a safe location
3. You now have unencrypted copies

⚠️ Only do this if you absolutely need to. Encrypted storage is safer.

---

## Verification Checklist

✅ VeraCrypt installed
✅ Encrypted container created (~50GB)
✅ Strong password chosen and stored safely
✅ Marcus data moved to M:\Marcus\
✅ marcus.env configured
✅ Marcus refuses to start without mounted drive
✅ Backup strategy in place

---

**Last updated:** 2026-01-10
**Marcus version:** v0.3 + Security Baseline
