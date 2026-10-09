# Kwai Codespaces: closed account menu is opened safely before UI inspection
STATUS: PROVEN
AREA: kwai-codespaces-browser-identity
DATE: 2026-10-09
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37947690214
JOB: 113878132215
SECURITY_QA: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37947544588
COMMIT: b181fd90e0a0a4b5387fb8ce2027ce1fcec54b2a
SUPERSEDES: test-hub/findings/20261009-lease-kwai-codespaces-auto-open-menu-1791557469.md
LEASE_CLOSED: test-hub/findings/20261009-lease-kwai-codespaces-auto-open-menu-1791557469.md

## Causal defect
User's private Codespace guard on 2026-10-09 reported chrome_connected=true, profile_url_matches=true, authenticated_ui_detected=false, account_menu_logout_visible=false. Screenshot of the SAME logged-in remote Chrome earlier showed account menu with 'Lucas Rosalem' and 'Log out'. Inspector had only read existing DOM without opening the dropdown, so this was a false negative for signed-in UI detection, NOT proof of login failure.

## Fix
.devcontainer/kwai-identity-guard.py now opens only the top-right account avatar in a disposable inspector tab, waits briefly, then reads visible logout and exact account-menu link evidence; never clicks logout, never touches an existing user's tab, never exports cookies/tokens. Fails closed if avatar cannot be found. Exact @universo.anthares ownership is still unverified unless independent exact menu profile link evidence exists; display name is insufficient. Browser profile remains untouched.

## Decisive evidence
37947690214 / 113878132215: job success with KWAI_CODESPACE_ACCOUNT_MENU_DOM={"display_name_only_detected":true,"wrong_account_rejected":true,"exact_menu_profile_accepted":true,"signed_out_rejected":true,"closed_menu_auto_opened":true,"no_avatar_fails_closed":true,"credentials_used":false,"synthetic_only":true}
37947544588: 13/13 offline security/unit tests passed.
Initial 37947459160 failed due test harness Python string escaping before running DOM assertions; corrected by changing only synthetic fixture quoting, new run 37947690214 passed. Not a Kwai product failure.

## Scope and limitation
PROVEN only for synthetic DOM on hosted Chrome, NOT verified in user's live Codespace. GitHub connector cannot execute in the user's private Codespace or read private port. To apply the fix to the existing live Codespace without restarting Chrome or losing login, user can run once in the existing Codespaces terminal:
git pull --ff-only && bash .devcontainer/kwai-refresh-guard.sh
Then click 'Verificar identidade da conta' at private 8765 root. Expect authenticated_ui_detected=true if top-right avatar/menu matches DOM; identity_verified may remain false if Kwai menu does not expose expected @handle. Do not export session until server identity verification exists.

## Next
If signed-in UI becomes true but exact handle still false, inspect owner profile navigation via the account menu in a disposable tab; never confuse Kwai account display name with TikTok handle. No Android, no PC executor, no real publication.
