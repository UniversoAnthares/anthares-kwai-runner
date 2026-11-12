package org.universoanthares.kwaishareproof;

import android.app.Activity;
import android.os.Bundle;
import android.content.Intent;
import android.content.ClipData;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Receives Kwai's own ACTION_SEND URL without touching either clipboard. */
public final class ShareActivity extends Activity {
    private static final Pattern URL = Pattern.compile(
        "https://(?:k\\.kwai\\.com/p/[A-Za-z0-9_-]+|www\\.kwai\\.com/@[A-Za-z0-9_.-]+/(?:photo|video)/[0-9]+)");
    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        String shared = "";
        Intent intent = getIntent();
        if (intent != null && Intent.ACTION_SEND.equals(intent.getAction())) {
            CharSequence value = intent.getCharSequenceExtra(Intent.EXTRA_TEXT);
            if (value != null) shared = value.toString();
            ClipData data = intent.getClipData();
            if (data != null) {
                for (int i=0; i<data.getItemCount(); i++) {
                    CharSequence txt = data.getItemAt(i).coerceToText(this);
                    if (txt != null) shared += "\n" + txt.toString();
                }
            }
        }
        Matcher match = URL.matcher(shared);
        String result = match.find() ? match.group(0) : "NO_PUBLIC_KWAI_URL";
        File target = new File(getFilesDir(), "last_share.txt");
        try (FileOutputStream out = new FileOutputStream(target, false)) {
            out.write((System.currentTimeMillis() + "\n" + result + "\n").getBytes(StandardCharsets.UTF_8));
        } catch (IOException e) {
            // Fail closed: the receiver never sends data to another process.
        }
        finish();
    }
}
