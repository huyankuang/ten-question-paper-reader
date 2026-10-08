# sync-skills.ps1
# 把主版本（.agents/skills/ten-question-paper-reader）同步到各平台目录：
#   - .claude/skills/   (Claude Code 唯一不收敛的路径)
#   - .codex/skills/    (Codex CLI 旧版 / Cursor 兼容读取)
# Gemini CLI、VS Code Copilot、APM 直接识别 .agents/skills/，无需复制。
# 用法：在仓库根目录执行  powershell -ExecutionPolicy Bypass -File tools/sync-skills.ps1

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$main = Join-Path $repo '.agents\skills\ten-question-paper-reader'
$targets = @('.claude\skills', '.codex\skills')

if (-not (Test-Path $main)) { throw "主目录不存在: $main" }

foreach ($t in $targets) {
    $dst = Join-Path $repo (Join-Path $t 'ten-question-paper-reader')
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
    if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
    Copy-Item -Recurse -Force $main $dst
    Write-Host "synced -> $dst"
}
Write-Host "完成。.agents/skills（主）、.claude/skills、.codex/skills 三处现已一致。"
