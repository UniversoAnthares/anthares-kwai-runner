<?php
/**
 * C009–C022/C024: REST acceptance on disposable WordPress only.
 * Must be copied to /tmp in the isolated Docker container, never to production.
 * Synthetic user credentials and content; PASS-only diagnostics.
 */
if (!defined('WP_CLI') || !WP_CLI) throw new RuntimeException('G4_WPCLI_REQUIRED');
if (getenv('STUDIO_G4_SYNTHETIC_ACCEPTANCE') !== '1') throw new RuntimeException('G4_ISOLATED_ENV_REQUIRED');
if (parse_url(home_url('/'),PHP_URL_HOST)!=='127.0.0.1') throw new RuntimeException('G4_PRODUCTION_REFUSED');
global $wpdb;
$old_count=(int)$wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type IN ('aest_projeto','aest_nota','aest_capitulo','aest_cartao')");
$old_fingerprint=hash('sha256',serialize($wpdb->get_results(
    "SELECT ID,post_type,post_status,post_author,post_title,post_content FROM {$wpdb->posts} WHERE post_type IN ('aest_projeto','aest_nota','aest_capitulo','aest_cartao') ORDER BY ID",ARRAY_A)));
$codes=[];
function g4ok($value,$id,$label='') {
 global $codes;
 if (!$value) {
  fwrite(STDERR,"G4_FAILED_CASE={$id} REASON={$label}\n");
  throw new RuntimeException("G4_CASE_FAILURE_{$id}_{$label}");
 }
 $codes[$id]=($codes[$id]??0)+1;
}
function g4request($user,$method,$route,$args=[]) {
 wp_set_current_user((int)$user);
 $request=new WP_REST_Request($method,'/anthares-studio/v1'.$route);
 foreach ($args as $name=>$val) $request->set_param($name,$val);
 $response=rest_do_request($request);
 if(is_wp_error($response))return ['status'=>($response->get_error_data()['status']??500),'data'=>['code'=>$response->get_error_code()]];
 return ['status'=>$response->get_status(),'data'=>$response->get_data()];
}
function g4success($r,$code) {g4ok($r['status']>=200&&$r['status']<300,$code,'HTTP_'.$r['status']);return $r['data'];}
function g4code($r,$status,$code) {g4ok((int)$r['status']===$status,$code,'EXPECTED_'.$status.'_GOT_'.$r['status']);}
$userA=get_user_by('login','g4synthetic');
g4ok($userA instanceof WP_User,'C002','SYNTHETIC_ADMIN_MISSING');
$uid=(int)$userA->ID;
$external=wp_create_user('g4second_'.wp_generate_password(8,false,false),'qa-only-nonproduction','synthetic2@example.invalid');
g4ok(!is_wp_error($external),'C024','SYNTHETIC_OTHER_CREATE');
get_user_by('id',$external)->set_role('administrator');
$anon=0;
$outsider=wp_create_user('g4subscriber_'.wp_generate_password(8,false,false),'qa-only-nonproduction','synthetic3@example.invalid');
g4ok(!is_wp_error($outsider),'C024','SYNTHETIC_SUBSCRIBER_CREATE');
get_user_by('id',$outsider)->set_role('subscriber');
rest_get_server();
g4code(g4request($anon,'GET','/bootstrap'),401,'C021');
g4code(g4request($outsider,'GET','/bootstrap'),403,'C024');
update_option('anst_writes_enabled','0',false);
g4code(g4request($uid,'POST','/projects',['mode'=>'sem-ideia','title'=>'SHOULD_NOT_WRITE']),423,'C020');
update_option('anst_writes_enabled','1',false);
g4ok(anst_writes_enabled(),'C020','ISOLATED_WRITE_GATE');
$project=g4success(g4request($uid,'POST','/projects',['mode'=>'sem-ideia','title'=>'Projeto sintético α']), 'C009');
$project=(int)$project['id'];
g4ok($project>0 && get_post($project)->post_author==$uid && get_post($project)->post_type==='anst_projeto','C009','PROJECT_PERSISTENCE');
$projectB=g4success(g4request($external,'POST','/projects',['mode'=>'manuscrito','title'=>'Projeto sintético β']), 'C009');
$projectB=(int)$projectB['id'];
g4ok($projectB!==$project,'C020','OWNER_PROJECT_SEPARATION');
g4code(g4request($external,'POST',"/projects/$project",['title'=>'RAID']),404,'C024');
g4code(g4request($uid,'POST',"/projects/$projectB",['title'=>'RAID']),404,'C024');
g4code(g4request($uid,'GET',"/bootstrap",['project'=>$projectB]),404,'C024');
g4success(g4request($uid,'POST',"/projects/$project",['title'=>'Projeto QA renomeado','topic'=>'Antropologia']), 'C009');
g4ok(get_post($project)->post_title==='Projeto QA renomeado','C009','TITLE_RENAME');
$idea=g4success(g4request($uid,'POST','/notes',['text'=>'Ideia global sintética','kind'=>'idea','project'=>0]),'C010');
$ideaID=(int)$idea['id'];
g4ok((int)anst_meta_get($ideaID,'_anst_project',true)===0,'C010','GLOBAL_IDEA_PERSISTENCE');
$research=g4success(g4request($uid,'POST','/notes',['text'=>'Pesquisa sintética','kind'=>'research','project'=>$project]),'C010');
g4ok((int)anst_meta_get($research['id'],'_anst_project',true)===$project,'C010','PROJECT_NOTE_ASSOC');
g4code(g4request($external,'POST','/notes',['text'=>'Cross owner','project'=>$project]),404,'C024');
$col=g4success(g4request($uid,'POST',"/projects/$project/columns",['name'=>'Cenas']), 'C011');
g4ok(count($col['columns'])>=4,'C011','COLUMN_CREATED');
$lastCol=end($col['columns']);$colId=(string)$lastCol['id'];
$card=g4success(g4request($uid,'POST','/cards',['project'=>$project,'text'=>'Cartão sintético','column'=>$colId]),'C011');
$cardID=(int)$card['id'];
g4success(g4request($uid,'POST',"/cards/$cardID",['text'=>'Cartão editado','color'=>'blue','notes'=>'Observações e versões']), 'C011');
g4ok(anst_meta_get($cardID,'_anst_color',true)==='blue','C011','CARD_COLOR_PERSISTED');
g4success(g4request($uid,'POST','/cards/reorder',['project'=>$project,'items'=>[['id'=>$cardID,'column'=>'trama','rank'=>0]]]),'C011');
g4ok(anst_meta_get($cardID,'_anst_column',true)==='trama','C011','CARD_REORDER');
g4success(g4request($uid,'POST',"/projects/$project/zoom",['zoom'=>110]),'C011');
g4ok(anst_board_zoom_read($project)===110,'C011','ZOOM_PERSISTED');
g4code(g4request($external,'POST',"/cards/$cardID",['text'=>'Cross-owner card']),404,'C024');
$es=g4success(g4request($uid,'POST',"/projects/$project/elements",['revision'=>0,'action'=>'folder_add','name'=>'Personagens']), 'C012')['elements'];
$folder=$es['folders'][0]['id'];
$es=g4success(g4request($uid,'POST',"/projects/$project/elements",['revision'=>$es['revision'],'action'=>'folder_rename','folder'=>$folder,'name'=>'Personagens centrais']), 'C012')['elements'];
$es=g4success(g4request($uid,'POST',"/projects/$project/elements",['revision'=>$es['revision'],'action'=>'item_add','folder'=>$folder,'title'=>'Capitão','notes'=>'Registro sintético','attrs'=>['funcao'=>'protagonista']]),'C012')['elements'];
$item=$es['folders'][0]['items'][0]['id'];
$es=g4success(g4request($uid,'POST',"/projects/$project/elements",['revision'=>$es['revision'],'action'=>'item_add','folder'=>$folder,'title'=>'Tenente','attrs'=>['funcao'=>'coadjuvante']]),'C012')['elements'];
$otherItem=$es['folders'][0]['items'][1]['id'];
$bad=g4request($uid,'POST',"/projects/$project/elements",['revision'=>$es['revision']-1,'action'=>'item_update','folder'=>$folder,'item'=>$item,'title'=>'Capt.']);
g4code($bad,409,'C022');
$es=g4success(g4request($uid,'POST',"/projects/$project/elements",['revision'=>$es['revision'],'action'=>'item_update','folder'=>$folder,'item'=>$item,'title'=>'Capitão alterado','notes'=>'Persistência de ficha','attrs'=>['funcao'=>'protagonista','idade'=>'52'],'links'=>[$otherItem]]),'C012')['elements'];
g4ok($es['folders'][0]['items'][0]['links']==[$otherItem],'C012','LINK_PERSISTENCE');
g4code(g4request($uid,'POST',"/projects/$project/elements",['revision'=>$es['revision'],'action'=>'item_update','folder'=>$folder,'item'=>$item,'title'=>'Link inválido','links'=>['i_missing']]),400,'C012');
$ev=g4success(g4request($uid,'POST',"/projects/$project/elements/versions",['action'=>'snapshot']),'C012');
$evId=$ev['versions'][0]['id'];
$es=g4success(g4request($uid,'POST',"/projects/$project/elements",['revision'=>$es['revision'],'action'=>'folder_rename','folder'=>$folder,'name'=>'Outros personagens']),'C012')['elements'];
$rest=g4success(g4request($uid,'POST',"/projects/$project/elements/versions",['action'=>'restore','version'=>$evId,'revision'=>$es['revision']]),'C017');
g4ok($rest['elements']['folders'][0]['name']==='Personagens centrais','C017','ELEMENT_HISTORY_RESTORED');
g4ok(count(g4success(g4request($uid,'GET',"/projects/$project/elements/versions"),'C017')['versions'])>1,'C017','ELEMENT_RESTORABLE_SNAPSHOTS');
$blank=anst_unlock_read($project);
g4ok($blank['version']===2,'C013','UNLOCK_V2');
for($step=0;$step<=10;$step++){
 $blank['step']=$step;
 if($step===10){$blank['premise']='Premissa 1';$blank['logline']='Logline 1';$blank['storyline']='Trama 1';$blank['outline']='Outline 1';}
 $out=g4success(g4request($uid,'POST',"/projects/$project/unlock",['state'=>$blank,'complete'=>$step===10]), 'C013');
 g4ok($out['state']['revision']===$blank['revision']+1,'C013','STEP_REVISION_'.$step);
 $blank=$out['state'];
}
g4ok($blank['completed']===true && $blank['step']===10,'C013','UNLOCK_COMPLETED');
g4code(g4request($uid,'POST',"/projects/$project/unlock",['state'=>$blank+['revision'=>0]]),409,'C022');
$chapterA=g4success(g4request($uid,'POST','/chapters',['project'=>$project,'title'=>'Capítulo um']),'C014');
$chapterA=(int)$chapterA['id'];
$chapterB=g4success(g4request($uid,'POST','/chapters',['project'=>$project,'title'=>'Capítulo dois']),'C014');
$chapterB=(int)$chapterB['id'];
g4success(g4request($uid,'POST','/chapters/reorder',['project'=>$project,'ids'=>[$chapterB,$chapterA]]),'C014');
g4ok((int)get_post($chapterB)->menu_order===0,'C014','CHAPTER_ORDER');
g4success(g4request($uid,'POST',"/chapters/$chapterA/structure",['model'=>'three_acts','stage'=>'setup','revision'=>0]),'C014');
$start=anst_chapter_data(get_post($chapterA));$oldHash=$start['contentHash'];
$delta1=['ops'=>[['insert'=>"Olá, capítulo 1! 😄\n",'attributes'=>['bold'=>true]],['insert'=>'Itálico','attributes'=>['italic'=>true]],['insert'=>"\n"]]];
$updated=g4success(g4request($uid,'POST',"/chapters/$chapterA",['delta'=>$delta1,'expected_hash'=>$oldHash]),'C015');
g4ok(isset($updated['contentHash']) && $updated['contentHash']!==$oldHash,'C015','DELTA_HASH_CHANGED');
$stored=anst_chapter_data(get_post($chapterA));
g4ok($stored['delta']===$delta1,'C015','QUILL_UNICODE_ATTRIBUTES');
g4code(g4request($external,'POST',"/chapters/$chapterA",['delta'=>$delta1,'expected_hash'=>$oldHash]),404,'C024');
$delta2=['ops'=>[['insert'=>"Segundo conteúdo 😄 com acento e colagem: café.\n"]]];
g4success(g4request($uid,'POST',"/chapters/$chapterA",['delta'=>$delta2,'expected_hash'=>$updated['contentHash']]),'C016');
$stale=g4request($uid,'POST',"/chapters/$chapterA",['delta'=>['ops'=>[['insert'=>'Concorrente!']]],'expected_hash'=>$updated['contentHash']]);
g4code($stale,409,'C022');
$again=g4success(g4request($uid,'GET','/bootstrap',['project'=>$project]),'C016');
$matches=array_values(array_filter($again['chapters'],static fn($x)=>(int)$x['id']===$chapterA));
g4ok(count($matches)===1 && $matches[0]['delta']===$delta2,'C016','READ_AFTER_SAVE_MATCH');
g4code(g4request($uid,'POST',"/chapters/$chapterA",['delta'=>['invalid'=>'x'],'expected_hash'=>$matches[0]['contentHash']]),400,'C021');
$huge=['ops'=>[['insert'=>str_repeat('A',2000010)]]];
g4code(g4request($uid,'POST',"/chapters/$chapterA",['delta'=>$huge,'expected_hash'=>$matches[0]['contentHash']]),413,'C021');
$versions=g4success(g4request($uid,'POST',"/chapters/$chapterA/versions",['action'=>'snapshot']),'C017');
g4ok(count($versions['versions'])>=1,'C017','MANUAL_SNAPSHOT');
$vId=$versions['versions'][0]['id'];
$delta3=['ops'=>[['insert'=>"Texto futuro\n"]]];
$after3=g4success(g4request($uid,'POST',"/chapters/$chapterA",['delta'=>$delta3,'expected_hash'=>$matches[0]['contentHash']]),'C017');
g4code(g4request($uid,'POST',"/chapters/$chapterA/versions",['action'=>'restore','version'=>$vId,'expected_hash'=>$matches[0]['contentHash']]),409,'C022');
g4success(g4request($uid,'POST',"/chapters/$chapterA/versions",['action'=>'restore','version'=>$vId,'expected_hash'=>$after3['contentHash']]),'C017');
g4ok(anst_chapter_data(get_post($chapterA))['delta']===$delta2,'C017','CHAPTER_VERSION_RESTORED');
$rev=g4success(g4request($uid,'GET',"/projects/$project/review"),'C018')['review'];
$rev=g4success(g4request($uid,'POST',"/projects/$project/review",['revision'=>$rev['revision'],'action'=>'create','chapter'=>$chapterA,'type'=>'trama','priority'=>'alta','note'=>'Revisar continuidade sintética','quote'=>'Segundo conteúdo','offset'=>1]),'C018')['review'];
g4ok(count($rev['tasks'])===1,'C018','REVIEW_TASK_PERSISTED');
$taskId=$rev['tasks'][0]['id'];
$rev=g4success(g4request($uid,'POST',"/projects/$project/review",['revision'=>$rev['revision'],'action'=>'status','item'=>$taskId,'status'=>'resolvida']),'C018')['review'];
g4ok($rev['tasks'][0]['status']==='resolvida','C018','REVIEW_TASK_RESOLVED');
g4code(g4request($uid,'POST',"/projects/$project/review",['revision'=>$rev['revision']-1,'action'=>'checklist','type'=>'trama','checked'=>true]),409,'C022');
$rev=g4success(g4request($uid,'POST',"/projects/$project/review",['revision'=>$rev['revision'],'action'=>'checklist','type'=>'trama','checked'=>true]),'C018')['review'];
g4ok($rev['checklist']['trama']===true,'C018','REVIEW_CHECKLIST');
$otherReview=g4request($external,'GET',"/projects/$project/review");
g4code($otherReview,404,'C024');
$beforeTrash=g4success(g4request($uid,'GET','/trash'),'C019');
g4success(g4request($uid,'DELETE',"/projects/$project",['title'=>'Projeto QA renomeado']),'C019');
g4ok(get_post_status($project)==='trash','C019','PROJECT_TO_TRASH');
g4ok(get_post_status($chapterA)==='trash' && get_post_status($cardID)==='trash','C019','CASCADE_TO_TRASH');
g4code(g4request($external,'POST',"/trash/$project/restore"),404,'C024');
g4success(g4request($uid,'POST',"/trash/$project/restore"),'C019');
g4ok(get_post_status($project)==='publish' && get_post_status($chapterA)==='publish' && get_post_status($cardID)==='publish','C019','CASCADE_RESTORED');
$old_count_after=(int)$wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type IN ('aest_projeto','aest_nota','aest_capitulo','aest_cartao')");
$after_fingerprint=hash('sha256',serialize($wpdb->get_results(
    "SELECT ID,post_type,post_status,post_author,post_title,post_content FROM {$wpdb->posts} WHERE post_type IN ('aest_projeto','aest_nota','aest_capitulo','aest_cartao') ORDER BY ID",ARRAY_A)));
g4ok($old_count_after===$old_count && hash_equals($old_fingerprint,$after_fingerprint),'C020','LEGACY_ISOLATED');
update_option('anst_writes_enabled','0',false);
g4code(g4request($uid,'POST',"/projects/$project",['title'=>'MUST_BE_LOCKED']),423,'C020');
g4ok(!anst_writes_enabled(),'C020','WRITE_LOCK_RESTORED');
ksort($codes);
foreach($codes as $id=>$count)fwrite(STDOUT,"G4_FUNCTION_CASE={$id} PASS_ASSERTIONS={$count}\n");
fwrite(STDOUT,"G4_FUNCTION_LEGACY_UNCHANGED=1\n");
fwrite(STDOUT,"G4_FUNCTION_SYNTHETIC_ONLY=1\n");
fwrite(STDOUT,"G4_FUNCTION_ACCEPTANCE_PASS=1\n");
