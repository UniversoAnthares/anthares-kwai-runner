package us.anthares.agent;

import android.content.BroadcastReceiver;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/** Minimal ADB-facing semantic diagnostic bridge. It never performs publication by itself. */
public class AntharesCommandReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        String cmd = intent == null ? "" : safe(intent.getStringExtra("cmd"));
        String arg = intent == null ? "" : safe(intent.getStringExtra("arg"));
        String result;
        if ("snapshot".equals(cmd)) {
            result = AntharesAutomationService.commandSnapshot();
            logChunks("COMMAND_SNAPSHOT", result);
        } else if ("click_exact".equals(cmd)) {
            result = AntharesAutomationService.commandClickExact(arg) ? "OK" : "MISS";
            Log.i("AntharesAgent", "COMMAND_CLICK_EXACT=" + result + " arg=" + arg);
        } else if ("click_contains".equals(cmd)) {
            result = AntharesAutomationService.commandClickContains(arg) ? "OK" : "MISS";
            Log.i("AntharesAgent", "COMMAND_CLICK_CONTAINS=" + result + " arg=" + arg);
        } else if ("clipboard".equals(cmd)) {
            ClipboardManager cm=(ClipboardManager)context.getSystemService(Context.CLIPBOARD_SERVICE);
            ClipData clip=cm==null?null:cm.getPrimaryClip();
            CharSequence text=(clip!=null&&clip.getItemCount()>0)?clip.getItemAt(0).coerceToText(context):"";
            result=text==null?"":text.toString();
            logChunks("COMMAND_CLIPBOARD",result);
        } else {
            result="BAD_COMMAND";
        }
        setResultCode(0);
        setResultData(result.length()>3000?result.substring(0,3000):result);
    }
    private static String safe(String s){return s==null?"":s.trim();}
    private static void logChunks(String key,String value){
        if(value==null)value="";
        if(value.isEmpty()){Log.i("AntharesAgent",key+"=");return;}
        int part=0;
        for(int i=0;i<value.length();i+=3000){int e=Math.min(value.length(),i+3000);Log.i("AntharesAgent",key+"_"+(part++)+"="+value.substring(i,e));}
    }
}
