package us.anthares.agent;

import android.app.Activity;
import android.content.ClipData;
import android.content.ContentUris;
import android.content.Intent;
import android.net.Uri;
import android.provider.MediaStore;
import android.widget.Toast;
import java.io.InputStream;
import java.security.MessageDigest;
import java.util.Locale;

/** Verified handoff for media already staged in Android MediaStore by Anthares ADB. */
public final class LocalMediaHandoff {
    private static final String FULL="com.kwai.video";
    private static final String LITE="kwai.lite.video";
    private LocalMediaHandoff() {}

    public static void share(Activity activity, Uri link) {
        try {
            String id=link.getQueryParameter("media_id");
            String expected=safe(link.getQueryParameter("sha256"),64).toLowerCase(Locale.ROOT);
            String caption=safe(link.getQueryParameter("caption"),500);
            String job=safe(link.getQueryParameter("job_id"),160);
            String pkg=safe(link.getQueryParameter("package"),80);
            if (!FULL.equals(pkg) && !LITE.equals(pkg)) throw new IllegalArgumentException("package");
            if (id==null || !id.matches("[0-9]{1,18}") || !expected.matches("[0-9a-f]{64}")) throw new IllegalArgumentException("identity");
            Uri media=ContentUris.withAppendedId(MediaStore.Video.Media.EXTERNAL_CONTENT_URI,Long.parseLong(id));
            MessageDigest d=MessageDigest.getInstance("SHA-256");
            long total=0; byte[] buf=new byte[65536];
            try(InputStream in=activity.getContentResolver().openInputStream(media)){
                if(in==null) throw new IllegalStateException("media");
                int n; while((n=in.read(buf))!=-1){total+=n;d.update(buf,0,n);}
            }
            if(total<=0 || !hex(d.digest()).equals(expected)) throw new IllegalStateException("sha256");
            AutoPublishState.arm(activity,caption,job);
            Intent send=new Intent(Intent.ACTION_SEND);
            send.setType("video/mp4"); send.setPackage(pkg);
            send.putExtra(Intent.EXTRA_STREAM,media);
            if(!caption.isEmpty()) send.putExtra(Intent.EXTRA_TEXT,caption);
            send.setClipData(ClipData.newUri(activity.getContentResolver(),"Anthares video",media));
            send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            activity.startActivity(send);
            android.util.Log.i("AntharesAgent","LOCAL_HANDOFF=VERIFIED job="+job+" package="+pkg+" bytes="+total);
        } catch(Exception e){
            AutoPublishState.clear(activity);
            android.util.Log.i("AntharesAgent","LOCAL_HANDOFF=FAILED "+e.getClass().getSimpleName());
            Toast.makeText(activity,"Handoff Anthares recusado: "+e.getClass().getSimpleName(),Toast.LENGTH_LONG).show();
        }
    }
    private static String safe(String v,int max){if(v==null)return "";v=v.trim();return v.length()<=max?v:v.substring(0,max);}
    private static String hex(byte[] b){StringBuilder s=new StringBuilder(b.length*2);for(byte x:b)s.append(String.format(Locale.ROOT,"%02x",x&255));return s.toString();}
}
