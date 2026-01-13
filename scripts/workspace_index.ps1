[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)]
  [ValidateNotNullOrEmpty()]
  [string]$Name,

  [Parameter()]
  [string]$Root = (Join-Path $PSScriptRoot "..\workspaces")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail([string]$msg) { Write-Error $msg; exit 1 }

$workspaceRoot = (Resolve-Path $Root).Path
$ws = Join-Path $workspaceRoot $Name
if (-not (Test-Path $ws)) { Fail "Workspace not found: $ws" }

$sources = Join-Path $ws "sources"
$indexDir = Join-Path $ws "index"
New-Item -ItemType Directory -Force $indexDir | Out-Null

$files = @()
if (Test-Path $sources) {
  $files = @(Get-ChildItem $sources -Recurse -File -ErrorAction SilentlyContinue | Select-Object FullName, Length, LastWriteTime)
}

$outPath = Join-Path $indexDir "sources_index.json"
if ($files.Length -gt 0) {
  $files | ConvertTo-Json -Depth 6 | Set-Content -Path $outPath -Encoding UTF8
} else {
  "[]" | Set-Content -Path $outPath -Encoding UTF8
}

Write-Host "[OK] Wrote index: $outPath"
