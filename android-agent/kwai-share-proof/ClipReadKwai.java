import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.os.Looper;
import java.lang.reflect.Method;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Shell-only read of Kwai URL in Android clipboard. Never writes clipboard. */
public final class ClipReadKwai {
  private static final Pattern URL=Pattern.compile(
     "https://(?:k\\.kwai\\.com/p/[A-Za-z0-9_-]+|www\\.kwai\\.com/@[A-Za-z0-9_.-]+/(?:photo|video)/[0-9]+)");
  private static void match(String candidate) {
    if (candidate==null) return;
    Matcher m=URL.matcher(candidate);
    while(m.find()) System.out.println("KWAI_PUBLIC_URL="+m.group(0));
  }
  public static void main(String[] args) throws Exception {
    Looper.prepareMainLooper();
    Class<?> at=Class.forName("android.app.ActivityThread");
    Method systemMain=at.getDeclaredMethod("systemMain");
    systemMain.setAccessible(true);
    Object thread=systemMain.invoke(null);
    Method getContext=at.getDeclaredMethod("getSystemContext");
    getContext.setAccessible(true);
    Context system=(Context)getContext.invoke(thread);
    Context shell=system.createPackageContext("com.android.shell",Context.CONTEXT_IGNORE_SECURITY);
    ClipboardManager clipboard=(ClipboardManager)shell.getSystemService(Context.CLIPBOARD_SERVICE);
    if(clipboard==null) throw new IllegalStateException("no clipboard service");
    ClipData data=clipboard.getPrimaryClip();
    if(data==null) throw new IllegalStateException("empty clipboard");
    for(int i=0;i<data.getItemCount();i++){
      ClipData.Item item=data.getItemAt(i);
      CharSequence txt=item.getText();
      if(txt!=null)match(txt.toString());
      match(item.getHtmlText());
      if(item.getUri()!=null)match(item.getUri().toString());
      Intent intent=item.getIntent();
      if(intent!=null) {
        match(intent.toUri(Intent.URI_INTENT_SCHEME));
        if(intent.getData()!=null)match(intent.getData().toString());
        CharSequence extra=intent.getCharSequenceExtra(Intent.EXTRA_TEXT);
        if(extra!=null)match(extra.toString());
      }
    }
  }
}
