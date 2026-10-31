# Lease — layout beta vertical + PNG da Runa
STATUS: RUNNING
AREA: wordpress-home-beta-opportunities + wordpress-beta-config-ui
DATE: 2026-10-31
JOB: chatgpt-20261031-beta-vertical-coin
OWNER: GPT-6
COMMIT: 50d962c9a6fb9fee79eedb1b8ee09eacc1c5b43f
SUPERSEDES: test-hub/findings/20261031-home-beta-container-pagination-production-partial-gpt6.md
EXPIRY: 30 min after creation.

EXCLUSIVE_SCOPE: anthares-wordpress/anthares-home/templates/dashboard/leituras-beta-disponiveis.php, anthares-home/assets/css/dashboard/leituras-beta-disponiveis.css, anthares-home/assets/images/runa-simbolo.png, anthares-pix-sales/includes/65-leitura-beta.php, qa/anthares-qa-sections.json, anthares-pix-sales/qa-sections.json. Screenshots confirm 3 stacked rows required, currency image PNG as 90% card vertical useful height while keeping Runas below count. Beta configuration: shrink quantity inputs to ~one third width, widen activation and put Save immediately below.
BASELINE_PROVEN: PHP/theme sources and production hashes read. User-provided official PNG loaded from zip and resized preserving proportion and alpha. Repo main 50d962c.
SUCCESS_SIGNAL: all assets in GitHub and Hostinger; image HTTP 200 and 90% CSS height; 3 vertical slots; runa label below count; config third column expanded and reduced gap; PHP lint and QA, runtime, no financial writes or PC artifacts.
FAILURE_SIGNAL: concurrent drift, image placeholder, incorrect number layout, PHP/QA failures or financial side effects.
SAFEGUARDS: staging/backup on Hostinger, expected SHA, no checkout changes or balances, no paid resources, no Windows CI.
