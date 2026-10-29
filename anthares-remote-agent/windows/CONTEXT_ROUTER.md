# ARA execution-context router

This optional Windows broker preserves the canonical SYSTEM ARA agent. It is not another queue consumer. Provider CLI calls are sent over a local named pipe to the existing registered interactive owner identity, without copying credentials or inheriting SYSTEM provider-token environment variables.

Install the reviewed script as a runtime component in a dedicated protected directory. Keep machine-specific config private. Configure pipe, user_sid, node, wrangler, python, gh, cloudflare_account, github_account, github_enabled, governance_root and governance. File ACLs must grant SYSTEM/administrators control and the owner read/execute; only the metadata audit file is owner-writable. Pipe ACL admits only SYSTEM and the registered owner SID. Run Serve through a hidden, limited, interactive scheduled task at owner logon. Never store a password or enable a second ARA agent for this purpose.

Use Invoke mode with explicit Service, literal ArgumentsJson, WorkingDirectory, bounded TimeoutSeconds and the existing job's 32-hex RequestId. Service Windows currently exposes only identity in the caller context. Cloudflare uses the owner's pinned existing Node/Wrangler installation and verifies the configured account using whoami before every command. GitHub uses its existing CLI and verifies the configured login; github_enabled must remain false until credential recovery and revalidation are complete. No Vercel or arbitrary-service route is implicitly installed.

Login/logout, credential printing and diagnostic flags are rejected. No automatic reroute on 401/403, security denial, quota or timeout. Result uncertainty requires reconciliation; do not resend a new ID. The metadata-only audit ledger rejects previously started IDs, including after restart. No raw command or provider output is persisted by this broker. OAuth tools can maintain their own existing profile files.

Stop the owned broker using Mode Stop, then confirm task completion and absence of its server/child processes before maintenance. Do not rely on stopping the Python wrapper task alone: that left an orphan server during initial acceptance and was corrected with the explicit stop protocol. Restart only this owned task. Do not stop canonical ARA processes, publisher tasks or user applications.

Limits: owner must be logged on. This route is explicit, not transparent interception of existing remote_exec commands. Other providers require individual registration, identity proof and authorization. An in-process configuration change is not picked up until a graceful restart.

Acceptance is recorded in the 20261029 ARA context-router finding. No production mutation is needed to test identity routing.
