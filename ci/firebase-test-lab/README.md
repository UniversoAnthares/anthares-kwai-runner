# Firebase Test Lab tertiary Android lane

This is the third Android lane after CircleCI and Bitrise. It is bounded to automated device validation and is not the manual-auth/noVNC lane.

Required environment: `FIREBASE_PROJECT_ID`, `FIREBASE_TEST_MODEL`, `FIREBASE_TEST_VERSION`, plus an authenticated `gcloud` context outside the repository.

The script downloads and verifies the public Kwai vault, passes the base APK as the app and the validated splits as additional APKs, then runs a bounded Robo matrix.

No Firebase credential, authenticated session, or billing configuration belongs in the repository. Use only the Spark no-cost quota; quota exhaustion marks this provider unavailable and must not enable billing.
