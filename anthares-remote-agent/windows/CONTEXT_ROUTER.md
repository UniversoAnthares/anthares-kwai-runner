# ARA registered execution contexts

The canonical SYSTEM ARA agent remains the queue consumer. This component routes registered provider operations to the existing interactive owner identity without copying credentials. The runtime config stays private; no passwords or provider tokens belong in the source, request IDs or metadata audit.

The validated transport implementation is context_router.py (existing Python/pywin32). Invoke-AntharesContext.ps1 is a compatibility adapter. The limited interactive task Anthares Context Router User runs pythonw.exe -B context_router.py --serve. Each server handles one request, acknowledges the framed reply, closes its named-pipe handles and exits. The next client starts the same task automatically. The task remains Interactive/Limited, requires owner logon, uses IgnoreNew, and does not consume ARA queues.

## Requests

Use explicit service, literal JSON arguments encoded as base64, a bounded timeout and a stable 32-lowercase-hex request ID. The Python CLI accepts --service, --arguments-b64, --cwd, --timeout and --id; the PowerShell adapter retains Service, ArgumentsJson, WorkingDirectory, TimeoutSeconds and RequestId. Do not put credentials in arguments.

Windows currently exposes identity in the caller context. Cloudflare uses the pinned existing Node/Wrangler executable and verifies the configured account before execution; whoami returns only a verified-account marker. GitHub verifies the configured existing login, and the route is re-enabled by the owner's explicit instruction. Credential-printing auth/diagnostic/extension operations remain denied. Hostinger exposes only identity and listener-status through the owner's existing SSH config, with BatchMode and StrictHostKeyChecking enabled. listener-status returns existence, file type, nonempty, ownership and access-mode metadata; it never reads the credential value. Arbitrary remote commands and read-token are not registered.

The named pipe is local-only with an explicit SYSTEM/owner DACL. The client verifies the server process SID before sending a request. Overlapped framed message I/O has deadlines. A per-request owned Windows Job Object closes descendant processes on termination. Metadata audit records request ID, time, service, status, process, identity SID and current verified governance version; no command arguments or provider output. Previously started IDs remain fenced across task restarts.

Connection retries happen only before submitting a request. A timeout or missing result after submission requires reconciliation of the same ID, never a new duplicate request. No identity switching on 401/403, no automatic provider fallback on quota, and no bypass of a tool security denial. Existing publisher authority and queue fencing remain separate.

## Operational acceptance

ARA job f11e3bc3c7265b66e7f767b0744f7afb completed SYSTEM -> registered owner -> Hostinger SSH listener-status, without reading the credential. GitHub identity, Cloudflare identity, credential-command denial, unregistered Hostinger operation denial, persisted duplicate rejection and four synthetic redaction cases passed. Repeated clients each started and completed a distinct short-lived server; the task returned exit 0 and Ready.

Do not ask an owner to open Work or copy a secret merely because browser tab context is read-only. Discover ARA capabilities and these registered routes first. An explicit denied deployment or branch write still needs formal review; routing does not authorize retrying it elsewhere.

Source PR #1887 remains a review branch. Installed runtime acceptance and default-branch integration are distinct. This does not create universal access to other services or make owner logoff credentials available. Eight stale non-repository governance registrations remain outside this change.
