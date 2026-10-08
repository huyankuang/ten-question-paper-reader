# sync-skills.ps1
# Sync the master skill (.agents/skills/ten-question-paper-reader) to
# platform-specific copies so discovery works across agents:
#   - .claude/skills/   (Claude Code; does NOT read .agents/)
#   - .codex/skills/    (Codex CLI legacy / Cursor compatibility)
# Gemini CLI, VS Code Copilot, and APM read .agents/skills/ directly.
# Usage (from repo root):
#   powershell -ExecutionPolicy Bypass -File tools/sync-skills.ps1

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$master = Join-Path $repo '.agents\skills\ten-question-paper-reader'
$targets = @('.claude\skills', '.codex\skills')

if (-not (Test-Path $master)) { throw "Master dir not found: $master" }

foreach ($t in $targets) {
    $dst = Join-Path $repo (Join-Path $t 'ten-question-paper-reader')
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
    if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
    Copy-Item -Recurse -Force $master $dst
    Write-Host "synced -> $dst"
}
Write-Host "Done. .agents/skills (master), .claude/skills, .codex/skills are now identical."
