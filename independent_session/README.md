# Independent Kwai session engine (new architecture)

The legacy Android login scripts are **not** invoked by this engine.

Components:
1. `engine.py`: AES-256-GCM authenticated encryption with scrypt key derivation, identity binding and integrity verification. Session payload remains opaque and private.
2. `test_engine.py`: synthetic cryptographic QA (no account claims).
3. An **independent Android identity acquisition adapter** must be built and tested before accepting a real session; neither a login chooser nor an emulator launch proves authentication.
4. An **independent remote durable backend** and two isolated restore jobs must be wired after authenticated acquisition. GitHub Actions artifacts alone are not an appropriate permanent secret store.

Security invariants: never publish session bytes or plaintext in Actions artifacts/logs; never bypass OTP/CAPTCHA; never claim login from an anonymous emulator. No local PC, paid service, or billing.

Status: cryptographic foundation only. Real authenticated capture and two independent restores remain unverified.
