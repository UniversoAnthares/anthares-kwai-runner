# CircleCI quota architecture — 2026-10-10

Status: PROVEN/PARTIAL

- CircleCI is receiving commits from `UniversoAnthares/anthares-kwai-runner`.
- `provider_smoke` succeeds.
- `kwai_install_smoke` failed on commit `63759d67df920d0cd87b4323ed76c77a576f21cb`; exact internal CircleCI log is not exposed through the current ChatGPT CircleCI connector surface.
- The default CircleCI workflow was reduced from the full Android matrix to a cheap validation path; the exhaustive matrix remains available behind `full_android_matrix=true`.
- A separate CircleCI config was added on branch `qa/circleci-wordpress` of private mirror `UniversoAnthares/anthares-wordpress` to test CircleCI as a third QA executor for PHP, JS and static checks without consuming GitLab shared-runner quota.

Do not treat a pending status as success. Do not re-enable the full Android matrix on every push.
