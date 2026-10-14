package com.anthares.kwaiup;

import android.os.Bundle;
import com.android.uiautomator.core.UiDevice;
import com.android.uiautomator.testrunner.UiAutomatorTestCase;

public class KwaiUpUiTest extends UiAutomatorTestCase {
    private int paramInt(String name) {
        Bundle params = getParams();
        String raw = params == null ? null : params.getString(name);
        if (raw == null) throw new IllegalArgumentException("missing param: " + name);
        return Integer.parseInt(raw);
    }

    public void testClick() throws Exception {
        UiDevice device = getUiDevice();
        int x = paramInt("x");
        int y = paramInt("y");
        if (!device.click(x, y)) throw new AssertionError("click failed");
        Thread.sleep(500);
    }

    public void testSwipe() throws Exception {
        UiDevice device = getUiDevice();
        int x1 = paramInt("x1");
        int y1 = paramInt("y1");
        int x2 = paramInt("x2");
        int y2 = paramInt("y2");
        int steps = paramInt("steps");
        if (!device.swipe(x1, y1, x2, y2, steps)) throw new AssertionError("swipe failed");
        Thread.sleep(500);
    }

    public void testBack() throws Exception {
        if (!getUiDevice().pressBack()) throw new AssertionError("back failed");
        Thread.sleep(300);
    }
}
