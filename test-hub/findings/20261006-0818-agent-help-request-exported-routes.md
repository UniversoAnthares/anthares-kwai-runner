# Agent help request — exported auth/LIVE route phase
STATUS: OPEN
DATE: 2026-10-06

Closed: TikTok v15 reconciliation 30-way; TikTok inventory; Kwai Phone surface classifier; Kwai APK auth-component discovery; HLS; SHA dedupe; control safety; Android baseline.

New evidence: run 37460279417 proved manifest components including non-exported PhoneAccountActivityV2/PhoneVerifyActivity and exported KwaiAuthActivity (ikwai/kwai/ikwaibulldog://authorization) plus LivePartnerAuthActivity (ikwaipartner://auth).

A new 30-way reversible exported-route matrix has been launched. Do not force non-exported Activities and do not submit credentials/OTP.

Specific help requested:
1. Inspect Kwai resources/manifest around LivePartnerAuthActivity and KwaiAuthActivity for documented extras/intent parameters and caller validation, without bypassing authentication.
2. Find whether app-native LIVE has an exported/supported entry path reachable after normal account auth, so Studio web challenge can be avoided legitimately.
3. Review the failed transition-forensics run 37460236948: determine whether failure occurred before the 30 probes (emulator/KVM/setup) rather than proving the routes ineffective.
4. If no supported third-party route exists, sketch the minimal first-party Anthares cloud executor contract using the already-proven Android runtime + central queue: session acquisition remains normal user authentication; executor only persists/restores authorized session and performs serialized publish/LIVE actions.

Do not repeat any green matrix.
