#!/usr/bin/env python3
"""Anthares Studio item 3: immutable read-only SQL audit, no user text or Delta printed."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile

BRANCH='refs/heads/audit/studio-item3-integrity-20261116'
REPO='UniversoAnthares/anthares-kwai-runner'
HOST_KEY='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA7FQ2RBq0cii+VVCqcB90JxkJRPdurdrX1RGThhKtT2'
SHA_PHP='042863a385c5fb8df359c52591bc63a0e033bd9b37e2f8cd8c3992b6d71ad5b7'
SHA_ORIGINAL='13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf'

REMOTE=r"""
import hashlib, json, os, pathlib, subprocess, sys
root=pathlib.Path.home()/'domains/anthares.us/public_html'
src=root/'wp-content/plugins/anthares-estudio/anthares-estudio.php'
dst=root/'wp-content/plugins/anthares-studio/anthares-estudio.php'
def require(condition,reason):
 if not condition:raise RuntimeError(reason)
require(src.is_file() and dst.is_file() and not src.is_symlink() and not dst.is_symlink(),'PLUGIN_FILES_MISSING')
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
require(sha(src)=='13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf','LEGACY_SHA_CHANGED')
require(sha(dst)=='042863a385c5fb8df359c52591bc63a0e033bd9b37e2f8cd8c3992b6d71ad5b7','NEW_PHP_SHA_CHANGED')
phpbin='/opt/alt/php83/usr/bin/php'
require(pathlib.Path(phpbin).is_file(),'PHP83_ABSENT')
audit=r'''
global $wpdb;
$issues=[];
$stat=[];
$logIssue=function($code) use (&$issues){$issues[$code]=($issues[$code]??0)+1;};
$types=['projeto','nota','capitulo','cartao'];
$oldTypes=array_map(function($x){return 'aest_'.$x;},$types);
$newTypes=array_map(function($x){return 'anst_'.$x;},$types);
function st_rows($types) {
 global $wpdb;
 $sql="SELECT * FROM {$wpdb->posts} WHERE post_type IN ('".implode("','",array_map('esc_sql',$types))."') ORDER BY ID ASC";
 return $wpdb->get_results($sql,ARRAY_A);
}
function st_meta($id){
 global $wpdb;
 return $wpdb->get_results($wpdb->prepare("SELECT meta_key,meta_value FROM {$wpdb->postmeta} WHERE post_id=%d ORDER BY meta_id ASC",(int)$id),ARRAY_A);
}
function st_multi($rows){
 $out=[];
 foreach($rows as $row){
  $ident=$row['meta_key']."\x00".hash('sha256',(string)$row['meta_value']);
  $out[$ident]=($out[$ident]??0)+1;
 }
 ksort($out);
 return $out;
}
function st_raw($rows,$key){
 $out=[];
 foreach($rows as $row)if($row['meta_key']===$key)$out[]=(string)$row['meta_value'];
 return $out;
}
function st_zoom($uid,$key){
 global $wpdb;
 return $wpdb->get_col($wpdb->prepare("SELECT meta_value FROM {$wpdb->usermeta} WHERE user_id=%d AND meta_key=%s ORDER BY umeta_id ASC",$uid,$key));
}
$rawOld=st_rows($oldTypes);
$rawNew=st_rows($newTypes);
$old=[];$new=[];$om=[];$nm=[];
foreach($rawOld as $p){$id=(int)$p['ID'];$old[$id]=$p;$om[$id]=st_meta($id);}
foreach($rawNew as $p){$id=(int)$p['ID'];$new[$id]=$p;$nm[$id]=st_meta($id);}
$statsOld=[];$statsNew=[];$statusOld=[];$statusNew=[];
foreach($rawOld as $p){$t=$p['post_type'];$s=$p['post_status'];$statsOld[$t]=($statsOld[$t]??0)+1;$statusOld[$s]=($statusOld[$s]??0)+1;}
foreach($rawNew as $p){$t=$p['post_type'];$s=$p['post_status'];$statsNew[$t]=($statsNew[$t]??0)+1;$statusNew[$s]=($statusNew[$s]??0)+1;}
$map=[];$seenTargets=[];$provenance=[];
foreach($new as $id=>$p) {
 $metadata=$nm[$id];
 $oldIds=st_raw($metadata,'_anst_source_id');
 $sourceTypes=st_raw($metadata,'_anst_source_type');
 $sourceHashes=st_raw($metadata,'_anst_source_sha256');
 if(count($oldIds)!==1||count($sourceTypes)!==1||count($sourceHashes)!==1){$logIssue('PROVENANCE_CARDINALITY');continue;}
 $oid=(int)$oldIds[0];$typ=$sourceTypes[0];
 if((string)$oid!==$oldIds[0]||$oid<=0){$logIssue('INVALID_SOURCE_ID');continue;}
 if(!isset($old[$oid])){$logIssue('UNMAPPED_SOURCE_ID');continue;}
 if($typ!==$old[$oid]['post_type'])$logIssue('SOURCE_TYPE_MISMATCH');
 if(isset($map[$oid])){$logIssue('DUPLICATE_MAPPING');continue;}
 $map[$oid]=$id;$seenTargets[$id]=true;$provenance[$oid]=$sourceHashes[0];
}
$metaMatch=0;$fieldsMatch=0;$deltaRawMatches=0;$deltaValid=0;$deltaCount=0;
$projectRefCount=0;$invalidRef=0;$zoomSource=0;$zoomTarget=0;
$changeCount=0;$sourceState=hash_init('sha256');
$rawFields=['post_status','post_author','post_title','post_content','post_excerpt','post_name','menu_order','comment_status','ping_status','post_password','post_mime_type','post_date','post_date_gmt','post_modified','post_modified_gmt'];
foreach($old as $oid=>$p) {
 $snapshotHash=hash('sha256',serialize([$p,$om[$oid]]));
 hash_update($sourceState,$snapshotHash."\n");
 if(!isset($map[$oid])){$logIssue('MISSING_TARGET');continue;}
 $target=$map[$oid];$n=$new[$target];$allFields=true;
 if($n['post_type']!=='anst_'.substr($p['post_type'],5)){$logIssue('POST_TYPE_MISMATCH');$allFields=false;}
 foreach($rawFields as $field){
  if((string)$p[$field] !== (string)$n[$field]) {$logIssue('FIELD_'.$field);$allFields=false;}
 }
 $oldParent=(int)$p['post_parent'];
 if($oldParent!==0&&!isset($map[$oldParent])){$logIssue('ORPHAN_LEGACY_POST_PARENT');$allFields=false;}
 $newParent=($oldParent===0)?0:($map[$oldParent]??-1);
 if((int)$n['post_parent']!==$newParent){$logIssue('POST_PARENT_MISMATCH');$allFields=false;}
 if($allFields)$fieldsMatch++;
 if(!hash_equals((string)($provenance[$oid]??''),$snapshotHash))$logIssue('SOURCE_CHECKSUM_MISMATCH');
 $expectedMeta=[];
 foreach($om[$oid] as $row){
  $key=(string)$row['meta_key'];$value=(string)$row['meta_value'];
  $key=preg_replace('/^_aest_/','_anst_',$key);
  $key=preg_replace('/^aest_/','anst_',$key);
  if(in_array($key,['_anst_project','_anst_cascade_project'],true)){
   $oldRef=(int)$value;
   if($oldRef!==0&&!isset($map[$oldRef])){$logIssue('ORPHAN_PROJECT_REFERENCE');$invalidRef++;}
   $value=(string)($oldRef===0?0:($map[$oldRef]??-1));
   $projectRefCount++;
  }
  if($key==='_anst_review_v1'){
   $review=json_decode($value,true);
   if(is_array($review)&&isset($review['tasks'])&&is_array($review['tasks'])){
    $changed=false;
    foreach($review['tasks'] as &$task){
     if(!is_array($task)||empty($task['chapter']))continue;
     $oldChapter=(int)$task['chapter'];
     if(!isset($map[$oldChapter])){$logIssue('ORPHAN_REVIEW_CHAPTER');continue;}
     $task['chapter']=$map[$oldChapter];$changed=true;
    }unset($task);
    if($changed)$value=wp_json_encode($review,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);
   }
  }
  $expectedMeta[]=['meta_key'=>$key,'meta_value'=>$value];
 }
 $actualMeta=array_values(array_filter($nm[$target],function($m){return !in_array($m['meta_key'],['_anst_source_id','_anst_source_type','_anst_source_sha256'],true);}));
 if(st_multi($expectedMeta)===st_multi($actualMeta)){$metaMatch++;}else{
  $logIssue('POST_META_MISMATCH');
  $expKeys=array_count_values(array_column($expectedMeta,'meta_key'));
  $actKeys=array_count_values(array_column($actualMeta,'meta_key'));
  foreach($expKeys as $k=>$n0)if(($actKeys[$k]??0)<$n0)$logIssue('META_KEY_MISSING_'.preg_replace('/[^A-Za-z0-9_]/','_', $k));
  foreach($actKeys as $k=>$n0)if(($expKeys[$k]??0)<$n0)$logIssue('META_KEY_EXTRA_'.preg_replace('/[^A-Za-z0-9_]/','_', $k));
 }
 $d=st_raw($om[$oid],'_aest_delta');
 if(count($d)){
  $deltaCount+=count($d);
  $newD=st_raw($nm[$target],'_anst_delta');
  if($d===$newD){$deltaRawMatches+=count($d);}
  else {$logIssue('QUILL_DELTA_RAW_MISMATCH');}
  foreach($d as $v){$decoded=json_decode($v,true);if(json_last_error()===JSON_ERROR_NONE&&is_array($decoded)&&isset($decoded['ops'])&&is_array($decoded['ops']))$deltaValid++;else $logIssue('QUILL_DELTA_SCHEMA_INVALID');}
 }
 if($p['post_type']==='aest_projeto' && (int)$p['post_author']>0) {
  $owner=(int)$p['post_author'];
  $sz=st_zoom($owner,'_aest_board_zoom_'.$oid);
  $dz=st_zoom($owner,'_anst_board_zoom_'.$target);
  if(count($sz)){$zoomSource+=count($sz);$zoomTarget+=count($dz);if($sz!==$dz)$logIssue('USER_ZOOM_MISMATCH');}
  elseif(count($dz))$logIssue('USER_ZOOM_EXTRA');
 }
 if($p['post_type']!=='aest_projeto'){
  $ref=st_raw($om[$oid],'_aest_project');
  $destref=st_raw($nm[$target],'_anst_project');
  if(count($ref)===1){
   $refId=(int)$ref[0];$targetProject=$map[$refId]??0;
   if(!$targetProject||!isset($old[$refId])||$old[$refId]['post_type']!=='aest_projeto')$logIssue('CHILD_PROJECT_SOURCE_INVALID');
   if(count($destref)!==1||(int)$destref[0]!==$targetProject)$logIssue('CHILD_PROJECT_TARGET_INVALID');
   if(isset($old[$refId])&&(int)$p['post_author']!==(int)$old[$refId]['post_author'])$logIssue('CROSS_OWNER_CHILD_PROJECT');
   if(isset($new[$targetProject])&&(int)$n['post_author']!==(int)$new[$targetProject]['post_author'])$logIssue('CROSS_OWNER_TARGET');
  }else{
   if($p['post_status']==='publish')$logIssue('ACTIVE_CHILD_WITHOUT_PROJECT');
  }
 }
}
foreach($new as $id=>$p){if(!isset($seenTargets[$id]))$logIssue('EXTRA_UNMAPPED_TARGET');}
$sourceFingerprint=hash_final($sourceState);
$rawOldAgain=st_rows($oldTypes);
$stable=count($rawOldAgain)===count($rawOld);
if($stable)foreach($rawOldAgain as $again){
 $id=(int)$again['ID'];
 if(!isset($old[$id])||hash('sha256',serialize([$again,st_meta($id)]))!==hash('sha256',serialize([$old[$id],$om[$id]]))){$stable=false;break;}
}
if(!$stable)$logIssue('SOURCE_CHANGED_DURING_AUDIT');
$active=get_option('active_plugins',[]);
if(!in_array('anthares-studio/anthares-estudio.php',$active,true))$logIssue('CLONE_PLUGIN_INACTIVE');
if(!in_array('anthares-estudio/anthares-estudio.php',$active,true))$logIssue('LEGACY_PLUGIN_INACTIVE');
$writeFlag=(string)get_option('anst_writes_enabled','0');
$cleanupFlag=(string)get_option('anst_trash_cleanup_enabled','0');
if($writeFlag!=='0')$logIssue('WRITE_GATE_ACTIVE');
if($cleanupFlag!=='0')$logIssue('TRASH_CLEANUP_ACTIVE');
$page=get_page_by_path('studio',OBJECT,'page');
if(!$page||$page->post_status!=='private')$logIssue('STUDIO_PAGE_NOT_PRIVATE');
$out=[
 'source_count'=>count($old),'target_count'=>count($new),'mapped'=>count($map),
 'old_types'=>$statsOld,'new_types'=>$statsNew,
 'old_status'=>$statusOld,'new_status'=>$statusNew,
 'source_checksum_match'=>count($old)-($issues['SOURCE_CHECKSUM_MISMATCH']??0),
 'posts_fields_match'=>$fieldsMatch,'posts_meta_match'=>$metaMatch,
 'delta_count'=>$deltaCount,'delta_raw_match'=>$deltaRawMatches,'delta_valid'=>$deltaValid,
 'project_reference_count'=>$projectRefCount,'orphan_references'=>$invalidRef,
 'user_zoom_source'=>$zoomSource,'user_zoom_target'=>$zoomTarget,
 'source_fingerprint'=>$sourceFingerprint,'source_stable'=>$stable,
 'write_flag'=>$writeFlag,'cleanup_flag'=>$cleanupFlag,
 'issues'=>$issues
];
echo "STUDIO_ITEM3_RESULT=".wp_json_encode($out,JSON_UNESCAPED_SLASHES)."\\n";
'''
bootstrap='define("WP_USE_THEMES",false);define("DISABLE_WP_CRON",true);require '+json.dumps(str(root/'wp-load.php'))+';'
process=subprocess.run([phpbin,'-d','display_errors=stderr','-r',bootstrap+audit],
                       capture_output=True,text=True,timeout=95)
if process.returncode!=0:
 print('STUDIO_ITEM3_FAILURE=WP_AUDIT_EXECUTION',flush=True)
 sys.exit(5)
line=next((x[len('STUDIO_ITEM3_RESULT='):] for x in process.stdout.splitlines() if x.startswith('STUDIO_ITEM3_RESULT=')),None)
require(bool(line),'RESULT_MISSING')
result=json.loads(line)
# Output counts/technical field codes only; never titles, text, Quill Delta, users or passwords.
print('STUDIO_ITEM3_RESULT='+json.dumps(result,sort_keys=True,ensure_ascii=True),flush=True)
require(result['source_count']==71 and result['target_count']==71,'COUNTS_NOT_71')
require(result['mapped']==71,'MAPPING_INCOMPLETE')
require(result['old_status'].get('publish')==40 and result['old_status'].get('trash')==31,'SOURCE_STATUS_MISMATCH')
require(result['new_status'].get('publish')==40 and result['new_status'].get('trash')==31,'TARGET_STATUS_MISMATCH')
require(result['delta_count']==7 and result['delta_raw_match']==7 and result['delta_valid']==7,'QUILL_NOT_EXACT')
require(result['source_stable'] is True,'SOURCE_SNAPSHOT_CHANGED')
require(result['write_flag']=='0' and result['cleanup_flag']=='0','FLAGS_UNSAFE')
require(not result['issues'],'INTEGRITY_ISSUES_PRESENT')
require(result['posts_fields_match']==71 and result['posts_meta_match']==71,'DATA_MISMATCH')
require(sha(src)=='13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf','LEGACY_CHANGED_DURING_AUDIT')
require(sha(dst)=='042863a385c5fb8df359c52591bc63a0e033bd9b37e2f8cd8c3992b6d71ad5b7','STUDIO_CHANGED_DURING_AUDIT')
print('STUDIO_ITEM3_INTEGRITY_PROVEN=1',flush=True)
"""
def require(condition,reason):
    if not condition: raise RuntimeError(reason)

def main():
    require(os.getenv('GITHUB_REPOSITORY')==REPO,'WRONG_REPO')
    require(os.getenv('GITHUB_REF')==BRANCH,'WRONG_BRANCH')
    require(os.getenv('GITHUB_EVENT_NAME')=='push','WRONG_EVENT')
    parent=Path(__file__).with_name('studio-css-live-once.py')
    module_spec=importlib.util.spec_from_file_location('anthares_studio_ssh',parent)
    module=importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    token=os.getenv('GITLAB_TOKEN','')
    require(bool(token),'PROTECTED_CREDENTIAL_BRIDGE_UNAVAILABLE')
    key,host,port,user=module.get_ssh_config(token)
    with tempfile.TemporaryDirectory(prefix='studio-g3-audit-') as tmp:
        folder=Path(tmp)
        keypath=folder/'key';keypath.write_text(key);keypath.chmod(0o600)
        hostfile=folder/'known_hosts'
        hostfile.write_text('anthares-studio-g3-audit '+HOST_KEY+'\n');hostfile.chmod(0o600)
        ssh=['ssh','-T','-i',str(keypath),'-p',port,'-o','IdentitiesOnly=yes',
             '-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=12',
             '-o','UserKnownHostsFile='+str(hostfile),
             '-o','HostKeyAlias=anthares-studio-g3-audit',f'{user}@{host}',
             '/opt/alt/python311/bin/python3.11 -']
        process=subprocess.run(ssh,input=REMOTE,text=True,capture_output=True,timeout=140)
        for line in process.stdout.splitlines():
            if line.startswith(('STUDIO_ITEM3_RESULT=','STUDIO_ITEM3_FAILURE=','STUDIO_ITEM3_INTEGRITY_PROVEN=')):
                print(line,flush=True)
        if process.returncode!=0:
            import re
            tail=(process.stderr.strip().splitlines() or ['UNKNOWN_REMOTE_ERROR'])[-1]
            m=re.search(r'^(?:RuntimeError|ValueError|TypeError|SyntaxError|NameError|IndentationError|AssertionError):\\s*(.{1,180})
        require('STUDIO_ITEM3_INTEGRITY_PROVEN=1' in process.stdout,'INTEGRITY_SUCCESS_SIGNAL_MISSING')

if __name__=='__main__':
    main()
,tail)
            label=(m.group(1) if m else ('SSH_AUTH_FAILED' if 'Permission denied' in process.stderr else 'REMOTE_RUNTIME_ERROR'))
            label=re.sub(r'[^A-Za-z0-9 _:-]','_',label)[:140]
            print('STUDIO_ITEM3_REMOTE_DIAGNOSTIC='+label,flush=True)
        require(process.returncode==0,'REMOTE_INTEGRITY_AUDIT_FAILED')
        require('STUDIO_ITEM3_INTEGRITY_PROVEN=1' in process.stdout,'INTEGRITY_SUCCESS_SIGNAL_MISSING')

if __name__=='__main__':
    main()
