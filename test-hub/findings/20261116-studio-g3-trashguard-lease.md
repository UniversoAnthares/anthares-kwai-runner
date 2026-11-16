# Lease Anthares Studio — proteção cron da lixeira, piloto privado
STATUS: RUNNING
AREA: studio-g3-trashguard-protection
DATE: 2026-11-16
START_UTC: 2026-11-16T17:30:00Z
EXPIRES_UTC: 2026-11-16T18:30:00Z
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-trashguard-20261116
SOURCE: github.com/UniversoAnthares/anthares-wordpress/pull/307 SHA 56efd039e328867171a7af0908932fca5f75b3c1
ACTIVE: production anthares-studio.php SHA d29cb73bfbab555c904aaa07506d55943a1da533a0cc26ad37268cc479dbb8e9
LEGACY: production anthares-estudio.php SHA 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf
BACKUP: Hostinger private storage studio-g1-backup-20261116-1527, restoration verified.

PERMITTED:
- Compare PR #307 to live G3, test cron filter using isolated WordPress CLI dry tests.
- If exactly scoped safety fix, copy only new-plugin PHP to production after byte-for-byte backup of prior live PHP, atomic rename, PHP syntax and REST read/write gate regression.
- Preserve active plugin state and /studio private, options ANST writes/cleanup OFF.
- Roll back exclusively own modified PHP on any failing test.
- Record resulting hash, timestamps and QA.

PROHIBITED:
- Changes to /estudio, all AEST data, public visibility or users; deletion of trash; automatic content writes.
- Merge into main or deploy ACF schema from PR #308 ahead of G4.
- Overwrite unrecognized concurrent changes; bypass auth or grant temporary admin sessions.
- Touch frontend CSS/JS, public HTML, email or price integrations.
- Open persistent windows or use personal PC storage.

SUCCESS: WordPress cron native deletion of ANST trash is blocked when disabled; 71 clone posts (31 trash) remain; 71 original posts unchanged, PHP lint PASS; same old GET 200 and POST 423; exact rollback path in private backup.
