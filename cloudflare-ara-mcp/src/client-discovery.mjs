// Public protocol guidance only. The owner's inventory stays in private governance.
export const DISCOVERY_REVISION = '2026-10-26.1';
export const CLIENT_INSTRUCTIONS = [
  'Anthares Remote is an authenticated remote execution connector, distinct from Chrome tab-context reading.',
  'Call capabilities before concluding that browser, local files, Codex, Kilo, Cline, Claude Code or VS Code are unavailable.',
  'Use only tools granted to this connection; remote_exec requires ara.write. Browser context alone does not determine this connector\'s capabilities.',
  'Read the owner governance through authorized file tools before work. Discover actual launchers and browser profiles before operating them.',
  'A configured route is not a verified login. Do not assume this connection grants access to other chats or every account.',
  'Keep automation hidden, never use personal input or clipboard, and close only owned temporary resources in finally.',
  'Respect explicit security denials, administrator profile restrictions and user-only consent; do not switch channels to evade them.'
].join(' ');

export function clientDiscovery(scopes = []) {
  const granted = [...new Set(scopes)];
  const writable = granted.includes('ara.write');
  return {
    revision: DISCOVERY_REVISION,
    granted_scopes: granted,
    remote_execution: writable ? 'granted' : 'not_granted',
    instructions: CLIENT_INSTRUCTIONS,
    discovery_tool: 'capabilities',
    next_step: writable ? 'Use remote_exec for the read-only discovery command below, then follow the installed contracts.' : 'Use file_list/file_read within ara.read. Remote execution requires an owner-approved ara.write grant.',
    ...(writable ? { discovery_command: String.raw`$root='D:\AntharsWork'; Get-Content -LiteralPath "$root\governance\REGRAS-OBRIGATORIAS.md"; Get-Content -LiteralPath "$root\governance\INDICE.md"; & "$root\browser-profiles\AntharesBrowserHub.ps1" -Action status; & 'C:\Users\Lucas\AppData\Local\Programs\Python\Python311\python.exe' "$root\codex-bridge\bridge.py" info; Get-Command code,kilo,claude,codex -ErrorAction SilentlyContinue | Select-Object Name,Source; Get-Item -LiteralPath "$root\omniroute-host\Invoke-AntharesAgent.ps1","$root\anthares-browser-local\control.js" -ErrorAction SilentlyContinue | Select-Object FullName` } : {}),
    verification: {
      browsers: 'Probe the installed Browser Hub; extension access and CDP are separate capabilities. Use explicit owned targets and preserve existing tabs. A port of 0 is not permission to enable debugging.',
      agents: 'Inspect installed bridge/launcher contracts and status. Do not start another agent just to prove installation or assume another chat shares its tools.',
      authentication: 'Check the target account separately, without printing credentials, cookies or session payloads.',
      unavailable_tool: 'A missing direct tool may have an authorized installed route through remote_exec. Verify that route before requesting manual operation; never use it to evade a security denial.'
    }
  };
}
