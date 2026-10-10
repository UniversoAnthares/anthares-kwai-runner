# Anthares Native — replacement architecture

Independent evidence-gated control plane. The previous 30-probe matrices and UI test success are **not** proof of login or publication.

## Components
1. **Evidence collector:** consumes explicitly validated identity, encrypted-session restoration, and public video evidence. No secrets in evidence JSON.
2. **State controller:** deterministic transitions; cannot mark authentication, persistence or publication complete without their specific proofs.
3. **Executor adapter (next):** implement real Android or browser executor behind this contract; fail closed on missing evidence.
4. **Publisher adapter (next):** queue lease, dedupe, publish, verify public URL.
5. **Private session vault (next):** authenticated, encrypted save and restore with identity verification after restore.

## Migration
This implementation is isolated. The existing production publisher remains unchanged until the new adapters prove a real session and public video. Never disable credential-rotation security checks to make tests pass.

## Evidence example
{"identity_verified":false,"encrypted_session_saved":false,"restored_identity_verified":false,"video_url":"","publication_verified":false}

Run: python3 -m anthares_native.controller --evidence evidence.json
