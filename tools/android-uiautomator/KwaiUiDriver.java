package us.anthares.tools;

import android.os.Bundle;
import android.app.UiAutomation;
import android.view.accessibility.AccessibilityNodeInfo;
import java.util.ArrayDeque;
import android.util.Base64;
import java.nio.charset.StandardCharsets;
import com.android.uiautomator.core.UiDevice;
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiSelector;
import com.android.uiautomator.testrunner.UiAutomatorTestCase;

/** Minimal, allowlisted UIAutomator driver used only for the physical Kwai test device. */
public final class KwaiUiDriver extends UiAutomatorTestCase {
    public void testAction() throws Exception {
        Bundle p = getParams();
        String action = p == null ? null : p.getString("action");
        String value = p == null ? null : p.getString("value");
        String encoded = p == null ? null : p.getString("value_base64");
        if (encoded != null && !encoded.isEmpty()) {
            value = new String(Base64.decode(encoded, Base64.NO_WRAP), StandardCharsets.UTF_8);
        }
        if (action == null || value == null) {
            throw new IllegalArgumentException("action and value are required");
        }

        UiDevice device = getUiDevice();
        device.waitForIdle(1500);

        UiObject target;
        if ("clickXY".equals(action)) {
            String[] parts = value.split(",", -1);
            if (parts.length != 2) throw new IllegalArgumentException("clickXY requires x,y");
            int x = Integer.parseInt(parts[0]);
            int y = Integer.parseInt(parts[1]);
            if (x < 0 || x > 1080 || y < 0 || y > 2340) throw new IllegalArgumentException("coordinates outside physical-device bounds");
            require(device.click(x, y), "coordinate click failed: " + value);
        } else if ("clickText".equals(action)) {
            target = new UiObject(new UiSelector().text(value));
            require(target.exists(), "text not found: " + value);
            require(target.click(), "click failed: " + value);
        } else if ("clickTextContains".equals(action)) {
            target = new UiObject(new UiSelector().textContains(value));
            require(target.exists(), "text fragment not found: " + value);
            require(target.click(), "click failed: " + value);
        } else if ("clickResource".equals(action)) {
            target = new UiObject(new UiSelector().resourceId(value));
            require(target.exists(), "resource not found: " + value);
            require(target.click(), "click failed: " + value);
        } else if ("setFirstEditText".equals(action)) {
            // Atomic accessibility text replacement, independent of the
            // Android IME's unreliable 'input text' and UiObject.setText.
            UiAutomation automation = findInstrumentation().getUiAutomation();
            AccessibilityNodeInfo root = automation.getRootInActiveWindow();
            AccessibilityNodeInfo edit = findResource(root, "com.kwai.video.basis:id/editor");
            require(edit != null && edit.isEnabled(), "Kwai editor not visible");
            Bundle args = new Bundle();
            args.putCharSequence("ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE", value);
            require(edit.performAction(0x200000, args), "ACTION_SET_TEXT failed");
            Thread.sleep(900);
            AccessibilityNodeInfo refreshed = findResource(
                automation.getRootInActiveWindow(), "com.kwai.video.basis:id/editor");
            require(refreshed != null && value.contentEquals(refreshed.getText()),
                    "ACTION_SET_TEXT not persisted in editor");
        } else {
            throw new IllegalArgumentException("unsupported action: " + action);
        }
        device.waitForIdle(2000);
        System.out.println("ANTHARES_UI_OK action=" + action);
    }

    // The SDK18 android.jar stub omits the inherited InstrumentationTestCase
    // method even though the Android platform UIAutomator runner supplies it.
    // Android 25 permits this bounded reflection on the known test superclass.
    private android.app.Instrumentation findInstrumentation() throws Exception {
        for (Class<?> type = getClass(); type != null; type = type.getSuperclass()) {
            try {
                java.lang.reflect.Method getter = type.getDeclaredMethod("getInstrumentation");
                getter.setAccessible(true);
                Object resolved = getter.invoke(this);
                if (resolved instanceof android.app.Instrumentation) {
                    return (android.app.Instrumentation) resolved;
                }
            } catch (NoSuchMethodException ignored) {
                // Continue through UiAutomatorTestCase -> InstrumentationTestCase.
            }
        }
        throw new IllegalStateException("instrumentation-unavailable");
    }

    private static AccessibilityNodeInfo findResource(AccessibilityNodeInfo root, String id) {
        if (root == null) return null;
        ArrayDeque<AccessibilityNodeInfo> queue = new ArrayDeque<AccessibilityNodeInfo>();
        queue.add(root);
        int scanned = 0;
        while (!queue.isEmpty() && scanned++ < 1200) {
            AccessibilityNodeInfo node = queue.remove();
            if (id.equals(node.getViewIdResourceName())) return node;
            for (int i = 0; i < node.getChildCount(); i++) {
                AccessibilityNodeInfo child = node.getChild(i);
                if (child != null) queue.add(child);
            }
        }
        return null;
    }

    private static void require(boolean ok, String message) {
        if (!ok) throw new IllegalStateException(message);
    }
}
