package us.anthares.tools;

import android.os.Bundle;
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
        if (action == null || value == null) {
            throw new IllegalArgumentException("action and value are required");
        }

        UiDevice device = getUiDevice();
        device.waitForIdle(1500);

        UiObject target;
        if ("clickText".equals(action)) {
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
            target = new UiObject(new UiSelector().className("android.widget.EditText").instance(0));
            require(target.exists(), "EditText not found");
            require(target.setText(value), "setText failed");
        } else {
            throw new IllegalArgumentException("unsupported action: " + action);
        }
        device.waitForIdle(2000);
        System.out.println("ANTHARES_UI_OK action=" + action + " value=" + value);
    }

    private static void require(boolean ok, String message) {
        if (!ok) throw new IllegalStateException(message);
    }
}
