package us.anthares.shareproof;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class ShareProofActivity extends Activity {
    private static final String TAG = "AntharesKwaiShare";
    private static final Pattern LINK = Pattern.compile("https://k\\.kwai\\.com/p/[A-Za-z0-9_-]+");
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        capture(getIntent());
        finish();
    }
    @Override protected void onNewIntent(Intent next) {
        super.onNewIntent(next);
        capture(next);
        finish();
    }
    private void capture(Intent incoming) {
        final long when = System.currentTimeMillis();
        if (incoming == null || !Intent.ACTION_SEND.equals(incoming.getAction())) {
            Log.w(TAG, "REJECT reason=not_send at_ms=" + when);
            return;
        }
        final String raw = incoming.getStringExtra(Intent.EXTRA_TEXT);
        if (raw == null || raw.length() > 2048) {
            Log.w(TAG, "REJECT reason=invalid_text at_ms=" + when);
            return;
        }
        final Matcher match = LINK.matcher(raw);
        if (!match.find()) {
            Log.w(TAG, "REJECT reason=no_public_url at_ms=" + when);
            return;
        }
        final String url = match.group();
        if (match.find() && !url.equals(match.group())) {
            Log.w(TAG, "REJECT reason=ambiguous_urls at_ms=" + when);
            return;
        }
        // Android ACTION_SEND delivers the link directly; ClipboardManager is never accessed.
        // Logcat is transported over isolated ADB; no Windows clipboard synchronization.
        Log.i(TAG, "DIRECT_SHARE_RECEIPT at_ms=" + when + " url=" + url);
    }
}
