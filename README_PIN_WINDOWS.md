# Marcus (Windows) — Install + Pin

## Prereq
- Mount VeraCrypt volume so `M:\Marcus\` exists before starting Marcus.
- Marcus is offline-first and stores data on the encrypted drive.

## Install (copy EXE into a stable location)
Open PowerShell:

```powershell
$dest = "$env:LOCALAPPDATA\Marcus"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item "C:\Users\conno\marcus\dist\Marcus.exe" $dest -Force
```

## Create Desktop Shortcut
```powershell
$exe = "$env:LOCALAPPDATA\Marcus\Marcus.exe"
$shortcut = "$env:USERPROFILE\Desktop\Marcus.lnk"
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut($shortcut)
$s.TargetPath = $exe
$s.WorkingDirectory = Split-Path $exe
$s.Description = "Marcus"
$s.Save()
```

## Pin to taskbar

- Right-click Marcus on your Desktop
- Click **Pin to taskbar**

## Smoke test (recommended)
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke_v050.ps1
```

## If the window doesn't appear

- Check VeraCrypt is mounted
- Verify backend is reachable:
  - http://127.0.0.1:8000/health
  - http://127.0.0.1:8000/app.js
- Rebuild the EXE if assets aren't bundled.
