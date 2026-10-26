# SEC-01 / item fixo 06 — read-only Bitwarden Admin UI observation — 2026-10-26

**State: PARTIAL**. This append-only finding extends the SEC-01 Bitwarden inventory evidence without claiming IAM completion. No secret values, tokens, cookies, or authentication exports were accessed.

## New verified evidence (dedicated Browser Hub profile)

- Desktop Chrome window handle `26738726`, process PID `29224`, Session 1, with profile `D:\AntharsWork\browser-profiles\AntharesBitwardenAdmin`, was visible and operating on `Contas de máquina | Bitwarden Gerenciador de Segredos`.
- Browser Hub `health` reports the dedicated profile present and running, with `port=0` and `cdp=false`. Therefore CDP was **intentionally not exposed** for the administrative vault.
- User confirmed logging into this dedicated profile. Microsoft UI Automation exposed the actual authenticated Secrets Manager page, showing 3 projects, 8 secrets, and 3 machine accounts.
- Opening the machine account `anthares-ai` in the Bitwarden UI showed one assigned project, `Anthares AI`, with permission **Pode ler e gravar** (read/write). This is evidence of configured scope, not a write-operation test.
- The account's `Tokens de acesso 1` panel showed one token **label** `anthares-omniroute-local`, status **Active**, expiration **Nunca**. This metadata does not establish that the GitHub `BWS_ACCESS_TOKEN` is derived from this account. A token marked never expiring is still revocable.
- Prior panel evidence identifies `anthares-automation` and `anthares-core`, but their detailed permissions and token metadata were **not** read in the present checkpoint. Prior SDK test `40235027169` confirmed scoped Threads secret/project metadata, not issuer identity.

## Limits and blockers

- Governance `REGRAS-OBRIGATORIAS.md`, `INDICE.md`, `PROMPT-MESTRE.md`, and `manifest.json` were rechecked on `UniversoAnthares/anthares-governance@main`, version `2e28d54043d6bad1`. Windows local manifest differs at `f6fc9ca59a96e451` (index hash), unchanged intentionally.
- A preflight command on the previous turn returned success for `SEC01-AUTH-VERIFY-20261026-R2`. On this continuation, attempts to use the Windows-control tool were blocked by the tool's security settings; **do not bypass this via another route**. Consequently, no UI read or IAM change after the block is claimed.
- The Hub profile is functional and authenticated per the user and UI metadata; **directory ACL hardening remains unverified**. Do not copy the personal Chrome's cookies into the dedicated profile.
- Further evidence needed for full closure: `anthares-automation` and `anthares-core` assigned projects, levels of access and token labels/statuses; authoritative issuer/source of GitHub `BWS_ACCESS_TOKEN`; secure profile ACL check; independent positive and negative access proofs where authorized. No need to create additional machine accounts or upgrade merely to inspect.

**No permission, token, credential, queue, deployment, plan, or purchase changed.** Preserve existing authenticated browser sessions.

Related records: `test-hub/findings/20261025-sec01-bitwarden-free-quota-browserhub-profile-evidence.md`, draft PR #1399.
