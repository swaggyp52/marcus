[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)]
  [ValidateNotNullOrEmpty()]
  [string]$Name,

  [Parameter()]
  [string]$Root = (Join-Path $PSScriptRoot "..\workspaces"),

  [Parameter()]
  [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail([string]$msg) { Write-Error $msg; exit 1 }

$workspaceRoot = (Resolve-Path $Root).Path
$template = Join-Path $workspaceRoot "_template"
if (-not (Test-Path $template)) { Fail "Template not found: $template" }

$dest = Join-Path $workspaceRoot $Name
if (Test-Path $dest) {
  if (-not $Force) { Fail "Workspace already exists: $dest (use -Force to overwrite)" }
  Remove-Item $dest -Recurse -Force
}

New-Item -ItemType Directory -Force $dest | Out-Null

# Copy template contents
Copy-Item (Join-Path $template "*") $dest -Recurse -Force

Write-Host "[OK] Created workspace: $dest"
