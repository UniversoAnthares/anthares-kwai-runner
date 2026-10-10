# Anthares Android Cloud — Phase 1

Status: source and architecture delivered; Android runtime validation is Phase 2.

## Goal
Run the official Kwai Android app in a remotely hosted, controlled environment, without using the user's PC. The orchestration code is developed in this repository. Android OS, Kwai app, and compute infrastructure remain external dependencies; a free, continuously running Android host is not established.

## Components
- **Controller**: Python standard-library CLI in `anthares_android_cloud/controller.py`; detects ADB device and confirms boot.
- **Bootstrap**: manually dispatched experimental GitHub Actions workflow `.github/workflows/anthares-android-cloud.yml`.
- **Tests**: isolated unit tests without Android or network.
- **Session layer**: not implemented. Future phase must keep authentication data in private storage, never Git history, public artifacts, or Actions logs.
- **Remote control UI / Kwai installer / publisher**: not implemented; subsequent phases.

## Security boundaries
Do not upload Kwai credentials, cookies, Android userdata, tokens, or device identity to public repositories or public workflow artifacts. No production jobs are changed. No unattended social posts until account authorization and real end-to-end validation.

## Reproduce unit tests
`python -m unittest discover -s tests -p test_controller.py -v`

## Completion criteria
Phase 1 is complete when controller, unit tests, bootstrap workflow, and architecture documentation are committed on an isolated branch. Phase 2 requires an actual successful emulator boot and verified logs.
