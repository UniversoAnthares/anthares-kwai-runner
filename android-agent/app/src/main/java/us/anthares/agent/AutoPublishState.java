package us.anthares.agent;

import android.content.Context;
import android.content.SharedPreferences;

final class AutoPublishState {
    private static final String PREFS = "anthares_auto_publish";
    private static final String K_ARMED_AT = "armed_at";
    private static final String K_CAPTION = "caption";
    private static final String K_JOB_ID = "job_id";
    private static final String K_PHASE = "phase";
    private static final long TTL_MS = 15L * 60L * 1000L;

    private AutoPublishState() {}

    static void arm(Context context, String caption, String jobId) {
        prefs(context).edit()
                .putLong(K_ARMED_AT, System.currentTimeMillis())
                .putString(K_CAPTION, caption == null ? "" : caption)
                .putString(K_JOB_ID, jobId == null ? "" : jobId)
                .putString(K_PHASE, "ARMED")
                .apply();
    }

    static boolean isArmed(Context context) {
        long at = prefs(context).getLong(K_ARMED_AT, 0L);
        if (at <= 0L) return false;
        if (System.currentTimeMillis() - at > TTL_MS) {
            clear(context);
            return false;
        }
        return true;
    }

    static String caption(Context context) {
        return prefs(context).getString(K_CAPTION, "");
    }

    static String jobId(Context context) {
        return prefs(context).getString(K_JOB_ID, "");
    }

    static String phase(Context context) {
        return prefs(context).getString(K_PHASE, "");
    }

    static void phase(Context context, String phase) {
        prefs(context).edit().putString(K_PHASE, phase == null ? "" : phase).apply();
    }

    static void clear(Context context) {
        prefs(context).edit().clear().apply();
    }

    private static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }
}
