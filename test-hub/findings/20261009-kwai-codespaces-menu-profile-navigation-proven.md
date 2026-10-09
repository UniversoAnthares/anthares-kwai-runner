# Kwai Codespaces own-profile navigation safely proves or rejects exact UI handle
STATUS: PROVEN
AREA: kwai-codespaces-browser-identity
DATE: 2026-10-09
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37948410405
JOB: 113880591361
SECURITY_QA: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37948226078
COMMIT: cee98becf287fcfb21d32b2dc20ccc6d8431dd80
SUPERSEDES: test-hub/findings/20261009-lease-kwai-menu-profile-navigation-1791557802.md
LEASE_CLOSED: test-hub/findings/20261009-lease-kwai-menu-profile-navigation-1791557802.md

## Cause and remedy
Actual signed-in Kwai menu in private Codespaces shows display name "Lucas Rosalem" and "Log out", not literal @universo.anthares. Previous guard checked the closed dropdown and demanded an exact handle link, so it returned false even when signed-in. New guard opens top-right avatar in a disposable Chrome tab and observes visible logout. When no exact handle link exists, a SECOND disposable tab opens the account menu and clicks only the avatar in the account row above Log out within the small top-right dropdown. The resulting own-profile URL must exactly match expected @handle; a wrong handle is rejected. No click on logout, no credentials/cookies/token extraction, no mutation to existing user tabs.

## Decisive tests
37948410405 / 113880591361: success, real hosted Chromium CDP with synthetic account menu fixture:
KWAI_CODESPACE_ACCOUNT_MENU_DOM={"display_name_only_detected":true,"wrong_account_rejected":true,"exact_menu_profile_accepted":true,"signed_out_rejected":true,"closed_menu_auto_opened":true,"no_avatar_fails_closed":true,"own_profile_wrong_handle_rejected":true,"own_profile_exact_handle_verified":true,"credentials_used":false,"synthetic_only":true}
37948226078: 15/15 offline unit/security tests passed.
Earlier 37948138042 failed due synthetic Python quote escaping; 37948176911 reached fixture but account row navigation did not find leaf Log out, corrected by preferring button/menuitem leaves. Both superseded by the green 37948410405.

## Strict limitations
PROVEN on synthetic DOM hosted Chrome only, NOT user's live private Codespace. Real account still must be verified via the private 8765 guard after user updates live checkout. Authenticated UI alone is not server-side identity proof; persistence_permitted and server_identity_verified remain false, session not exported. Expected @universo.anthares may differ from the actual Kwai account handle; do not assume display name "Lucas Rosalem" maps to that handle. No Android or user's PC as executor.

## Safe live deployment
User's Codespace terminal: git pull --ff-only && bash .devcontainer/kwai-refresh-guard.sh
Then private https://supreme-spork-x4gpgwv5x7xfv55j-8765.app.github.dev/ -> Verificar identidade da conta.
No rebuild or logout. Existing browser profile is preserved.
