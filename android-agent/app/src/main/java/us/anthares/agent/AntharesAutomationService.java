package us.anthares.agent;

import android.accessibilityservice.AccessibilityService;
import android.os.Bundle;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import java.util.ArrayDeque;
import java.util.Locale;

/** Accessibility-based semantic driver used when uiautomator is unavailable. */
public class AntharesAutomationService extends AccessibilityService {
    private static volatile AntharesAutomationService INSTANCE;
    private static final String KWAI_FULL = "com.kwai.video";
    private static final String KWAI_LITE = "kwai.lite.video";

    @Override protected void onServiceConnected() { super.onServiceConnected(); INSTANCE=this; RemoteControlLoop.start(this); log("SERVICE","CONNECTED"); }
    @Override public void onDestroy() { RemoteControlLoop.stop(); if(INSTANCE==this) INSTANCE=null; super.onDestroy(); }
    @Override public void onAccessibilityEvent(AccessibilityEvent event) {
        if(event==null||event.getPackageName()==null)return;
        String pkg=event.getPackageName().toString(); if(!KWAI_FULL.equals(pkg)&&!KWAI_LITE.equals(pkg))return;
        AccessibilityNodeInfo root=getRootInActiveWindow(); if(root==null)return;
        if(AutoPublishState.isArmed(this))driveAutomaticPublish(root,snapshot(root).toLowerCase(Locale.ROOT));
    }
    @Override public void onInterrupt(){log("SERVICE","INTERRUPTED");}

    private void driveAutomaticPublish(AccessibilityNodeInfo root,String snap){
        String phase=AutoPublishState.phase(this),job=AutoPublishState.jobId(this);
        if(hasAny(snap,"published successfully","post published","publicado com sucesso","publicaÃ§Ã£o concluÃ­da","publicacao concluida","video posted","vÃ­deo publicado","video publicado")){log("AUTO_PUBLISH","CONFIRMED job="+job);AutoPublishState.clear(this);return;}
        if(hasAny(snap,"failed","falhou","try again","tente novamente","erro ao publicar")){log("AUTO_PUBLISH","UNCERTAIN_VISIBLE_ERROR job="+job);return;}
        String caption=AutoPublishState.caption(this);
        if(!caption.isEmpty()&&!"CAPTION_SET".equals(phase)&&!"PUBLISH_CLICKED".equals(phase)){
            AccessibilityNodeInfo editor=findEditable(root); if(editor!=null&&setText(editor,caption)){AutoPublishState.phase(this,"CAPTION_SET");log("AUTO_PUBLISH","CAPTION_SET job="+job);phase="CAPTION_SET";}
        }
        if(hasAny(snap,"next","avanÃ§ar","avancar","continuar","continue","prÃ³ximo","proximo")&&clickSemanticExact(root,"next","avanÃ§ar","avancar","continuar","continue","prÃ³ximo","proximo")){AutoPublishState.phase(this,"ADVANCED");log("AUTO_PUBLISH","ADVANCE job="+job);return;}
        boolean publishScreen=hasAny(snap,"caption","legenda","description","descriÃ§Ã£o","descricao","cover","capa","visibility","visibilidade","draft","rascunho","who can view","quem pode ver","add location","localizaÃ§Ã£o","localizacao");
        if(publishScreen&&hasAny(snap,"publish","publicar","post","postar","share","compartilhar","enviar")&&clickSemanticExact(root,"publish","publicar","post","postar","share","compartilhar","enviar")){AutoPublishState.phase(this,"PUBLISH_CLICKED");log("AUTO_PUBLISH","PUBLISH_CLICKED job="+job);return;}
        if("PUBLISH_CLICKED".equals(phase)&&hasAny(snap,"done","concluir","finalizar","finish")&&clickSemanticExact(root,"done","concluir","finalizar","finish"))log("AUTO_PUBLISH","FINALIZE job="+job);
    }

    public static String commandSnapshot(){AntharesAutomationService s=INSTANCE;if(s==null)return "SERVICE_NOT_CONNECTED";AccessibilityNodeInfo r=s.getRootInActiveWindow();return r==null?"ROOT_NULL":s.snapshot(r);}
    public static boolean commandClickExact(String label){AntharesAutomationService s=INSTANCE;if(s==null)return false;AccessibilityNodeInfo r=s.getRootInActiveWindow();return r!=null&&s.clickSemanticExact(r,label);}
    public static boolean commandClickContains(String label){
        AntharesAutomationService s=INSTANCE;if(s==null)return false;AccessibilityNodeInfo root=s.getRootInActiveWindow();if(root==null)return false;
        String wanted=label==null?"":label.trim().toLowerCase(Locale.ROOT);if(wanted.isEmpty())return false;
        ArrayDeque<AccessibilityNodeInfo>q=new ArrayDeque<>();q.add(root);while(!q.isEmpty()){AccessibilityNodeInfo n=q.remove();if(nodeText(n).toLowerCase(Locale.ROOT).contains(wanted)&&clickNodeOrParent(n))return true;for(int i=0;i<n.getChildCount();i++){AccessibilityNodeInfo c=n.getChild(i);if(c!=null)q.add(c);}}return false;
    }
    public static boolean commandClickId(String suffix){
        AntharesAutomationService s=INSTANCE;if(s==null)return false;AccessibilityNodeInfo root=s.getRootInActiveWindow();if(root==null)return false;
        String wanted=suffix==null?"":suffix.trim();if(wanted.isEmpty())return false;
        ArrayDeque<AccessibilityNodeInfo>q=new ArrayDeque<>();q.add(root);while(!q.isEmpty()){AccessibilityNodeInfo n=q.remove();String id=n.getViewIdResourceName();if(id!=null&&(id.equals(wanted)||id.endsWith("/"+wanted))&&clickNodeOrParent(n))return true;for(int i=0;i<n.getChildCount();i++){AccessibilityNodeInfo c=n.getChild(i);if(c!=null)q.add(c);}}return false;
    }

    private boolean clickSemanticExact(AccessibilityNodeInfo root,String...labels){ArrayDeque<AccessibilityNodeInfo>q=new ArrayDeque<>();q.add(root);while(!q.isEmpty()){AccessibilityNodeInfo n=q.remove();String text=visibleText(n).trim().toLowerCase(Locale.ROOT);for(String label:labels){String wanted=label.toLowerCase(Locale.ROOT);if((text.equals(wanted)||text.startsWith(wanted+" ")||text.endsWith(" "+wanted))&&clickNodeOrParent(n))return true;}for(int i=0;i<n.getChildCount();i++){AccessibilityNodeInfo c=n.getChild(i);if(c!=null)q.add(c);}}return false;}
    private AccessibilityNodeInfo findEditable(AccessibilityNodeInfo root){ArrayDeque<AccessibilityNodeInfo>q=new ArrayDeque<>();q.add(root);while(!q.isEmpty()){AccessibilityNodeInfo n=q.remove();if(n.isEditable()&&n.isEnabled())return n;for(int i=0;i<n.getChildCount();i++){AccessibilityNodeInfo c=n.getChild(i);if(c!=null)q.add(c);}}return null;}
    private boolean setText(AccessibilityNodeInfo node,String value){Bundle b=new Bundle();b.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE,value);return node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT,b);}
    private static boolean clickNodeOrParent(AccessibilityNodeInfo node){for(int i=0;node!=null&&i<6;i++,node=node.getParent())if(node.isClickable()&&node.isEnabled())return node.performAction(AccessibilityNodeInfo.ACTION_CLICK);return false;}
    private String snapshot(AccessibilityNodeInfo root){StringBuilder out=new StringBuilder();ArrayDeque<AccessibilityNodeInfo>q=new ArrayDeque<>();q.add(root);int count=0;while(!q.isEmpty()&&count++<1000){AccessibilityNodeInfo n=q.remove();out.append(' ').append(nodeText(n));for(int i=0;i<n.getChildCount();i++){AccessibilityNodeInfo c=n.getChild(i);if(c!=null)q.add(c);}}return out.toString();}
    private static String visibleText(AccessibilityNodeInfo n){CharSequence t=n.getText(),d=n.getContentDescription();if(t!=null&&t.length()>0)return t.toString();return d==null?"":d.toString();}
    private static String nodeText(AccessibilityNodeInfo n){return String.valueOf(n.getText())+" "+String.valueOf(n.getContentDescription())+" "+String.valueOf(n.getViewIdResourceName());}
    private static boolean hasAny(String source,String...values){for(String v:values)if(source.contains(v))return true;return false;}
    private void log(String key,String value){android.util.Log.i("AntharesAgent",key+"="+value);}
}

