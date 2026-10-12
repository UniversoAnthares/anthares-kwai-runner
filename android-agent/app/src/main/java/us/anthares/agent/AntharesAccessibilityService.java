package us.anthares.agent;

import android.accessibilityservice.AccessibilityService;
import android.os.Bundle;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import java.util.ArrayDeque;
import java.util.Locale;

public class AntharesAccessibilityService extends AccessibilityService {
    private static final String KWAI = "com.kwai.video";
    private KwaiState state = KwaiState.BOOT;

    @Override public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event == null || event.getPackageName() == null
                || !KWAI.contentEquals(event.getPackageName())) return;
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) return;
        KwaiState next = detect(root);
        if (next != state) {
            state = next;
            log("STATE", state.name());
        }
        drive(root, next);
    }

    @Override public void onInterrupt() {
        log("SERVICE", "INTERRUPTED");
    }

    private void drive(AccessibilityNodeInfo root, KwaiState current) {
        try {
            String snap = snapshot(root).toLowerCase(Locale.ROOT);

            // Fail-closed automatic publication. This branch runs only for a
            // verified Anthares handoff and expires automatically after 15 min.
            if (AutoPublishState.isArmed(this)) {
                driveAutomaticPublish(root, snap);
                return;
            }

            // Existing login/bootstrap assistance remains available when no
            // publication is armed.
            if (current == KwaiState.MAIN) {
                AccessibilityNodeInfo profile = findById(root, "id_home_bottom_tab_me");
                if (profile == null) profile = findById(root, "ll_profile");
                if (profile != null && clickNodeOrParent(profile)) {
                    log("ACTION", "CLICK_PROFILE");
                    return;
                }
            }
            if (current == KwaiState.PROFILE || current == KwaiState.UNKNOWN_UI) {
                if (hasAny(snap, "log in", "login", "entrar", "sign in")) {
                    clickSemantic("log in", "login", "entrar", "sign in");
                    return;
                }
            }
            if (current == KwaiState.LOGIN_REQUIRED || current == KwaiState.UNKNOWN_UI) {
                if (hasAny(snap, "phone", "telefone", "número de telefone", "numero de telefone")) {
                    clickSemantic("phone", "telefone", "número de telefone", "numero de telefone");
                }
            }
        } catch (Exception error) {
            log("DRIVE_ERROR", error.getClass().getSimpleName());
        }
    }

    private void driveAutomaticPublish(AccessibilityNodeInfo root, String snap) {
        String phase = AutoPublishState.phase(this);

        if (hasAny(snap,
                "published successfully", "post published", "publicado com sucesso",
                "publicação concluída", "video posted", "vídeo publicado")) {
            log("AUTO_PUBLISH", "CONFIRMED job=" + AutoPublishState.jobId(this));
            AutoPublishState.clear(this);
            return;
        }

        String caption = AutoPublishState.caption(this);
        if (!caption.isEmpty() && !"CAPTION_SET".equals(phase)
                && !"PUBLISH_CLICKED".equals(phase)) {
            AccessibilityNodeInfo editor = findEditable(root);
            if (editor != null && setText(editor, caption)) {
                AutoPublishState.phase(this, "CAPTION_SET");
                log("AUTO_PUBLISH", "CAPTION_SET");
                phase = "CAPTION_SET";
            }
        }

        // Kwai's share/edit flow varies by version and locale. While the
        // handoff is armed, advance only positive flow controls; never tap
        // cancel/back/discard nodes.
        if (hasAny(snap, "next", "avançar", "continuar", "continue", "próximo", "proximo")) {
            if (clickSemanticExact("next", "avançar", "continuar", "continue", "próximo", "proximo")) {
                AutoPublishState.phase(this, "ADVANCED");
                log("AUTO_PUBLISH", "ADVANCE");
                return;
            }
        }

        boolean publishScreen = hasAny(snap,
                "caption", "legenda", "description", "descrição", "descricao",
                "cover", "capa", "visibility", "visibilidade", "draft", "rascunho",
                "who can view", "quem pode ver", "add location", "localização", "localizacao");
        if (publishScreen && hasAny(snap,
                "publish", "publicar", "post", "postar", "share", "compartilhar", "enviar")) {
            if (clickSemanticExact("publish", "publicar", "post", "postar", "share", "compartilhar", "enviar")) {
                AutoPublishState.phase(this, "PUBLISH_CLICKED");
                log("AUTO_PUBLISH", "PUBLISH_CLICKED job=" + AutoPublishState.jobId(this));
                return;
            }
        }

        // Some Kwai builds show a final Done/Finish control after processing.
        if ("PUBLISH_CLICKED".equals(phase)
                && hasAny(snap, "done", "concluir", "finalizar", "finish")) {
            if (clickSemanticExact("done", "concluir", "finalizar", "finish")) {
                log("AUTO_PUBLISH", "FINALIZE");
            }
        }
    }

    private KwaiState detect(AccessibilityNodeInfo root) {
        String text = snapshot(root).toLowerCase(Locale.ROOT);
        if (hasAny(text, "resource downloading", "downloading resources")) return KwaiState.RESOURCE_LOADING;
        if (hasAny(text, "password", "senha", "verification code", "código de verificação", "log in", "login", "entrar")) return KwaiState.LOGIN_REQUIRED;
        if (hasAny(text, "edit profile", "editar perfil") && hasAny(text, "followers", "seguidores")) return KwaiState.AUTHENTICATED;
        if (findById(root, "id_home_bottom_tab_me") != null || findById(root, "ll_profile") != null) return KwaiState.MAIN;
        if (hasAny(text, "profile", "perfil") && hasAny(text, "log in", "login", "entrar", "sign in")) return KwaiState.PROFILE;
        if (hasAny(text, "verification code", "código de verificação", "otp", "verify")) return KwaiState.AUTH_CHALLENGE;
        return KwaiState.UNKNOWN_UI;
    }

    public boolean clickSemantic(String... needles) {
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) return false;
        ArrayDeque<AccessibilityNodeInfo> queue = new ArrayDeque<>();
        queue.add(root);
        while (!queue.isEmpty()) {
            AccessibilityNodeInfo node = queue.remove();
            String text = nodeText(node).toLowerCase(Locale.ROOT);
            for (String needle : needles) {
                if (text.contains(needle.toLowerCase(Locale.ROOT)) && clickNodeOrParent(node)) {
                    log("ACTION", "CLICK:" + needle);
                    return true;
                }
            }
            for (int i = 0; i < node.getChildCount(); i++) {
                AccessibilityNodeInfo child = node.getChild(i);
                if (child != null) queue.add(child);
            }
        }
        return false;
    }

    private boolean clickSemanticExact(String... labels) {
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) return false;
        ArrayDeque<AccessibilityNodeInfo> queue = new ArrayDeque<>();
        queue.add(root);
        while (!queue.isEmpty()) {
            AccessibilityNodeInfo node = queue.remove();
            String text = visibleText(node).trim().toLowerCase(Locale.ROOT);
            for (String label : labels) {
                String wanted = label.toLowerCase(Locale.ROOT);
                if ((text.equals(wanted) || text.startsWith(wanted + " ") || text.endsWith(" " + wanted))
                        && clickNodeOrParent(node)) {
                    log("ACTION", "AUTO_CLICK:" + label);
                    return true;
                }
            }
            for (int i = 0; i < node.getChildCount(); i++) {
                AccessibilityNodeInfo child = node.getChild(i);
                if (child != null) queue.add(child);
            }
        }
        return false;
    }

    private AccessibilityNodeInfo findEditable(AccessibilityNodeInfo root) {
        ArrayDeque<AccessibilityNodeInfo> queue = new ArrayDeque<>();
        queue.add(root);
        while (!queue.isEmpty()) {
            AccessibilityNodeInfo node = queue.remove();
            if (node.isEditable() && node.isEnabled()) return node;
            for (int i = 0; i < node.getChildCount(); i++) {
                AccessibilityNodeInfo child = node.getChild(i);
                if (child != null) queue.add(child);
            }
        }
        return null;
    }

    private boolean setText(AccessibilityNodeInfo node, String value) {
        Bundle args = new Bundle();
        args.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, value);
        return node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args);
    }

    private boolean clickNodeOrParent(AccessibilityNodeInfo node) {
        for (int i = 0; node != null && i < 5; i++, node = node.getParent()) {
            if (node.isClickable() && node.isEnabled()) {
                return node.performAction(AccessibilityNodeInfo.ACTION_CLICK);
            }
        }
        return false;
    }

    private AccessibilityNodeInfo findById(AccessibilityNodeInfo root, String suffix) {
        ArrayDeque<AccessibilityNodeInfo> queue = new ArrayDeque<>();
        queue.add(root);
        while (!queue.isEmpty()) {
            AccessibilityNodeInfo node = queue.remove();
            String id = node.getViewIdResourceName();
            if (id != null && id.endsWith("/" + suffix)) return node;
            for (int i = 0; i < node.getChildCount(); i++) {
                AccessibilityNodeInfo child = node.getChild(i);
                if (child != null) queue.add(child);
            }
        }
        return null;
    }

    private String snapshot(AccessibilityNodeInfo root) {
        StringBuilder out = new StringBuilder();
        ArrayDeque<AccessibilityNodeInfo> queue = new ArrayDeque<>();
        queue.add(root);
        int count = 0;
        while (!queue.isEmpty() && count++ < 800) {
            AccessibilityNodeInfo node = queue.remove();
            out.append(' ').append(nodeText(node));
            for (int i = 0; i < node.getChildCount(); i++) {
                AccessibilityNodeInfo child = node.getChild(i);
                if (child != null) queue.add(child);
            }
        }
        return out.toString();
    }

    private String visibleText(AccessibilityNodeInfo node) {
        CharSequence text = node.getText();
        CharSequence desc = node.getContentDescription();
        if (text != null && text.length() > 0) return text.toString();
        return desc == null ? "" : desc.toString();
    }

    private String nodeText(AccessibilityNodeInfo node) {
        return String.valueOf(node.getText()) + " "
                + String.valueOf(node.getContentDescription()) + " "
                + String.valueOf(node.getViewIdResourceName());
    }

    private boolean hasAny(String source, String... values) {
        for (String value : values) if (source.contains(value)) return true;
        return false;
    }

    private void log(String key, String value) {
        android.util.Log.i("AntharesAgent", key + "=" + value);
    }
}
