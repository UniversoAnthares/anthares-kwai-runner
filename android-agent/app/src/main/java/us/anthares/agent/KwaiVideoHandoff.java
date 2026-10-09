package us.anthares.agent;

import android.app.Activity;
import android.content.ClipData;
import android.content.Intent;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import android.widget.Toast;
import androidx.core.content.FileProvider;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.security.MessageDigest;
import java.util.Locale;

/**
 * Delivers a video to the official Kwai Android application through Android's
 * standard ACTION_SEND. This never talks to private Kwai endpoints and never
 * handles Kwai login credentials or browser cookies.
 */
public final class KwaiVideoHandoff {
    private static final String KWAI_PACKAGE = "com.kwai.video";
    private static final long MAX_VIDEO_BYTES = 250L * 1024L * 1024L;
    private KwaiVideoHandoff() {}

    public static void sharePicked(Activity activity, Uri uri) {
        if (uri == null || !"content".equals(uri.getScheme())) {
            show(activity, "Selecione um arquivo de vídeo válido.");
            return;
        }
        String mime = activity.getContentResolver().getType(uri);
        if (mime == null || !mime.toLowerCase(Locale.ROOT).startsWith("video/")) {
            show(activity, "O arquivo selecionado não é um vídeo.");
            return;
        }
        shareUri(activity, uri);
    }

    public static void shareFromApprovedLink(Activity activity, Uri link) {
        if (link == null || !"anthares-kwai".equals(link.getScheme())
                || !"send".equals(link.getHost())) {
            show(activity, "Link Anthares inválido.");
            return;
        }
        String rawUrl = link.getQueryParameter("url");
        String expectedHash = link.getQueryParameter("sha256");
        if (rawUrl == null || expectedHash == null
                || !expectedHash.matches("(?i)[0-9a-f]{64}")) {
            show(activity, "O link exige URL HTTPS e SHA-256.");
            return;
        }
        Uri source = Uri.parse(rawUrl);
        String host = source.getHost();
        if (!"https".equalsIgnoreCase(source.getScheme())
                || host == null || !("anthares.us".equalsIgnoreCase(host)
                || "www.anthares.us".equalsIgnoreCase(host))
                || source.getUserInfo() != null || source.getPort() != -1) {
            show(activity, "Origem do vídeo não autorizada.");
            return;
        }
        new Thread(() -> {
            File output = null;
            try {
                File dir = new File(activity.getCacheDir(), "kwai-videos");
                if (!dir.isDirectory() && !dir.mkdirs()) {
                    throw new IllegalStateException("cache unavailable");
                }
                output = new File(dir, "handoff-" + expectedHash.toLowerCase(Locale.ROOT) + ".mp4");
                if (!output.exists() || !matchesHash(output, expectedHash)) {
                    URL url = new URL(rawUrl);
                    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                    conn.setInstanceFollowRedirects(false);
                    conn.setConnectTimeout(12000);
                    conn.setReadTimeout(30000);
                    try {
                        if (conn.getResponseCode() != 200) {
                            throw new IllegalStateException("HTTP " + conn.getResponseCode());
                        }
                        long declared = conn.getContentLengthLong();
                        if (declared > MAX_VIDEO_BYTES) {
                            throw new IllegalStateException("video too large");
                        }
                        MessageDigest digest = MessageDigest.getInstance("SHA-256");
                        long total = 0;
                        byte[] buffer = new byte[65536];
                        File temp = new File(dir, output.getName() + ".part");
                        try (InputStream in = conn.getInputStream();
                             FileOutputStream out = new FileOutputStream(temp)) {
                            int n;
                            while ((n = in.read(buffer)) != -1) {
                                total += n;
                                if (total > MAX_VIDEO_BYTES) {
                                    throw new IllegalStateException("video too large");
                                }
                                digest.update(buffer, 0, n);
                                out.write(buffer, 0, n);
                            }
                        } catch (Exception e) {
                            temp.delete();
                            throw e;
                        }
                        if (total == 0 || !hex(digest.digest()).equalsIgnoreCase(expectedHash)) {
                            temp.delete();
                            throw new IllegalStateException("SHA-256 mismatch");
                        }
                        if (!temp.renameTo(output)) {
                            temp.delete();
                            throw new IllegalStateException("cache rename failed");
                        }
                    } finally {
                        conn.disconnect();
                    }
                }
                File ready = output;
                activity.runOnUiThread(() -> {
                    Uri content = FileProvider.getUriForFile(activity,
                            activity.getPackageName() + ".files", ready);
                    shareUri(activity, content);
                });
            } catch (Exception e) {
                if (output != null && !matchesHash(output, expectedHash)) output.delete();
                show(activity, "Não foi possível validar o vídeo: " + e.getClass().getSimpleName());
            }
        }, "anthares-kwai-download").start();
    }

    private static boolean matchesHash(File file, String expected) {
        if (!file.exists() || file.length() == 0 || file.length() > MAX_VIDEO_BYTES) return false;
        try (InputStream in = new java.io.FileInputStream(file)) {
            MessageDigest d = MessageDigest.getInstance("SHA-256");
            byte[] buffer = new byte[65536];
            int n;
            while ((n = in.read(buffer)) != -1) d.update(buffer, 0, n);
            return hex(d.digest()).equalsIgnoreCase(expected);
        } catch (Exception e) {
            return false;
        }
    }

    private static String hex(byte[] bytes) {
        StringBuilder s = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) s.append(String.format(Locale.ROOT, "%02x", b & 0xff));
        return s.toString();
    }

    private static void shareUri(Activity activity, Uri uri) {
        Intent send = new Intent(Intent.ACTION_SEND);
        send.setType("video/mp4");
        send.setPackage(KWAI_PACKAGE);
        send.putExtra(Intent.EXTRA_STREAM, uri);
        send.setClipData(ClipData.newUri(activity.getContentResolver(), "Anthares video", uri));
        send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        try {
            activity.startActivity(send);
        } catch (Exception e) {
            show(activity, "Instale ou atualize o aplicativo oficial do Kwai.");
        }
    }

    private static void show(Activity activity, String message) {
        new Handler(Looper.getMainLooper()).post(
                () -> Toast.makeText(activity, message, Toast.LENGTH_LONG).show());
    }
}
