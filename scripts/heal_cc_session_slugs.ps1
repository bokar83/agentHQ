#!/usr/bin/env pwsh
# heal_cc_session_slugs.ps1 -- fix "No conversation found" on claude --resume
#
# Problem: CC --resume from a worktree cwd looks for session jsonl under
# slug derived from process.cwd(). But CC sometimes writes the jsonl to
# the canonical project slug instead. Mismatch -> "No conversation found".
#
# Fix: scan every jsonl under canonical slug (d--Ai-Sandbox-agentsHQ).
# For each, read its recorded cwd. Compute slug from that cwd. If slug
# folder doesn't have a copy of this jsonl, place one there.
#
# Also handle junctioned paths: if cwd is D:/tmp/wt-X (legacy junction),
# also copy to slug for resolved real path D:/Ai_Sandbox/agentsHQ-worktrees/wt-X.
#
# Idempotent. Safe to re-run.
#
# Wire via Windows Task Scheduler at logon for automatic healing.
#
# 2026-05-16: created after legacy D:/tmp/wt-X session resume failure.
# Migration moved worktrees under canonical-sibling but CC --resume
# stayed broken until slug folders were manually backfilled.
#
# 2026-05-16 v2 fix: also copy the UUID subdirectory (CC stores session
# sidecar files there: tool-use buffers, compaction state, etc.). Without
# it, the first resume succeeds but the second resume fails with a state-
# integrity error because the sidecar files are missing.
#
# 2026-05-16 v2 safety: never overwrite a destination jsonl that is LARGER
# than the source (that means a live CC session is appending to it; clobber
# = data loss). Skip copy if dst.Length > src.Length.

$ErrorActionPreference = 'Continue'
$projectsDir = "$env:USERPROFILE/.claude/projects"
$canonicalSlug = 'd--Ai-Sandbox-agentsHQ'
$src = "$projectsDir/$canonicalSlug"

if (-not (Test-Path $src)) {
  Write-Output "Canonical slug folder not found: $src"
  exit 0
}

function PathToSlug([string]$path) {
  # CC slug pattern observed 2026-05-16: lowercase drive letter, preserve rest.
  #   - `D:` -> `d-`
  #   - `\` `/` -> `-`
  #   - `_` -> `-`
  # Canonical slug example: D:/Ai_Sandbox/agentsHQ -> d--Ai-Sandbox-agentsHQ
  # NTFS is case-insensitive so case-mismatches still resolve to same dir,
  # but CC may do case-sensitive string compare so preserve as-typed.
  $s = $path -replace '\\', '-' -replace '/', '-' -replace '_', '-' -replace ':', '-'
  # Lowercase only first char (the drive letter)
  if ($s.Length -gt 0) { $s = $s.Substring(0,1).ToLower() + $s.Substring(1) }
  return $s
}

$jsonls = Get-ChildItem $src -Filter "*.jsonl" -File
$healed = 0
$alreadyOk = 0
$noCwd = 0
foreach ($j in $jsonls) {
  $id = $j.BaseName
  # Read first 50 lines, find first cwd
  $cwd = $null
  $head = Get-Content $j.FullName -TotalCount 50 -ErrorAction SilentlyContinue
  foreach ($line in $head) {
    if ($line -match '"cwd":"([^"]+)"') {
      $cwd = $matches[1] -replace '\\\\', '\'
      break
    }
  }
  if (-not $cwd) { $noCwd++; continue }

  # If cwd is canonical itself, jsonl is already in the right place
  if ($cwd -ieq 'D:\Ai_Sandbox\agentsHQ' -or $cwd -ieq 'D:/Ai_Sandbox/agentsHQ') {
    $alreadyOk++
    continue
  }

  $targetSlugs = @()
  $targetSlugs += PathToSlug $cwd

  # If cwd is a D:/tmp/wt-X path, also create slug for resolved path
  if ($cwd -match '^[Dd]:[\\/]+tmp[\\/]+(wt-.+)$') {
    $wt = $matches[1]
    $resolved = "D:\Ai_Sandbox\agentsHQ-worktrees\$wt"
    $targetSlugs += PathToSlug $resolved
  }
  # Inverse: if cwd is D:/Ai_Sandbox/agentsHQ-worktrees/wt-X, also create junction slug
  if ($cwd -match '^[Dd]:[\\/]+Ai[_-]Sandbox[\\/]+agentsHQ-worktrees[\\/]+(wt-.+)$') {
    $wt = $matches[1]
    $junction = "D:\tmp\$wt"
    $targetSlugs += PathToSlug $junction
  }

  foreach ($slug in ($targetSlugs | Select-Object -Unique)) {
    $dst = "$projectsDir/$slug"
    if (-not (Test-Path $dst)) { New-Item -ItemType Directory -Path $dst -Force | Out-Null }
    $dstFile = "$dst/$($j.Name)"
    $copyJsonl = $false
    if (-not (Test-Path $dstFile)) {
      $copyJsonl = $true
    } else {
      $dstLen = (Get-Item $dstFile).Length
      # Skip if dst is LARGER (live session writing there -- don't clobber)
      # Skip if same size (already in sync)
      if ($dstLen -lt $j.Length) { $copyJsonl = $true }
    }
    if ($copyJsonl) {
      Copy-Item $j.FullName $dstFile -Force
      Write-Output "healed jsonl: id=$id cwd=$cwd slug=$slug"
      $healed++
    }

    # Also copy UUID subdirectory (session sidecar state). CC requires both
    # the jsonl + the UUID dir, else resume succeeds once then fails with
    # state-integrity error on next resume.
    $srcUuid = "$src/$id"
    $dstUuid = "$dst/$id"
    if ((Test-Path $srcUuid) -and (-not (Test-Path $dstUuid))) {
      Copy-Item $srcUuid $dstUuid -Recurse -Force -ErrorAction SilentlyContinue
      Write-Output "healed uuid-dir: id=$id slug=$slug"
    }
  }
}

Write-Output ""
Write-Output "Summary: healed=$healed already-ok=$alreadyOk no-cwd=$noCwd total=$($jsonls.Count)"
