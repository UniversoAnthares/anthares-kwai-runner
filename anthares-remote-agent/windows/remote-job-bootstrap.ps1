param()

$raw = [Console]::In.ReadToEnd()
$payload = $raw | ConvertFrom-Json -ErrorAction Stop

$handler = "C:\ProgramData\Anthares\remote-job\remote-job-handler.ps1"

$argList = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $handler,
    "-CommandId", $payload.command_id,
    "-TimeoutSeconds", $payload.timeout_seconds,
    "-RequestedBy", "anthares-vercel-mcp",
    "-ExecScope", "ara.exec"
)

if ($payload.args) {
    $argList += @("-CommandArgs", $payload.args)
}

if ($payload.cwd) {
    $argList += @("-Cwd", $payload.cwd)
}

& powershell.exe @argList 2>&1
