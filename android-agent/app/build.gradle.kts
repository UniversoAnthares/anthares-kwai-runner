plugins { id("com.android.application") }
android {
 namespace = "us.anthares.agent"
 compileSdk = 35
 defaultConfig { applicationId = "us.anthares.agent.redmi"; minSdk = 26; targetSdk = 31; versionCode = 2; versionName = "0.1.1-redmi" }
}

dependencies { implementation("androidx.core:core:1.15.0") }
