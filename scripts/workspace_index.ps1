[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)]
  [ValidateNotNullOrEmpty()]
  [string]$Name,

  [Parameter()]
  [string]$RunId,

  [Parameter()]
  [string]$Root = (Join-Path $PSScriptRoot "..\workspaces")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Load workspace library
. (Join-Path $PSScriptRoot "_workspace_lib.ps1")

function Fail([string]$msg) { Write-Error $msg; exit 1 }

$workspaceRoot = (Resolve-Path $Root).Path
$ws = Join-Path $workspaceRoot $Name
if (-not (Test-Path $ws)) { Fail "Workspace not found: $ws" }

$sources = Join-Path $ws "sources"
$indexDir = Join-Path $ws "index"
New-Item -ItemType Directory -Force $indexDir | Out-Null

$files = @()
if (Test-Path $sources) {
  $rawFiles = @(Get-ChildItem $sources -Recurse -File -ErrorAction SilentlyContinue)
  
  foreach ($file in $rawFiles) {
    $relativePath = $file.FullName.Substring($ws.Length).TrimStart('\', '/')
    
    # Compute SHA256
    $hash = (Get-FileHash -Path $file.FullName -Algorithm SHA256).Hash
    
    $files += [PSCustomObject]@{
      relativePath = $relativePath
      fileName = $file.Name
      extension = $file.Extension
      bytes = $file.Length
      lastWriteTimeUtc = $file.LastWriteTimeUtc.ToString("o")
      sha256 = $hash
    }
  }
}

$outPath = Join-Path $indexDir "sources_index.json"
if ($files.Length -gt 0) {
  $files | ConvertTo-Json -Depth 6 | Set-Content -Path $outPath -Encoding UTF8
} else {
  "[]" | Set-Content -Path $outPath -Encoding UTF8
}

# Archive to run folder
$runMeta = Initialize-WorkspaceRun -WorkspaceRoot $ws -Command "workspace-index" -RunId $RunId
$archived = @(Add-ToRun -FilePath $outPath -RunFolder $runMeta.RunFolder)
Complete-WorkspaceRun -WorkspaceRoot $ws -RunMetadata $runMeta -ArchivedFiles $archived

Write-Host "[OK] Wrote index: $outPath"
