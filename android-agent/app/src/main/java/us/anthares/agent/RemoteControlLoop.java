package us.anthares.agent;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.util.Log;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/** Outbound-only HTTPS control loop. No ADB, inbound port or LAN address is required after provisioning. */
final class RemoteControlLoop {
    private static final String TAG="AntharesAgent";
    private static final String PREFS="anthares_remote_control";
    private static final String PRIMARY="https://anthares-remote-primary.vercel.app";
    private static final String BACKUP="https://anthares-remote-secondary.vercel.app";
    private static volatile Thread worker;
    private static volatile boolean running;
    private RemoteControlLoop() {}

    static synchronized void start(Context source) {
        if (running && worker != null && worker.isAlive()) return;
        Context app=source.getApplicationContext();
        running=true;
        worker=new Thread(() -> loop(app), "anthares-remote-control");
        worker.setDaemon(true);
        worker.start();
        Log.i(TAG,"REMOTE_CONTROL=STARTED");
    }

    static synchronized void stop() {
        running=false;
        if(worker!=null) worker.interrupt();
        worker=null;
    }

    private static void loop(Context c) {
        long backoff=3000L;
        while(running){
            try {
                Config cfg=loadConfig(c);
                if(cfg==null){ sleep(5000); continue; }
                String base=heartbeat(c,cfg,PRIMARY) ? PRIMARY : (heartbeat(c,cfg,BACKUP) ? BACKUP : null);
                if(base==null){ sleep(backoff); backoff=Math.min(backoff*2,60000L); continue; }
                backoff=3000L;
                JSONObject job=nextJob(cfg,base);
                if(job!=null){
                    JSONObject result=execute(c,job);
                    postResult(cfg,base,job.optString("id"),result);
                }
                sleep(job==null?5000:500);
            } catch(Throwable t){
                Log.w(TAG,"REMOTE_CONTROL_ERROR="+t.getClass().getSimpleName());
                sleep(backoff); backoff=Math.min(backoff*2,60000L);
            }
        }
    }

    private static boolean heartbeat(Context c,Config cfg,String base){
        try{
            JSONObject body=new JSONObject();
            body.put("agent","anthares-android-agent");
            body.put("transport","outbound_https");
            body.put("model",Build.MODEL);
            body.put("sdk",Build.VERSION.SDK_INT);
            body.put("accessibility_connected",AntharesAutomationService.commandSnapshot().equals("SERVICE_NOT_CONNECTED")?false:true);
            body.put("publish_armed",AutoPublishState.isArmed(c));
            body.put("publish_phase",AutoPublishState.phase(c));
            Response r=request("POST",base+"/v1/device/heartbeat",cfg,body.toString());
            boolean ok=r.code>=200&&r.code<300;
            if(ok) Log.i(TAG,"REMOTE_HEARTBEAT=OK base="+base);
            return ok;
        }catch(Exception e){return false;}
    }

    private static JSONObject nextJob(Config cfg,String base) throws Exception{
        Response r=request("GET",base+"/v1/device/jobs/next",cfg,null);
        if(r.code==204) return null;
        if(r.code<200||r.code>=300) throw new IllegalStateException("next_http_"+r.code);
        JSONObject root=new JSONObject(r.body);
        return root.optJSONObject("job");
    }

    private static void postResult(Config cfg,String base,String id,JSONObject result) throws Exception{
        if(id==null||id.isEmpty()) return;
        Response r=request("POST",base+"/v1/device/jobs/"+Uri.encode(id)+"/result",cfg,result.toString());
        if(r.code<200||r.code>=300) throw new IllegalStateException("result_http_"+r.code);
    }

    private static JSONObject execute(Context c,JSONObject job){
        JSONObject out=new JSONObject();
        String type=job.optString("type","");
        JSONObject args=job.optJSONObject("args"); if(args==null) args=new JSONObject();
        try{
            if("ping".equals(type)){
                out.put("ok",true); out.put("pong",true); out.put("model",Build.MODEL); out.put("sdk",Build.VERSION.SDK_INT);
            } else if("snapshot".equals(type)){
                out.put("ok",true); out.put("snapshot",AntharesAutomationService.commandSnapshot());
            } else if("click_exact".equals(type)){
                boolean ok=AntharesAutomationService.commandClickExact(args.optString("label")); out.put("ok",ok);
            } else if("click_contains".equals(type)){
                boolean ok=AntharesAutomationService.commandClickContains(args.optString("label")); out.put("ok",ok);
            } else if("click_id".equals(type)){
                boolean ok=AntharesAutomationService.commandClickId(args.optString("id")); out.put("ok",ok);
            } else if("kwai_handoff".equals(type)){
                String url=args.optString("url",""); String sha=args.optString("sha256",""); String caption=args.optString("caption",""); String jid=job.optString("id","");
                if(!url.startsWith("https://")||!sha.matches("(?i)[0-9a-f]{64}")) throw new IllegalArgumentException("bad_handoff_args");
                Uri link=new Uri.Builder().scheme("anthares-kwai").authority("send").appendQueryParameter("url",url).appendQueryParameter("sha256",sha).appendQueryParameter("caption",caption).appendQueryParameter("job_id",jid).build();
                Intent i=new Intent(Intent.ACTION_VIEW,link); i.setClass(c,MainActivity.class); i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_SINGLE_TOP); c.startActivity(i);
                out.put("ok",true); out.put("accepted",true); out.put("final",false); out.put("phase","HANDOFF_STARTED");
            } else {
                out.put("ok",false); out.put("error","unsupported_job_type"); out.put("type",type);
            }
        }catch(Throwable t){
            try{out.put("ok",false);out.put("error",t.getClass().getSimpleName());}catch(Exception ignored){}
        }
        return out;
    }

    private static Config loadConfig(Context c){
        try{
            File dir=c.getExternalFilesDir(null);
            File bootstrap=dir==null?null:new File(dir,"bootstrap.json");
            if(bootstrap!=null&&bootstrap.isFile()){
                StringBuilder s=new StringBuilder();
                try(BufferedReader br=new BufferedReader(new FileReader(bootstrap))){String line;while((line=br.readLine())!=null)s.append(line);}
                JSONObject j=new JSONObject(s.toString()); String token=j.optString("token","").trim(); String id=j.optString("device_id","").trim();
                if(token.length()>=20&&id.matches("[A-Za-z0-9._-]{3,100}")){
                    c.getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putString("token",token).putString("device_id",id).apply();
                    if(!bootstrap.delete()) Log.w(TAG,"BOOTSTRAP_DELETE=FAILED"); else Log.i(TAG,"BOOTSTRAP=CONSUMED");
                }
            }
            String token=c.getSharedPreferences(PREFS,Context.MODE_PRIVATE).getString("token","");
            String id=c.getSharedPreferences(PREFS,Context.MODE_PRIVATE).getString("device_id","");
            if(token==null||token.length()<20||id==null||id.length()<3) return null;
            return new Config(token,id);
        }catch(Exception e){Log.w(TAG,"CONFIG_ERROR="+e.getClass().getSimpleName());return null;}
    }

    private static Response request(String method,String raw,Config cfg,String body) throws Exception{
        URL u=new URL(raw); if(!"https".equalsIgnoreCase(u.getProtocol())) throw new SecurityException("https_required");
        String host=u.getHost(); if(!"anthares-remote-primary.vercel.app".equals(host)&&!"anthares-ara-vercel-reserve.vercel.app".equals(host)) throw new SecurityException("host_not_allowed");
        HttpURLConnection x=(HttpURLConnection)u.openConnection(); x.setConnectTimeout(12000);x.setReadTimeout(20000);x.setRequestMethod(method);x.setRequestProperty("Authorization","Bearer "+cfg.token);x.setRequestProperty("X-Anthares-Device",cfg.deviceId);x.setRequestProperty("Accept","application/json");
        if(body!=null){byte[] data=body.getBytes(StandardCharsets.UTF_8);x.setDoOutput(true);x.setRequestProperty("Content-Type","application/json");try(OutputStream o=x.getOutputStream()){o.write(data);}}
        int code=x.getResponseCode();InputStream in=code>=400?x.getErrorStream():x.getInputStream();StringBuilder s=new StringBuilder();if(in!=null)try(BufferedReader br=new BufferedReader(new InputStreamReader(in,StandardCharsets.UTF_8))){String line;while((line=br.readLine())!=null)s.append(line);}x.disconnect();return new Response(code,s.toString());
    }

    private static void sleep(long ms){try{Thread.sleep(ms);}catch(InterruptedException ignored){Thread.currentThread().interrupt();}}
    private static final class Config{final String token,deviceId;Config(String t,String d){token=t;deviceId=d;}}
    private static final class Response{final int code;final String body;Response(int c,String b){code=c;body=b;}}
}
