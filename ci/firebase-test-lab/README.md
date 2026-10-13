# Firebase Test Lab tertiary Android lane

This lane is the third Android executor after CircleCI and Bitrise. It is bounded to automated Android device validation; it is not the manual-auth/noVNC lane.

Required environment: `FIREBASE_PROJECT_ID`, `FIREBASE_TEST_MODEL`, `FIREBASE_TEST_VERSION`, and an authenticated `gcloud` context outside the repository.

The runner downloads the public validated Kwai vault, verifies SHA-256, supplies the base APK as the app and the remaining validated split APKs as additional APKs, then runs a bounded Robo matrix.

No Firebase credentials, session material, or payment configuration belong in this repository. Use the Spark no-cost quota only; if that quota is exhausted, mark this provider unhealthy and fail closed rather than enable billing.
