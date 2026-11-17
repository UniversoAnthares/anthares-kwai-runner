<?php
/**
 * Plugin Name: Anthares Studio — Cópia Isolada de Escrita
 * Description: Núcleo privado de projetos literários integrado ao cabeçalho do Universo Anthares.
 * Version: 0.7.8-staging
 * Requires PHP: 8.0
 * Text Domain: anthares-studio
 */
if (!defined('ABSPATH')) { exit; }
// A ativação do repositório ACF exige também anst_acf_runtime_enabled=1; OFF mantém o legado.
if (!defined('ANST_ACF_RUNTIME_APPROVED')) { define('ANST_ACF_RUNTIME_APPROVED', true); }
// Camada de campos ACF: modo legado até autorização dupla e migração verificada.
require_once __DIR__ . '/includes/acf/class-anst-acf-repository.php';

function anst_is_anthares_role() {
    $user=wp_get_current_user();
    return $user && $user->exists() && in_array('anthares',(array)$user->roles,true);
}
function anst_can_manage_lessons() {return anst_is_anthares_role();}
function anst_lesson_settings() {
    $stored=anst_acf_lesson_option_get();
    $names=['mural','assunto','premissa','logline','storyline','tema','outline'];
    $out=[];
    foreach($names as $key){$out[$key]=is_array($stored)?(string)($stored[$key]??''):'';}
    return $out;
}
function anst_can_use() {
    $user = wp_get_current_user();
    if (!$user || !$user->exists()) return false;
    $id = (int) $user->ID;
    return in_array('administrator', (array) $user->roles, true)
        || $id === 106
        || current_user_can('manage_options')
        || anst_is_anthares_role()
        || (bool) apply_filters('anthares_estudio_paid_access', false, $id);
}
function anst_register_types() {
    foreach (['anst_projeto' => 'Projetos do Estúdio', 'anst_nota' => 'Notas do Estúdio', 'anst_capitulo' => 'Capítulos do Estúdio', 'anst_cartao' => 'Cartões do Mural'] as $type => $label) {
        register_post_type($type, [
            'label' => $label, 'public' => false, 'publicly_queryable' => false,
            'exclude_from_search' => true, 'show_ui' => false, 'show_in_rest' => false,
            'supports' => ['title', 'editor', 'author'], 'capability_type' => 'post',
        ]);
    }
}
add_action('init', 'anst_register_types');
function anst_front_assets() {
    if (!is_page('studio')) { return; }
    $url = plugin_dir_url(__FILE__);
    wp_enqueue_style('anst-ui', $url . 'assets/estudio.css', [], (string) filemtime(__DIR__ . '/assets/estudio.css'));
    wp_enqueue_style('anst-dark', $url . 'assets/estudio-dark.css', ['anst-ui'], (string) filemtime(__DIR__ . '/assets/estudio-dark.css'));
    wp_enqueue_style('anst-g6-nav', $url . 'assets/studio-g6-navigation.css', ['anst-ui', 'anst-dark'], (string) filemtime(__DIR__ . '/assets/studio-g6-navigation.css'));
    // O editor só é carregado quando um capítulo é aberto.
    wp_enqueue_script('anst-ui', $url . 'assets/estudio.js', [], (string) filemtime(__DIR__ . '/assets/estudio.js'), true);
    wp_add_inline_script('anst-ui', 'window.AntharesEstudio=' . wp_json_encode([
        'rest' => esc_url_raw(rest_url('anthares-studio/v1/')),
        'nonce' => wp_create_nonce('wp_rest'),
        'hotmart' => 'https://consumer.hotmart.com/',
        'name' => wp_get_current_user()->display_name,
        'canManageLessons' => anst_can_manage_lessons(),
        'lessonVideos' => anst_lesson_settings(),
        'quillJs' => $url . 'assets/vendor/quill-2.0.3.js',
        'quillCss' => $url . 'assets/vendor/quill-2.0.3.snow.css',
    ]) . ';', 'before');
}
add_action('wp_enqueue_scripts', 'anst_front_assets');
add_filter('body_class', function($classes){
 if (is_page('studio')) {
  // Identidade visual estável e exclusiva do novo Studio.
  $classes[] = 'anst-studio-page';
  if (!is_user_logged_in() || !anst_can_use()) $classes[] = 'aest-access-gate';
 }
 return $classes;
});
function anst_shortcode() {
    if (!is_user_logged_in()) {
        return '<div class="aest-access"><h2>Estúdio de Escrita</h2><p>Entre na sua conta Anthares para acessar seus projetos.</p><a class="aest-btn aest-primary" href="' . esc_url(wp_login_url(get_permalink())) . '">Entrar na minha conta</a></div>';
    }
    if (!anst_can_use()) {
        return '<div class="aest-access"><h2>Estúdio de Escrita</h2><p>O acesso às ferramentas é exclusivo para clientes com direito de uso adquirido pelo curso na Hotmart ou diretamente no Anthares.</p><p>A vinculação comercial está em implantação. Seu acesso será reconhecido quando essa integração estiver concluída.</p></div>';
    }
    // Dados privados de leitura carregados uma só vez, no mesmo HTML,
    // sem aguardar uma segunda requisição REST após a abertura da página.
    $initial = anst_bootstrap(true)->get_data();
    wp_add_inline_script('anst-ui', 'window.AntharesEstudio.initial=' .
        wp_json_encode($initial, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT) . ';', 'before');
    return '<div id="anthares-estudio-root" class="aest" aria-live="polite"></div>';
}
add_shortcode('anthares_studio', 'anst_shortcode');
// Evita que material privado do autor seja armazenado no cache público.
add_action('template_redirect', function () {
    if (is_page('studio') && is_user_logged_in()) {
        if (!defined('DONOTCACHEPAGE')) { define('DONOTCACHEPAGE', true); }
        nocache_headers();
    }
}, 0);
function anst_writes_enabled() { return (string)get_option('anst_writes_enabled','0')==='1'; }
function anst_permission($request=null) {
    if (!anst_can_use()) { return false; }
    $method=$request instanceof WP_REST_Request?$request->get_method():'GET';
    if ($method!=='GET' && !anst_writes_enabled()) {
        return new WP_Error('anst_staging_locked','O Estúdio está em homologação somente para leitura.',['status'=>423]);
    }
    return true;
}
function anst_own($id, $type) {
    $post = get_post(absint($id));
    return $post && $post->post_type === $type && (int) $post->post_author === get_current_user_id() ? $post : false;
}
function anst_children($type, $project = null, $kind = null) {
    $args = ['post_type' => $type, 'post_status' => 'publish', 'author' => get_current_user_id(), 'posts_per_page' => 250, 'orderby' => 'date', 'order' => 'DESC'];
    $meta = [];
    if ($project !== null) { $meta[] = ['key' => anst_meta_query_key($type,'_anst_project'), 'value' => (string) absint($project)]; }
    if ($kind !== null) { $meta[] = ['key' => anst_meta_query_key($type,'_anst_kind'), 'value' => sanitize_key($kind)]; }
    if ($meta) { $args['meta_query'] = $meta; }
    return get_posts($args);
}
function anst_elements_read($project) {
    $stored=json_decode((string)anst_meta_get(absint($project),'_anst_elements_v1',true),true);
    if(!is_array($stored)||!is_array($stored['folders']??null))return ['revision'=>0,'folders'=>[]];
    return ['revision'=>max(0,(int)($stored['revision']??0)),'folders'=>array_values($stored['folders'])];
}
function anst_elements_update($req) {
    $project=absint($req['id']);
    if(!anst_own($project,'anst_projeto'))
      return new WP_Error('anst_project','Projeto indisponível.',['status'=>404]);
    $state=anst_elements_read($project);
    $beforeState=$state;
    if(!is_numeric($req->get_param('revision'))||(int)$req->get_param('revision')!==$state['revision'])
      return new WP_Error('anst_conflict','Esta lista foi atualizada em outra sessão. Recarregue a página para continuar.',['status'=>409]);
    $action=sanitize_key((string)$req->get_param('action'));
    $folder_id=sanitize_key((string)$req->get_param('folder'));
    $item_id=sanitize_key((string)$req->get_param('item'));
    $folder_index=-1;
    foreach($state['folders'] as $i=>$folder) {
      if(strtolower((string)($folder['id']??''))===$folder_id){$folder_index=$i;break;}
    }
    if($action==='folder_add') {
      $name=trim(sanitize_text_field((string)$req->get_param('name')));
      if($name===''||mb_strlen($name)>65)return new WP_Error('anst_name','Informe um título de até 65 caracteres.',['status'=>400]);
      if(count($state['folders'])>=40)return new WP_Error('anst_limit','Limite de 40 pastas neste projeto.',['status'=>400]);
      foreach($state['folders'] as $folder){
        if(mb_strtolower($folder['name'])===mb_strtolower($name))
          return new WP_Error('anst_duplicate','Já existe uma pasta com esse nome.',['status'=>409]);
      }
      $state['folders'][]=['id'=>'f_'.strtolower(wp_generate_password(12,false,false)),'name'=>$name,'items'=>[]];
    } elseif($action==='folder_rename') {
      if($folder_index<0)return new WP_Error('anst_folder','Pasta não encontrada.',['status'=>404]);
      $name=trim(sanitize_text_field((string)$req->get_param('name')));
      if($name===''||mb_strlen($name)>65)return new WP_Error('anst_name','Informe um título de até 65 caracteres.',['status'=>400]);
      foreach($state['folders'] as $i=>$folder){
        if($i!==$folder_index&&mb_strtolower($folder['name'])===mb_strtolower($name))
          return new WP_Error('anst_duplicate','Já existe uma pasta com esse nome.',['status'=>409]);
      }
      $state['folders'][$folder_index]['name']=$name;
    } elseif($action==='item_add'||$action==='item_update') {
      if($folder_index<0)return new WP_Error('anst_folder','Pasta não encontrada.',['status'=>404]);
      $title=trim(sanitize_text_field((string)$req->get_param('title')));
      $notes=trim(sanitize_textarea_field((string)$req->get_param('notes')));
      if($title===''||mb_strlen($title)>140)return new WP_Error('anst_title','Informe um título de até 140 caracteres.',['status'=>400]);
      if(mb_strlen($notes)>20000)return new WP_Error('anst_notes','A descrição permite até 20.000 caracteres.',['status'=>400]);
      // Fichas têm campos próprios e vínculos estáveis apenas dentro do mesmo projeto.
      $attrs=$req->get_param('attrs');
      if(!is_array($attrs))$attrs=[];
      if($action==='item_update'&&!$req->has_param('attrs'))
        foreach(($state['folders'][$folder_index]['items']??[]) as $it)
          if(($it['id']??'')===$item_id)$attrs=$it['attrs']??[];
      if(count($attrs)>24)return new WP_Error('anst_attrs','Quantidade de campos acima do limite.',['status'=>400]);
      $clean_attrs=[];
      foreach($attrs as $k=>$v){
        $key=sanitize_key((string)$k);
        if($key===''||!preg_match('/^[a-z0-9_]{1,35}$/',$key)||!is_scalar($v)||mb_strlen((string)$v)>5000)
          return new WP_Error('anst_attr','Campo de ficha inválido.',['status'=>400]);
        $clean_attrs[$key]=sanitize_textarea_field((string)$v);
      }
      $links=$req->get_param('links');
      if(!is_array($links))$links=[];
      if($action==='item_update'&&!$req->has_param('links'))
        foreach(($state['folders'][$folder_index]['items']??[]) as $it)
          if(($it['id']??'')===$item_id)$links=$it['links']??[];
      if(count($links)>60)return new WP_Error('anst_links','H? vínculos demais nesta ficha.',['status'=>400]);
      $known_ids=[];
      foreach($state['folders'] as $fold)foreach(($fold['items']??[]) as $entry)
        $known_ids[(string)($entry['id']??'')]=true;
      $clean_links=[];
      foreach($links as $related){
        $rel=sanitize_key((string)$related);
        if(!isset($known_ids[$rel]))return new WP_Error('anst_link','Vínculo inexistente ou fora do projeto.',['status'=>400]);
        if($rel!==$item_id && !in_array($rel,$clean_links,true))$clean_links[]=$rel;
      }
      $items=&$state['folders'][$folder_index]['items'];
      if($action==='item_add') {
        if(count($items)>=250)return new WP_Error('anst_limit','Limite de 250 elementos por pasta.',['status'=>400]);
        $items[]=['id'=>'i_'.strtolower(wp_generate_password(12,false,false)),'title'=>$title,'notes'=>$notes,'attrs'=>$clean_attrs,'links'=>$clean_links];
      }else {
        $found=false;
        foreach($items as &$item){
          if(strtolower((string)($item['id']??''))!==$item_id)continue;
          $item['title']=$title;$item['notes']=$notes;$item['attrs']=$clean_attrs;$item['links']=$clean_links;$found=true;break;
        }unset($item);
        if(!$found)return new WP_Error('anst_item','Elemento não encontrado.',['status'=>404]);
      }unset($items);
    }else {
      return new WP_Error('anst_action','Operação inválida.',['status'=>400]);
    }
    $state['revision']++;
    $encoded=wp_json_encode($state,JSON_UNESCAPED_UNICODE|JSON_INVALID_UTF8_SUBSTITUTE);
    if(!is_string($encoded)||strlen($encoded)>4000000)
      return new WP_Error('anst_size','O material excedeu o limite de armazenamento.',['status'=>413]);
    if($beforeState['revision']>0||count($beforeState['folders'])){
      $copy=anst_elements_snapshot($project,'automatico',false,$beforeState);
      if(is_wp_error($copy))return $copy;
    }
    anst_meta_update($project,'_anst_elements_v1',wp_slash($encoded));
    $saved=anst_elements_read($project);
    if($saved['revision']!==$state['revision']||$saved['folders']!==$state['folders'])
      return new WP_Error('anst_save','Não foi possível confirmar as alterações.',['status'=>503]);
    return rest_ensure_response(['ok'=>true,'elements'=>$saved]);
}
function anst_project_tone($id) {
    $color=(string)anst_meta_get(absint($id),'_anst_project_tone',true);
    return in_array($color,['none','sea','blue','violet','rose','amber','forest','slate'],true)?$color:'none';
}
function anst_project_data($p,$slim=false) {
    if($slim)return [
      'id'=>(int)$p->ID,'title'=>$p->post_title,'created'=>$p->post_date,
      'start'=>(string)anst_meta_get($p->ID,'_anst_start',true),
      'color'=>anst_project_tone($p->ID),'visibility'=>'private',
      'unlock'=>['step'=>(int)(anst_unlock_read($p->ID)['step']??0),
                 'completed'=>(bool)(anst_unlock_read($p->ID)['completed']??false)]
    ];
    return [
        'id' => (int) $p->ID, 'title' => $p->post_title, 'created' => $p->post_date,
        'start' => anst_meta_get($p->ID, '_anst_start', true),
        'color' => anst_project_tone($p->ID),
        'topic' => anst_meta_get($p->ID, '_anst_topic', true),
        'premise' => anst_meta_get($p->ID, '_anst_premise', true),
        'visibility' => 'private', 'unlock' => anst_unlock_read($p->ID),
        'boardColumns'=>anst_board_columns_read($p->ID),
        'legacyImported'=>(bool)anst_meta_get($p->ID,'_anst_legacy_cards_imported',true),
        'boardZoom'=>anst_board_zoom_read($p->ID),
        'elements'=>anst_elements_read($p->ID),
        'review'=>anst_review_read($p->ID),
        'logline' => anst_meta_get($p->ID,'_anst_logline',true),
        'storyline' => anst_meta_get($p->ID,'_anst_storyline',true),
        'theme' => anst_meta_get($p->ID,'_anst_theme',true),
        'thesis' => anst_meta_get($p->ID,'_anst_thesis',true),
        'tone' => anst_meta_get($p->ID,'_anst_tone',true),
        'summary' => anst_meta_get($p->ID,'_anst_summary',true),
        'outline' => anst_meta_get($p->ID,'_anst_outline',true),
    ];
}
function anst_note_data($p) {
    return ['id' => (int) $p->ID, 'text' => $p->post_content,
        'kind' => anst_meta_get($p->ID, '_anst_kind', true),
        'project' => (int) anst_meta_get($p->ID, '_anst_project', true),
        'date' => $p->post_date];
}
/* As partes estruturais são referências privadas aos capítulos reais. */
function anst_structure_stages() {
 return [
  'three_acts'=>['ato1','ato2','ato3'],
  'hero_journey'=>['mundo_comum','chamado','recusa','mentor','limiar','provas','aproximacao','provacao','recompensa','retorno','ressurreicao','elixir']
 ];
}
function anst_structure_state($chapter){
 $raw=anst_meta_get(absint($chapter),'_anst_structure_map_v1',true);
 $stored=is_string($raw)?json_decode($raw,true):null;
 $models=anst_structure_stages();
 $positions=[];
 foreach($models as $model=>$stages){
  $candidate=is_array($stored)?sanitize_key((string)($stored['positions'][$model]??'')):'';
  $positions[$model]=in_array($candidate,$stages,true)?$candidate:'';
 }
 return ['revision'=>is_array($stored)?max(0,(int)($stored['revision']??0)):0,'positions'=>$positions];
}
function anst_structure_update($req){
 $chapter=anst_own($req['id'],'anst_capitulo');
 if(!$chapter)return new WP_Error('anst_chapter','Capítulo indisponível.',['status'=>404]);
 $project=(int)anst_meta_get($chapter->ID,'_anst_project',true);
 if(!anst_own($project,'anst_projeto'))return new WP_Error('anst_project','Projeto indisponível.',['status'=>404]);
 $model=sanitize_key((string)$req->get_param('model'));
 $stage=sanitize_key((string)$req->get_param('stage'));
 $models=anst_structure_stages();
 if(!array_key_exists($model,$models)||($stage!==''&&!in_array($stage,$models[$model],true)))
  return new WP_Error('anst_stage','Etapa estrutural inválida.',['status'=>400]);
 $current=anst_structure_state($chapter->ID);
 if(!is_numeric($req->get_param('revision'))||(int)$req->get_param('revision')!==$current['revision'])
  return new WP_Error('anst_conflict','O vínculo foi alterado em outra sessão. Atualize a página e tente novamente.',['status'=>409]);
 $current['positions'][$model]=$stage;$current['revision']++;
 $json=wp_json_encode($current,JSON_UNESCAPED_UNICODE);
 if(!is_string($json)||!anst_meta_update($chapter->ID,'_anst_structure_map_v1',wp_slash($json)))
  return new WP_Error('anst_write','Falha ao gravar a posição estrutural.',['status'=>503]);
 $saved=anst_structure_state($chapter->ID);
 if($saved!==$current)return new WP_Error('anst_verify','A posição não foi confirmada.',['status'=>503]);
 return rest_ensure_response(['ok'=>true,'id'=>(int)$chapter->ID,'structure'=>$saved]);
}


/** Uma ordem compartilhada entre Manuscrito, Três atos e Jornada do herói. */
function anst_reorder_chapters($req){
 $project=absint($req->get_param('project'));
 if(!anst_own($project,'anst_projeto'))return new WP_Error('anst_project','Projeto indisponível.',['status'=>404]);
 $ids=$req->get_param('ids');
 if(!is_array($ids)||count($ids)>250)return new WP_Error('anst_order','Ordem inválida.',['status'=>400]);
 $actual=anst_children('anst_capitulo',$project);
 $expected=array_map(static fn($x)=>(int)$x->ID,$actual);
 $sorted=array_map('absint',$ids);
 sort($expected,SORT_NUMERIC);$check=$sorted;sort($check,SORT_NUMERIC);
 if($check!==$expected)return new WP_Error('anst_order','A lista foi alterada. Atualize antes de reorganizar.',['status'=>409]);
 foreach($sorted as $i=>$id){
  if((int)get_post($id)->menu_order!==$i){
   $result=wp_update_post(['ID'=>$id,'menu_order'=>$i],true);
   if(is_wp_error($result))return $result;
  }
 }
 $confirmed=anst_children('anst_capitulo',$project);
 $map=[];
 foreach($confirmed as $row)$map[(int)$row->ID]=(int)$row->menu_order;
 foreach($sorted as $i=>$id)if(($map[$id]??-1)!==$i)
  return new WP_Error('anst_verify','A ordem não foi confirmada.',['status'=>503]);
 return rest_ensure_response(['ok'=>true,'ids'=>$sorted]);
}

function anst_chapter_data($p) {
    $raw = (string) anst_meta_get($p->ID, '_anst_delta', true);
    $delta = json_decode($raw, true);
    return ['id' => (int) $p->ID, 'title' => $p->post_title, 'project' => (int) anst_meta_get($p->ID, '_anst_project', true),
        'delta' => is_array($delta) ? $delta : ['ops' => [['insert' => "\n"]]],
        'contentHash' => hash('sha256', $p->post_title . "\0" . $raw),
        'modified' => $p->post_modified, 'order' => (int) $p->menu_order,
        'structure'=>anst_structure_state($p->ID)];
}

function anst_board_columns_read($id){
    $stored=json_decode((string)anst_meta_get($id,'_anst_board_columns',true),true);
    $cols=is_array($stored)&&count($stored)?$stored:[
        ['id'=>'soltas','name'=>'Título'],
        ['id'=>'desenvolvimento','name'=>'Título'],
        ['id'=>'trama','name'=>'Título']
    ];
    // Conservar IDs, ordem e cartões; substituir só os três rótulos predefinidos.
    $defaults=['soltas'=>'Ideias soltas','desenvolvimento'=>'Em desenvolvimento','trama'=>'Na trama'];
    $changed=false;
    foreach($cols as &$col){
        if(isset($col['id'],$col['name'],$defaults[$col['id']]) &&
           $col['name']===$defaults[$col['id']]){
            $col['name']='Título';$changed=true;
        }
    }unset($col);
    if($changed){anst_meta_update($id,'_anst_board_columns',wp_slash(wp_json_encode($cols,JSON_UNESCAPED_UNICODE)));}
    return $cols;
}
function anst_card_data($p){
 return ['id'=>(int)$p->ID,'project'=>(int)anst_meta_get($p->ID,'_anst_project',true),
  'text'=>$p->post_content,'column'=>anst_meta_get($p->ID,'_anst_column',true)?:'soltas',
  'rank'=>(int)anst_meta_get($p->ID,'_anst_rank',true),
  'color'=>anst_meta_get($p->ID,'_anst_color',true)?:'none',
  'notes'=>(string)anst_meta_get($p->ID,'_anst_card_notes',true)];
}
function anst_card_create($req){
 $project=absint($req->get_param('project'));
 if(!anst_own($project,'anst_projeto'))return new WP_Error('anst_missing','Projeto indisponível.',['status'=>404]);
 $text=trim(sanitize_textarea_field((string)$req->get_param('text')));
 if($text===''||mb_strlen($text)>4000)return new WP_Error('anst_text','Escreva uma anotação de até 4000 caracteres.',['status'=>400]);
 $col=sanitize_text_field((string)$req->get_param('column'));
 if(!in_array($col,array_column(anst_board_columns_read($project),'id'),true))
   return new WP_Error('anst_column','Coluna inválida.',['status'=>400]);
 $cards=anst_children('anst_cartao',$project);
 $id=wp_insert_post(['post_type'=>'anst_cartao','post_status'=>'publish','post_author'=>get_current_user_id(),
    'post_title'=>mb_substr($text,0,80),'post_content'=>$text],true);
 if(is_wp_error($id))return $id;
 anst_meta_update($id,'_anst_project',$project);
 anst_meta_update($id,'_anst_column',$col);
 anst_meta_update($id,'_anst_rank',count($cards));
 anst_meta_update($id,'_anst_card_notes','');
 return rest_ensure_response(anst_card_data(get_post($id)));
}
function anst_card_update($req){
 $p=anst_own($req['id'],'anst_cartao');
 if(!$p||!anst_own(anst_meta_get($p->ID,'_anst_project',true),'anst_projeto'))
  return new WP_Error('anst_missing','Cartão indisponível.',['status'=>404]);
 if($req->has_param('text')){
   $text=trim(sanitize_textarea_field((string)$req->get_param('text')));
   if($text===''||mb_strlen($text)>4000)return new WP_Error('anst_text','Texto inválido.',['status'=>400]);
   wp_update_post(['ID'=>$p->ID,'post_content'=>$text,'post_title'=>mb_substr($text,0,80)]);
 }
 if($req->has_param('notes')){
   $raw=$req->get_param('notes');
   if(!is_string($raw)||mb_strlen($raw)>30000)
     return new WP_Error('anst_notes','O bloco de notas permite até 30.000 caracteres.',['status'=>400]);
   anst_meta_update($p->ID,'_anst_card_notes',sanitize_textarea_field($raw));
 }
 if($req->has_param('color')){
   $color=sanitize_key($req->get_param('color'));
   if(!in_array($color,['none','yellow','blue','green','pink'],true))
      return new WP_Error('anst_color','Cor inválida.',['status'=>400]);
   anst_meta_update($p->ID,'_anst_color',$color);
 }
 return rest_ensure_response(anst_card_data(get_post($p->ID)));
}
function anst_card_delete($req){
 $p=anst_own($req['id'],'anst_cartao');
 if(!$p||!anst_own(anst_meta_get($p->ID,'_anst_project',true),'anst_projeto'))
    return new WP_Error('anst_missing','Cartão indisponível.',['status'=>404]);
 wp_trash_post($p->ID);
 return rest_ensure_response(['ok'=>true]);
}
function anst_cards_reorder($req){
 $project=absint($req->get_param('project'));
 if(!anst_own($project,'anst_projeto'))return new WP_Error('anst_missing','Projeto indisponível.',['status'=>404]);
 $items=$req->get_param('items');
 if(!is_array($items)||count($items)>300)return new WP_Error('anst_invalid','Lista inválida.',['status'=>400]);
 $columns=array_column(anst_board_columns_read($project),'id');
 $seen=[];
 foreach($items as $item){
   if(!is_array($item)||!isset($item['id'],$item['column'],$item['rank']))return new WP_Error('anst_invalid','Item inválido.',['status'=>400]);
   $id=(int)$item['id'];$p=anst_own($id,'anst_cartao');
   if(!$p||(int)anst_meta_get($id,'_anst_project',true)!==$project||isset($seen[$id])||!in_array($item['column'],$columns,true))
     return new WP_Error('anst_invalid','Cartão ou coluna inválidos.',['status'=>400]);
   $seen[$id]=1;
 }
 foreach($items as $item){
   anst_meta_update((int)$item['id'],'_anst_column',sanitize_text_field((string)$item['column']));
   anst_meta_update((int)$item['id'],'_anst_rank',max(0,(int)$item['rank']));
 }
 return rest_ensure_response(['ok'=>true]);
}
function anst_board_add_column($req){
 $id=absint($req['id']);
 if(!anst_own($id,'anst_projeto'))return new WP_Error('anst_missing','Projeto indisponível.',['status'=>404]);
 $name=trim(sanitize_text_field((string)($req->get_param('name')?:'Título')));
 if($name===''||mb_strlen($name)>40)return new WP_Error('anst_invalid','Nome inválido.',['status'=>400]);
 $cols=anst_board_columns_read($id);
 if(count($cols)>=60)return new WP_Error('anst_limit','Limite de 60 colunas.',['status'=>400]);
 $cols[]=['id'=>'col_'.strtolower(wp_generate_password(8,false,false)),'name'=>$name];
 anst_meta_update($id,'_anst_board_columns',wp_slash(wp_json_encode($cols,JSON_UNESCAPED_UNICODE)));
 return rest_ensure_response(['columns'=>$cols]);
}
function anst_board_import($req){
 $p=anst_own($req['id'],'anst_projeto');
 if(!$p)return new WP_Error('anst_missing','Projeto indisponível.',['status'=>404]);
 if(anst_meta_get($p->ID,'_anst_legacy_cards_imported',true))
  return rest_ensure_response(['imported'=>0,'already'=>true]);
 $u=anst_unlock_read($p->ID);
 $lines=array_values(array_filter(array_map('trim',preg_split('/\R/u',(string)$u['brainstorm']))));
 if(count($lines)>150)return new WP_Error('anst_limit','Muitas notas antigas.',['status'=>400]);
 $count=0;
 foreach($lines as $line){
   $id=wp_insert_post(['post_type'=>'anst_cartao','post_status'=>'publish','post_author'=>get_current_user_id(),
     'post_title'=>mb_substr($line,0,80),'post_content'=>mb_substr($line,0,4000)],true);
   if(is_wp_error($id))return $id;
   anst_meta_update($id,'_anst_project',$p->ID);
   anst_meta_update($id,'_anst_column','soltas');
   anst_meta_update($id,'_anst_rank',$count++);
 }
 anst_meta_update($p->ID,'_anst_legacy_cards_imported',1);
 return rest_ensure_response(['imported'=>$count]);
}

function anst_bootstrap($request=false) {
    if (!headers_sent()) nocache_headers();
    $slim=$request===true;
    $scope=$request instanceof WP_REST_Request?absint($request->get_param('project')):0;
    if($scope&&!anst_own($scope,'anst_projeto'))
      return new WP_Error('anst_project','Projeto indisponível.',['status'=>404]);
    $projects=array_map(static fn($p)=>anst_project_data($p,$slim||($scope>0&&(int)$p->ID!==$scope)),anst_children('anst_projeto'));
    if($slim)return rest_ensure_response(['projects'=>$projects,'notes'=>[],'chapters'=>[],'cards'=>[],'slim'=>true]);
    $notes=array_map('anst_note_data',anst_children('anst_nota',$scope?:null));
    $chapters=array_map('anst_chapter_data',anst_children('anst_capitulo',$scope?:null));
    usort($chapters,static fn($a,$b)=>$a['project']<=>$b['project']?:$a['order']<=>$b['order']?:$a['id']<=>$b['id']);
    $cards=array_map('anst_card_data',anst_children('anst_cartao',$scope?:null));
    return rest_ensure_response(['projects'=>$projects,'notes'=>$notes,'chapters'=>$chapters,'cards'=>$cards,'scope'=>$scope?:'all']);
}
function anst_create_project($req) {
    $mode = sanitize_key($req->get_param('mode'));
    if (!in_array($mode, ['sem-ideia', 'assunto', 'ideia', 'manuscrito'], true)) { return new WP_Error('anst_mode', 'Escolha um ponto de partida válido.', ['status' => 400]); }
    $raw = sanitize_text_field((string) $req->get_param('title'));
    $title = $raw !== '' ? mb_substr($raw, 0, 140) : 'Projeto sem título';
    $id = wp_insert_post(['post_type' => 'anst_projeto', 'post_status' => 'publish', 'post_author' => get_current_user_id(), 'post_title' => $title], true);
    if (is_wp_error($id)) { return $id; }
    anst_meta_update($id, '_anst_start', $mode);
    anst_meta_update($id, '_anst_visibility', 'private');
    if ($mode!=='manuscrito') {
       $state=anst_unlock_blank();
       $state['step']=$mode==='assunto'?1:($mode==='ideia'?3:0);
       anst_meta_update($id,'_anst_unlock_v2',wp_slash(wp_json_encode($state,JSON_UNESCAPED_UNICODE)));
    }
    return rest_ensure_response(['id' => (int) $id]);
}
function anst_update_project($req) {
    $p = anst_own($req['id'], 'anst_projeto');
    if (!$p) { return new WP_Error('anst_missing', 'Projeto indisponível.', ['status' => 404]); }
    if ($req->has_param('title')) {
        $t = sanitize_text_field((string) $req->get_param('title'));
        if ($t !== '') { wp_update_post(['ID' => $p->ID, 'post_title' => mb_substr($t, 0, 140)]); }
    }
    if ($req->has_param('color')) {
        $tone=sanitize_key((string)$req->get_param('color'));
        if(!in_array($tone,['none','sea','blue','violet','rose','amber','forest','slate'],true))
            return new WP_Error('anst_tone','Escolha um tom disponível.',['status'=>400]);
        anst_meta_update($p->ID,'_anst_project_tone',$tone);
        if(anst_project_tone($p->ID)!==$tone)
            return new WP_Error('anst_tone_save','A cor não foi confirmada pelo servidor.',['status'=>503]);
    }
    foreach (['topic', 'premise','logline','storyline','theme','thesis','tone','summary','outline'] as $field) {
        if ($req->has_param($field)) {
            anst_meta_update($p->ID, '_anst_' . $field, sanitize_textarea_field((string) $req->get_param($field)));
        }
    }
    return rest_ensure_response(['ok' => true,'color'=>anst_project_tone($p->ID),'title'=>get_the_title($p->ID)]);
}
function anst_create_note($req) {
    $text = trim(sanitize_textarea_field((string) $req->get_param('text')));
    if ($text === '') { return new WP_Error('anst_empty', 'Escreva sua anotação.', ['status' => 400]); }
    if (mb_strlen($text) > 20000) { return new WP_Error('anst_large', 'A anotação excedeu o limite de 20 mil caracteres.', ['status' => 400]); }
    $kind = sanitize_key($req->get_param('kind') ?: 'idea');
    if (!in_array($kind, ['idea', 'research', 'review'], true)) { return new WP_Error('anst_kind', 'Tipo de anotação inválido.', ['status' => 400]); }
    $project = absint($req->get_param('project'));
    if ($project && !anst_own($project, 'anst_projeto')) { return new WP_Error('anst_project', 'Projeto indisponível.', ['status' => 404]); }
    $id = wp_insert_post(['post_type' => 'anst_nota', 'post_status' => 'publish', 'post_author' => get_current_user_id(),
        'post_title' => mb_substr($text, 0, 72), 'post_content' => $text], true);
    if (is_wp_error($id)) { return $id; }
    anst_meta_update($id, '_anst_kind', $kind);
    anst_meta_update($id, '_anst_project', $project);
    $note=anst_note_data(get_post($id));
    return rest_ensure_response(['id' => (int) $id,'note'=>$note]);
}
function anst_create_chapter($req) {
    $project = absint($req->get_param('project'));
    if (!$project || !anst_own($project, 'anst_projeto')) { return new WP_Error('anst_project', 'Projeto indisponível.', ['status' => 404]); }
    $all = anst_children('anst_capitulo', $project);
    $structModel=sanitize_key((string)$req->get_param('structureModel'));
    $structStage=sanitize_key((string)$req->get_param('structureStage'));
    if($structModel!=='') {
      $stages=anst_structure_stages();
      if(!isset($stages[$structModel])||!in_array($structStage,$stages[$structModel],true))
         return new WP_Error('anst_stage','Escolha uma posição válida para o capítulo.',['status'=>400]);
    }
    $title = sanitize_text_field((string) $req->get_param('title'));
    if ($title === '') { $title = 'Capítulo ' . (count($all) + 1); }
    $id = wp_insert_post(['post_type' => 'anst_capitulo', 'post_status' => 'publish', 'post_author' => get_current_user_id(),
        'post_title' => mb_substr($title, 0, 140), 'menu_order' => count($all)], true);
    if (is_wp_error($id)) { return $id; }
    anst_meta_update($id, '_anst_project', $project);
    anst_meta_update($id, '_anst_delta', wp_slash(wp_json_encode(['ops' => [['insert' => "\n"]]])));
    if($structModel!=='') {
       $positions=['three_acts'=>'','hero_journey'=>''];
       $positions[$structModel]=$structStage;
       anst_meta_update($id,'_anst_structure_map_v1',wp_slash(wp_json_encode(['revision'=>1,'positions'=>$positions])));
    }
    $verify=anst_chapter_data(get_post($id));
    if($verify['project']!==$project||($structModel!==''&&($verify['structure']['positions'][$structModel]??'')!==$structStage))
      return new WP_Error('anst_chapter_verify','Capítulo criado, mas a associação precisa de confirmação.',['status'=>503,'chapter_id'=>(int)$id]);
    return rest_ensure_response(['id' => (int) $id,'structure'=>anst_structure_state($id),'chapter'=>$verify]);
}
function anst_import_chapter($req) {
 $project=absint($req->get_param('project'));
 if(!$project||!anst_own($project,'anst_projeto'))
   return new WP_Error('anst_project','Projeto indisponível.',['status'=>404]);
 $text=$req->get_param('text');
 if(!is_string($text)||trim($text)===''||strlen($text)>2500000)
   return new WP_Error('anst_import_size','Arquivo vazio ou maior que 1,5 MB.',['status'=>413]);
 if(!mb_check_encoding($text,'UTF-8')||str_contains($text,"\xEF\xBF\xBD"))
   return new WP_Error('anst_import_charset','O TXT contém caracteres ilegíveis. Selecione o arquivo original para corrigir a codificação.',['status'=>422]);
 $title=sanitize_text_field((string)$req->get_param('title'));
 $title=$title!==''?mb_substr($title,0,140):'Manuscrito importado';
 $normalized=rtrim(str_replace(["\r\n","\r"],"\n",$text),"\n")."\n";
 $json=wp_json_encode(['ops'=>[['insert'=>$normalized]]],JSON_UNESCAPED_UNICODE);
 if(!is_string($json)||strlen($json)>10000000)
   return new WP_Error('anst_json','Texto acima do limite de codificação.',['status'=>413]);
 $sha=hash('sha256',$normalized);
 $all=anst_children('anst_capitulo',$project);
 foreach($all as $old){
   if($old->post_title!==$title)continue;
   $stored=(string)anst_meta_get($old->ID,'_anst_import_sha',true);
   if($stored!==''&&hash_equals($stored,$sha))
     return rest_ensure_response(['ok'=>true,'id'=>(int)$old->ID,'existing'=>true,'chapter'=>anst_chapter_data($old)]);
   if($stored===''){
     $prior=anst_chapter_data($old);
     $txt=implode('',array_map(static fn($op)=>is_string($op['insert']??null)?$op['insert']:'',$prior['delta']['ops']??[]));
     if($txt===$normalized)return rest_ensure_response(['ok'=>true,'id'=>(int)$old->ID,'existing'=>true,'chapter'=>anst_chapter_data($old)]);
   }
 }
 $id=wp_insert_post(['post_type'=>'anst_capitulo','post_status'=>'publish',
   'post_author'=>get_current_user_id(),'post_title'=>$title,'menu_order'=>count($all)],true);
 if(is_wp_error($id))return $id;
 anst_meta_update($id,'_anst_project',$project);
 anst_meta_update($id,'_anst_delta',wp_slash($json));
 anst_meta_update($id,'_anst_import_sha',$sha);
 $saved=json_decode((string)anst_meta_get($id,'_anst_delta',true),true);
 if(($saved['ops'][0]['insert']??null)!==$normalized)
   return new WP_Error('anst_import_verify','Capítulo criado, porém o conteúdo precisa ser verificado.',['status'=>503,'id'=>$id]);
 return rest_ensure_response(['ok'=>true,'id'=>(int)$id,'existing'=>false,'chapter'=>anst_chapter_data(get_post($id))]);
}
function anst_reimport_chapter($req){
 $id=absint($req['id']);
 $p=anst_own($id,'anst_capitulo');
 if(!$p)return new WP_Error('anst_missing','Capítulo indisponível.',['status'=>404]);
 $text=$req->get_param('text');
 if(!is_string($text)||trim($text)===''||strlen($text)>2500000)
   return new WP_Error('anst_import_size','Arquivo vazio ou muito grande.',['status'=>413]);
 if(!mb_check_encoding($text,'UTF-8')||str_contains($text,"\xEF\xBF\xBD"))
   return new WP_Error('anst_import_charset','A nova leitura contém caracteres ilegíveis. O capítulo anterior foi preservado.',['status'=>422]);
 $normalized=rtrim(str_replace(["\r\n","\r"],"\n",$text),"\n")."\n";
 $json=wp_json_encode(['ops'=>[['insert'=>$normalized]]],JSON_UNESCAPED_UNICODE);
 if(!is_string($json)||strlen($json)>10000000)
   return new WP_Error('anst_import_encoding','Erro ao codificar o novo conteúdo.',['status'=>413]);
 $before=(string)anst_meta_get($id,'_anst_delta',true);
 if($before==='')return new WP_Error('anst_import_missing','O texto anterior não foi encontrado.',['status'=>409]);
 if(!anst_meta_get($id,'_anst_pre_encoding_repair_backup',true)){
   anst_meta_update($id,'_anst_pre_encoding_repair_backup',wp_slash($before));
   if((string)anst_meta_get($id,'_anst_pre_encoding_repair_backup',true)!==$before)
     return new WP_Error('anst_backup_failure','Falha ao preservar o texto anterior.',['status'=>503]);
 }
 anst_meta_update($id,'_anst_delta',wp_slash($json));
 $saved=json_decode((string)anst_meta_get($id,'_anst_delta',true),true);
 if(($saved['ops'][0]['insert']??null)!==$normalized){
   anst_meta_update($id,'_anst_delta',wp_slash($before));
   return new WP_Error('anst_import_verify','Falha ao confirmar texto corrigido. A versão anterior foi restaurada.',['status'=>503]);
 }
 anst_meta_update($id,'_anst_import_sha',hash('sha256',$normalized));
 return rest_ensure_response(['ok'=>true,'id'=>$id,'repaired'=>true,'backup'=>true,'chapter'=>anst_chapter_data(get_post($id))]);
}
function anst_save_chapter($req) {
    $p = anst_own($req['id'], 'anst_capitulo');
    if (!$p) return new WP_Error('anst_missing', 'Capítulo indisponível.', ['status'=>404]);
    $project = (int) anst_meta_get($p->ID, '_anst_project', true);
    if (!anst_own($project, 'anst_projeto')) return new WP_Error('anst_project', 'Projeto indisponível.', ['status'=>404]);
    $hasDelta = $req->has_param('delta');
    $json = null; $expected = '';
    if ($hasDelta) {
        $delta = $req->get_param('delta');
        if (!is_array($delta) || !isset($delta['ops']) || !is_array($delta['ops']))
            return new WP_Error('anst_delta', 'Formato de texto inválido.', ['status'=>400]);
        $json = wp_json_encode($delta);
        if (!is_string($json)) return new WP_Error('anst_delta', 'Documento inválido.', ['status'=>400]);
        if (strlen($json) > 2000000) return new WP_Error('anst_size', 'Capítulo acima do limite desta versão.', ['status'=>413]);
        $expected = (string)$req->get_param('expected_hash');
        if (!preg_match('/^[a-f0-9]{64}$/', $expected))
            return new WP_Error('anst_precondition', 'Reabra o capítulo para confirmar a versão antes de salvar.', ['status'=>428]);
    }
    $title = null;
    if ($req->has_param('title')) {
        $clean = sanitize_text_field((string)$req->get_param('title'));
        if ($clean !== '') $title = mb_substr($clean, 0, 140);
    }
    global $wpdb;
    $mutex = 'anst_chapter_save_' . (int)$p->ID;
    $locked = (int)$wpdb->get_var($wpdb->prepare('SELECT GET_LOCK(%s, 4)', $mutex));
    if ($locked !== 1)
        return new WP_Error('anst_busy', 'Outro salvamento está em andamento. Aguarde e tente novamente.', ['status'=>409]);
    try {
        $p = get_post((int)$p->ID);
        $previous = (string)anst_meta_get($p->ID, '_anst_delta', true);
        $currentHash = hash('sha256', $p->post_title . "\0" . $previous);
        if ($hasDelta && !hash_equals($currentHash, $expected))
            return new WP_Error('anst_conflict', 'O capítulo foi alterado em outra janela. Copie suas alterações antes de recarregar.', ['status'=>409]);
        if ($hasDelta && $previous !== $json && $previous !== '') {
            $snapshot = anst_version_snapshot($p->ID, 'automatico', false);
            if (is_wp_error($snapshot)) return $snapshot;
        }
        if ($hasDelta) {
            anst_meta_update($p->ID, '_anst_delta', wp_slash($json));
            $verified = json_decode((string)anst_meta_get($p->ID,'_anst_delta',true), true);
            if (!is_array($verified) || $verified !== $delta)
                return new WP_Error('anst_verify', 'O servidor ainda não confirmou o texto.', ['status'=>503,'id'=>$p->ID]);
        }
        if ($title !== null && $title !== $p->post_title) {
            $result = wp_update_post(['ID'=>$p->ID,'post_title'=>$title], true);
            if (is_wp_error($result))
                return new WP_Error('anst_title', 'O título do capítulo ainda não foi confirmado.', ['status'=>503]);
        } elseif ($hasDelta) {
            wp_update_post(['ID'=>$p->ID]);
        }
        $p = get_post((int)$p->ID);
        $current = (string)anst_meta_get($p->ID, '_anst_delta', true);
        return rest_ensure_response(['ok'=>true,
            'contentHash'=>hash('sha256', $p->post_title . "\0" . $current),
            'modified'=>$p->post_modified]);
    } finally {
        $wpdb->get_var($wpdb->prepare('SELECT RELEASE_LOCK(%s)', $mutex));
    }
}


/** Percurso sequencial conforme M1/A2, M2/A8 e M2/A9. Preserva o v1. */
function anst_unlock_blank() {
    return [
        'version'=>2, 'step'=>0, 'brainstorm'=>'', 'pattern'=>'', 'sentence'=>'',
        'paragraph'=>'', 'premise'=>'', 'developments'=>'',
        'protagonist'=>'', 'objective'=>'', 'obstacle'=>'', 'logline'=>'',
        'turning'=>'', 'storyline'=>'', 'theme'=>'', 'thesis'=>'', 'tone'=>'',
        'summary'=>'', 'events'=>'', 'outline'=>'', 'expanded_topics'=>'', 'questions_outline'=>'',
        'logline_mode'=>'template', 'logline_template'=>'need','logline_custom'=>'',
        'logline_actor'=>'','logline_action'=>'','logline_goal'=>'','logline_want'=>'','logline_block'=>'',
        'storyline_mode'=>'template','storyline_custom'=>'','storyline_incident'=>'',
        'storyline_actor'=>'','storyline_goal'=>'','storyline_challenge'=>'','storyline_stakes'=>'',
        'completed'=>false, 'revision'=>0
    ];
}
function anst_unlock_read($id) {
    $raw = anst_meta_get(absint($id), '_anst_unlock_v2', true);
    $v2 = json_decode((string)$raw, true);
    if (is_array($v2) && isset($v2['version']) && (int)$v2['version']===2) {
        // Textos produzidos antes dos modelos preenchíveis abrem no modo livre.
        if(!array_key_exists('logline_mode',$v2) && !empty($v2['logline'])){
            $v2['logline_mode']='free';
            $v2['logline_custom']=(string)$v2['logline'];
        }
        if(!array_key_exists('storyline_mode',$v2) && !empty($v2['storyline'])){
            $v2['storyline_mode']='free';
            $v2['storyline_custom']=(string)$v2['storyline'];
        }
        return array_merge(anst_unlock_blank(), $v2);
    }
    // Migração somente na leitura: o registro antigo continua preservado.
    $old = json_decode((string)anst_meta_get(absint($id), '_anst_unlock_v1', true), true);
    if (!is_array($old)) {
       $state=anst_unlock_blank();
       $mode=(string)anst_meta_get(absint($id),'_anst_start',true);
       $state['step']=$mode==='assunto'?1:($mode==='ideia'?3:0);
       $state['pattern']=(string)anst_meta_get(absint($id),'_anst_topic',true);
       $state['premise']=(string)anst_meta_get(absint($id),'_anst_premise',true);
       return $state;
    }
    $v = anst_unlock_blank();
    $observation=trim((string)($old['observation']??''));
    $brainstorm=trim((string)($old['brainstorm']??''));
    $v['brainstorm']=implode("\n",array_filter([$observation,$brainstorm],static fn($x)=>$x!==''));
    $v['pattern']=(string)($old['pattern']??'');
    $alternatives=is_array($old['questions']??null)?$old['questions']:[];
    $chosen=(int)($old['selected']??-1);
    $v['premise']=trim((string)($alternatives[$chosen]??''));
    if ($v['premise']==='') {
        foreach($alternatives as $alt) if(trim((string)$alt)!=='') {$v['premise']=trim((string)$alt);break;}
    }
    $legacyStep=max(0,min(3,(int)($old['step']??0)));
    $v['step']=match($legacyStep){0,1=>0,2=>1,3=>3};
    if(!empty($old['completed'])) $v['step']=4;
    return $v;
}
function anst_unlock_update($req) {
    $post=anst_own($req['id'],'anst_projeto');
    if (!$post) return new WP_Error('anst_missing','Projeto indisponível.',['status'=>404]);
    if (!in_array(anst_meta_get($post->ID,'_anst_start',true),['sem-ideia','assunto','ideia'],true))
        return new WP_Error('anst_mode','Este projeto começa pelo manuscrito.',['status'=>400]);
    $data=$req->get_param('state');
    if (!is_array($data))
        return new WP_Error('anst_invalid','Dados inválidos.',['status'=>400]);
    $old=anst_unlock_read($post->ID);
    if (!isset($data['revision']) || !is_numeric($data['revision']) ||
        (int)$data['revision'] !== (int)$old['revision']) {
        return new WP_Error('anst_conflict','O projeto foi alterado em outra aba. Recarregue antes de salvar.',['status'=>409]);
    }
    $limits=[
        'brainstorm'=>22000,'pattern'=>2500,'sentence'=>2500,
        'paragraph'=>8000,'premise'=>5000,'developments'=>18000,
        'protagonist'=>3000,'objective'=>3000,'obstacle'=>3000,'logline'=>5000,
        'turning'=>5000,'storyline'=>7000,'theme'=>2500,'thesis'=>5000,'tone'=>2500,
        'summary'=>15000,'events'=>16000,'outline'=>22000,'expanded_topics'=>18000,'questions_outline'=>16000,
        'logline_mode'=>20,'logline_template'=>20,'logline_custom'=>5000,
        'logline_actor'=>2500,'logline_action'=>2500,'logline_goal'=>2500,
        'logline_want'=>2500,'logline_block'=>2500,
        'storyline_mode'=>20,'storyline_custom'=>7000,
        'storyline_incident'=>2500,'storyline_actor'=>2500,'storyline_goal'=>2500,
        'storyline_challenge'=>2500,'storyline_stakes'=>2500
    ];
    $new=$old;
    foreach($limits as $key=>$max){
        $v=$data[$key]??'';
        if(!is_scalar($v) || mb_strlen((string)$v)>$max)
            return new WP_Error('anst_size','Há um campo acima do limite permitido.',['status'=>400]);
        $new[$key]=sanitize_textarea_field((string)$v);
    }
    if(!in_array($new['logline_mode'],['free','template'],true) ||
       !in_array($new['storyline_mode'],['free','template'],true) ||
       !in_array($new['logline_template'],['need','want'],true))
       return new WP_Error('anst_mode','Modelo narrativo inválido.',['status'=>400]);
    $step=$data['step']??0;
    if(!is_numeric($step) || (int)$step<0 || (int)$step>10)
        return new WP_Error('anst_step','Etapa inválida.',['status'=>400]);
    $new['step']=(int)$step;
    $complete=(bool)$req->get_param('complete');
    if($complete){
        foreach(['premise'=>'premissa','logline'=>'logline','storyline'=>'storyline','outline'=>'outline'] as $key=>$label){
            if(trim($new[$key])==='') return new WP_Error('anst_required','Preencha a '.$label.' antes de concluir.',['status'=>400]);
        }
        if($new['step']!==10) return new WP_Error('anst_step','Conclua a última etapa.',['status'=>400]);
        $new['completed']=true;
    }elseif(!empty($old['completed'])){
        $keys=array_keys($limits);
        foreach($keys as $key){if($new[$key]!==$old[$key]){$new['completed']=false;break;}}
    }
    $new['version']=2;
    $new['revision']=(int)$old['revision']+1;
    $updated=anst_meta_update($post->ID,'_anst_unlock_v2',wp_slash(wp_json_encode($new,JSON_UNESCAPED_UNICODE)));
    if($updated===false) return new WP_Error('anst_storage','Não foi possível salvar o exercício.',['status'=>500]);
    // Integra as decisões narrativas ao projeto à medida que são salvas.
    foreach([
        '_anst_topic'=>'pattern','_anst_premise'=>'premise','_anst_logline'=>'logline',
        '_anst_storyline'=>'storyline','_anst_theme'=>'theme','_anst_thesis'=>'thesis',
        '_anst_tone'=>'tone','_anst_summary'=>'summary','_anst_outline'=>'outline'
    ] as $meta=>$field){
        if($new[$field]!==$old[$field])anst_meta_update($post->ID,$meta,$new[$field]);
    }
    if($complete){
        foreach([
            '_anst_premise'=>'premise','_anst_topic'=>'pattern',
            '_anst_logline'=>'logline','_anst_storyline'=>'storyline',
            '_anst_theme'=>'theme','_anst_thesis'=>'thesis','_anst_tone'=>'tone',
            '_anst_summary'=>'summary','_anst_events'=>'events','_anst_outline'=>'outline'
        ] as $meta=>$field){anst_meta_update($post->ID,$meta,$new[$field]);}
    }
    return rest_ensure_response([
        'ok'=>true,'state'=>$new,
        'concept'=>$complete?[
            'premise'=>$new['premise'],'topic'=>$new['pattern'],
            'logline'=>$new['logline'],'storyline'=>$new['storyline'],
            'theme'=>$new['theme'],'thesis'=>$new['thesis'],
            'tone'=>$new['tone'],'summary'=>$new['summary'],'outline'=>$new['outline']
        ]:null
    ]);
}



/** Lixeira privada do Estúdio: sete dias de retenção, com restauração. */
function anst_trash_types(){return ['anst_projeto','anst_nota','anst_capitulo','anst_cartao'];}
function anst_trashed_at($p){
 $t=(int)anst_meta_get($p->ID,'_wp_trash_meta_time',true);
 return $t>0?$t:(strtotime((string)$p->post_modified_gmt.' UTC')?:0);
}
function anst_trash_item_data($p){
 $labels=['anst_projeto'=>'Projeto','anst_nota'=>'Anotação','anst_capitulo'=>'Capítulo','anst_cartao'=>'Cartão'];
 $title=trim($p->post_title);
 if(!$title)$title=mb_substr(wp_strip_all_tags($p->post_content),0,80);
 if(!$title)$title='Item #'.$p->ID;
 $time=anst_trashed_at($p);
 return ['id'=>(int)$p->ID,'title'=>$title,'type'=>$p->post_type,'typeLabel'=>$labels[$p->post_type],
 'project'=>(int)anst_meta_get($p->ID,'_anst_project',true),
 'cascade'=>(int)anst_meta_get($p->ID,'_anst_cascade_project',true),
 'trashedAt'=>$time,'expiresAt'=>$time+7*DAY_IN_SECONDS];
}
function anst_purge_project_children($project){
 foreach(['anst_nota','anst_capitulo','anst_cartao'] as $type){
   foreach(['trash','publish','draft','private'] as $status){
     for($i=0;$i<30;$i++){
       $ids=get_posts(['post_type'=>$type,'post_status'=>$status,'posts_per_page'=>150,
         'fields'=>'ids','meta_query'=>[['key'=>anst_meta_query_key($type,'_anst_project'),'value'=>(string)absint($project)]]]);
       if(!$ids)break;
       $deleted=0;
       foreach($ids as $id){if(wp_delete_post((int)$id,true))$deleted++;}
       if(!$deleted||count($ids)<150)break;
     }
   }
 }
}
function anst_trash_cleanup_enabled(){return (string)get_option('anst_trash_cleanup_enabled','0')==='1';}

/** Preserva itens ANST da lixeira quando WordPress executa limpeza nativa. */
add_filter('pre_delete_post',static function($pre,$post,$force_delete){
 if($pre!==null)return $pre;
 if(!anst_trash_cleanup_enabled()&&doing_action('wp_scheduled_delete')&&
    $post instanceof WP_Post&&in_array($post->post_type,anst_trash_types(),true))return false;
 return $pre;
},10,3);
/**
 * WP 5.6+ restaura por padrão como draft. O novo Estúdio recupera o status
 * anterior exclusivamente nos seus quatro CPTs.
 */
add_filter('wp_untrash_post_status', static function($status,$id,$previous){
 $p=get_post($id);
 if($p instanceof WP_Post && in_array($p->post_type,anst_trash_types(),true)
    && in_array($previous,['publish','draft','pending','private'],true))return $previous;
 return $status;
},10,3);

function anst_cleanup_trash(){
 if(!anst_trash_cleanup_enabled())return;
 $cutoff=time()-7*DAY_IN_SECONDS;
 for($i=0;$i<30;$i++){
  $posts=get_posts(['post_type'=>anst_trash_types(),'post_status'=>'trash','posts_per_page'=>100,
    'meta_key'=>'_wp_trash_meta_time','orderby'=>'meta_value_num','order'=>'ASC',
    'meta_query'=>[['key'=>'_wp_trash_meta_time','value'=>$cutoff,'compare'=>'<=','type'=>'NUMERIC']]]);
  if(!$posts)break;
  $deleted=0;
  foreach($posts as $p){
    if($p->post_status!=='trash'||anst_trashed_at($p)>$cutoff)continue;
    if($p->post_type==='anst_projeto')anst_purge_project_children($p->ID);
    if(wp_delete_post($p->ID,true))$deleted++;
  }
  if(!$deleted||count($posts)<100)break;
 }
 update_option('_anst_trash_cleaned',time(),false);
}
function anst_schedule_trash(){
 if(!anst_trash_cleanup_enabled())return;
 if(!wp_next_scheduled('anst_trash_cleanup_daily'))
   wp_schedule_event(time()+300,'daily','anst_trash_cleanup_daily');
}
add_action('init','anst_schedule_trash',20);
add_action('anst_trash_cleanup_daily','anst_cleanup_trash');
function anst_trash_catchup(){
 if(!anst_trash_cleanup_enabled())return;
 if(!is_page('studio')||(int)get_option('_anst_trash_cleaned',0)>time()-DAY_IN_SECONDS)return;
 if(get_transient('_anst_cleanup_active'))return;
 set_transient('_anst_cleanup_active',1,15*MINUTE_IN_SECONDS);
 try{anst_cleanup_trash();}finally{delete_transient('_anst_cleanup_active');}
}
add_action('template_redirect','anst_trash_catchup',30);
function anst_trash_list($req){
 if(anst_trash_cleanup_enabled()&&(int)get_option('_anst_trash_cleaned',0)<time()-DAY_IN_SECONDS)anst_cleanup_trash();
 $posts=get_posts(['post_type'=>anst_trash_types(),'post_status'=>'trash',
   'author'=>get_current_user_id(),'posts_per_page'=>500,'orderby'=>'modified','order'=>'DESC']);
 return rest_ensure_response(['items'=>array_map('anst_trash_item_data',$posts),'retentionDays'=>7]);
}
function anst_trash_restore($req){
 $p=get_post(absint($req['id']));
 if(!$p||!in_array($p->post_type,anst_trash_types(),true)||$p->post_status!=='trash'||
    (int)$p->post_author!==get_current_user_id())
   return new WP_Error('anst_missing','Item indisponível na sua lixeira.',['status'=>404]);
 if($p->post_type!=='anst_projeto'){
   $parent_id=(int)anst_meta_get($p->ID,'_anst_project',true);
   $parent=$parent_id>0?get_post($parent_id):null;
   if($parent&&$parent->post_status==='trash')
      return new WP_Error('anst_parent','Restaure primeiro o projeto.',['status'=>409]);
   if($parent&&(int)$parent->post_author!==get_current_user_id())
      return new WP_Error('anst_parent','Projeto indisponível.',['status'=>409]);
 }
 if(!wp_untrash_post($p->ID))
    return new WP_Error('anst_restore','Falha ao restaurar.',['status'=>500]);
 $restored=0;
 if($p->post_type==='anst_projeto'){
  foreach(['anst_nota','anst_capitulo','anst_cartao'] as $type){
   $children=get_posts(['post_type'=>$type,'post_status'=>'trash','author'=>get_current_user_id(),
      'posts_per_page'=>-1,'meta_query'=>[
       ['key'=>anst_meta_query_key($type,'_anst_project'),'value'=>(string)$p->ID],
       ['key'=>anst_meta_query_key($type,'_anst_cascade_project'),'value'=>(string)$p->ID]]]);
   foreach($children as $child)if(wp_untrash_post($child->ID)){
      anst_meta_delete($child->ID,'_anst_cascade_project');$restored++;
   }
  }
 }else anst_meta_delete($p->ID,'_anst_cascade_project');
 return rest_ensure_response(['ok'=>true,'childrenRestored'=>$restored]);
}
function anst_trash_forever($req){
 $p=get_post(absint($req['id']));
 if(!$p||!in_array($p->post_type,anst_trash_types(),true)||$p->post_status!=='trash'||
    (int)$p->post_author!==get_current_user_id())
    return new WP_Error('anst_missing','Item indisponível.',['status'=>404]);
 if((string)$req->get_param('confirm_title')!==anst_trash_item_data($p)['title'])
    return new WP_Error('anst_confirm','Confirmação inválida.',['status'=>400]);
 if($p->post_type==='anst_projeto')anst_purge_project_children($p->ID);
 if(!wp_delete_post($p->ID,true))
    return new WP_Error('anst_delete','Falha na exclusão definitiva.',['status'=>500]);
 return rest_ensure_response(['ok'=>true]);
}
function anst_trash_single($req){
 $p=get_post(absint($req['id']));
 if(!$p||!in_array($p->post_type,['anst_nota','anst_capitulo','anst_cartao'],true)||
   $p->post_status==='trash'||(int)$p->post_author!==get_current_user_id())
   return new WP_Error('anst_missing','Item indisponível.',['status'=>404]);
 if(!wp_trash_post($p->ID))
    return new WP_Error('anst_trash','Falha ao enviar para a lixeira.',['status'=>500]);
 return rest_ensure_response(['ok'=>true]);
}

function anst_delete_project($req){
    $project=anst_own($req['id'],'anst_projeto');
    if(!$project)return new WP_Error('anst_missing','Projeto indisponível.',['status'=>404]);
    if((string)$req->get_param('title')!==$project->post_title)
        return new WP_Error('anst_confirm','A confirmação do nome do projeto é obrigatória.',['status'=>400]);
    foreach(['anst_nota','anst_capitulo','anst_cartao'] as $type){
        $ids=get_posts(['post_type'=>$type,'post_status'=>'publish','author'=>get_current_user_id(),
          'posts_per_page'=>-1,'fields'=>'ids','meta_query'=>[['key'=>anst_meta_query_key($type,'_anst_project'),'value'=>(string)$project->ID]]]);
        foreach($ids as $id){
            anst_meta_update((int)$id,'_anst_cascade_project',$project->ID);
            if(!wp_trash_post((int)$id))
               return new WP_Error('anst_trash','Falha ao enviar material para a lixeira.',['status'=>500]);
        }
    }
    if(!wp_trash_post($project->ID))
        return new WP_Error('anst_trash','Não foi possível mover o projeto para a lixeira.',['status'=>500]);
    return rest_ensure_response(['ok'=>true,'trashed'=>(int)$project->ID]);
}



function anst_board_reorder_columns($req){
    $project_id=absint($req['id']);
    if(!anst_own($project_id,'anst_projeto'))
      return new WP_Error('anst_missing','Projeto indisponível.',['status'=>404]);
    $order=$req->get_param('order');
    $columns=anst_board_columns_read($project_id);
    if(!is_array($order)||count($order)!==count($columns))
      return new WP_Error('anst_order','A lista de colunas está incompleta.',['status'=>400]);
    $map=[];
    foreach($columns as $column){$map[$column['id']]=$column;}
    $sorted=[];
    foreach($order as $id){
        if(!is_string($id)||!array_key_exists($id,$map))
          return new WP_Error('anst_order','Coluna duplicada ou desconhecida.',['status'=>400]);
        $sorted[]=$map[$id];
        unset($map[$id]);
    }
    if($map)return new WP_Error('anst_order','Colunas ausentes.',['status'=>400]);
    anst_meta_update($project_id,'_anst_board_columns',wp_slash(wp_json_encode($sorted,JSON_UNESCAPED_UNICODE)));
    if(array_column(anst_board_columns_read($project_id),'id')!==$order)
      return new WP_Error('anst_write','Falha ao salvar a nova ordem.',['status'=>500]);
    return rest_ensure_response(['columns'=>$sorted]);
}

function anst_board_rename_column($req){
    $id=absint($req['id']);$p=anst_own($id,'anst_projeto');
    if(!$p)return new WP_Error('anst_missing','Projeto indisponível.',['status'=>404]);
    $column=sanitize_text_field((string)$req->get_param('column'));
    $name=trim(sanitize_text_field((string)$req->get_param('name')));
    if($name===''||mb_strlen($name)>40)
      return new WP_Error('anst_invalid','O título precisa ter de 1 a 40 caracteres.',['status'=>400]);
    $cols=anst_board_columns_read($id);
    $found=false;
    foreach($cols as &$col){
      if($col['id']===$column){$col['name']=$name;$found=true;break;}
    }unset($col);
    if(!$found)return new WP_Error('anst_missing','Coluna indisponível.',['status'=>404]);
    anst_meta_update($id,'_anst_board_columns',wp_slash(wp_json_encode($cols,JSON_UNESCAPED_UNICODE)));
    return rest_ensure_response(['columns'=>$cols]);
}
function anst_board_zoom_read($id){
    $value=(int)anst_user_meta_get(get_current_user_id(),'_anst_board_zoom_'.absint($id),true);
    return ($value>=50&&$value<=150&&$value%10===0)?$value:100;
}
function anst_board_zoom_update($req){
    $id=absint($req['id']);
    if(!anst_own($id,'anst_projeto'))return new WP_Error('anst_missing','Projeto indisponível.',['status'=>404]);
    $zoom=$req->get_param('zoom');
    if(!is_numeric($zoom)||((int)$zoom)<50||((int)$zoom)>150||((int)$zoom)%10!==0)
      return new WP_Error('anst_invalid','Ampliação deve estar entre 50% e 150%, em passos de 10%.',['status'=>400]);
    anst_user_meta_update(get_current_user_id(),'_anst_board_zoom_'.$id,(int)$zoom);
    return rest_ensure_response(['zoom'=>(int)$zoom]);
}
function anst_video_update($req){
    if(!anst_can_manage_lessons())
      return new WP_Error('anst_forbidden','Somente o papel Anthares edita os vídeos.',['status'=>403]);
    $key=sanitize_key($req['section']);
    $allowed=['mural','assunto','premissa','logline','storyline','tema','outline'];
    if(!in_array($key,$allowed,true))return new WP_Error('anst_invalid','Seção inválida.',['status'=>400]);
    $raw=trim((string)$req->get_param('url'));
    $url='';
    if($raw!==''){
        if(strlen($raw)>2048)return new WP_Error('anst_url','URL muito longa.',['status'=>400]);
        $parts=wp_parse_url($raw);
        if(!$parts||strtolower((string)($parts['scheme']??''))!=='https'||
           empty($parts['host'])||isset($parts['user'])||isset($parts['pass']))
           return new WP_Error('anst_url','Informe um link HTTPS válido.',['status'=>400]);
        $host=strtolower(rtrim($parts['host'],'.'));
        $domains=['youtube.com','youtu.be','youtube-nocookie.com','hotmart.com','hotmartclub.com'];
        $valid=false;
        foreach($domains as $domain){
            if($host===$domain||str_ends_with($host,'.'.$domain)){$valid=true;break;}
        }
        if(!$valid)return new WP_Error('anst_url','Aceitamos links do YouTube ou da Hotmart.',['status'=>400]);
        $url=esc_url_raw($raw,['https']);
        if(!$url)return new WP_Error('anst_url','URL inválida.',['status'=>400]);
    }
    $settings=anst_lesson_settings();
    $settings[$key]=$url;
    anst_acf_lesson_option_update($settings);
    return rest_ensure_response(['section'=>$key,'url'=>$url,'videos'=>$settings]);
}
function anst_lesson_permission(){return anst_can_manage_lessons()&&anst_writes_enabled();}


/** Revisão privada por projeto, com tarefas, trecho associado e lista por técnica. */

/** Backups private and restorable for elements folders and character sheets. */
function anst_elements_history_read($project){
 $items=json_decode((string)anst_meta_get(absint($project),'_anst_elements_versions_v1',true),true);
 return is_array($items)&&is_array($items['items']??null)?array_values($items['items']):[];
}
function anst_elements_history_list($items){
 return array_map(static fn($x)=>[
   'id'=>$x['id'],'created'=>$x['created'],'source'=>$x['source'],
   'folders'=>count($x['state']['folders']??[]),
   'elements'=>array_sum(array_map(static fn($f)=>count($f['items']??[]),$x['state']['folders']??[]))
 ],array_reverse($items));
}
function anst_elements_snapshot($project,$source='manual',$force=false,$state=null){
 $items=anst_elements_history_read($project);
 $last=end($items);
 if(!$force&&$last&&time()-(int)($last['epoch']??0)<900)return $items;
 $state=is_array($state)?$state:anst_elements_read($project);
 $items[]=['id'=>wp_generate_uuid4(),'created'=>current_time('mysql',true),
  'epoch'=>time(),'source'=>$source,'state'=>$state];
 $items=array_slice($items,-8);
 $json=wp_json_encode(['items'=>$items],JSON_UNESCAPED_UNICODE|JSON_INVALID_UTF8_SUBSTITUTE);
 while(is_string($json)&&strlen($json)>12000000&&count($items)>1){
  array_shift($items);$json=wp_json_encode(['items'=>$items],JSON_UNESCAPED_UNICODE|JSON_INVALID_UTF8_SUBSTITUTE);
 }
 if(!is_string($json)||strlen($json)>12000000)return new WP_Error('anst_history_size','Hist?rico acima do limite.',['status'=>413]);
 anst_meta_update($project,'_anst_elements_versions_v1',wp_slash($json));
 $verify=anst_elements_history_read($project);
 if(count($verify)!==count($items)||end($verify)['id']!==end($items)['id'])
   return new WP_Error('anst_history_verify','C?pia n?o confirmada.',['status'=>503]);
 return $verify;
}
function anst_elements_versions_manage($req){
 $project=absint($req['id']);
 if(!anst_own($project,'anst_projeto'))return new WP_Error('anst_project','Projeto indispon?vel.',['status'=>404]);
 $items=anst_elements_history_read($project);
 if($req->get_method()==='GET')
   return rest_ensure_response(['ok'=>true,'versions'=>anst_elements_history_list($items)]);
 $action=sanitize_key((string)$req->get_param('action'));
 if($action==='snapshot'){
  $result=anst_elements_snapshot($project,'manual',true);
  if(is_wp_error($result))return $result;
  return rest_ensure_response(['ok'=>true,'versions'=>anst_elements_history_list($result)]);
 }
 if($action!=='restore')return new WP_Error('anst_action','Opera??o inv?lida.',['status'=>400]);
 $current=anst_elements_read($project);
 $revision=$req->get_param('revision');
 if(!is_numeric($revision)||(int)$revision!==$current['revision'])
  return new WP_Error('anst_conflict','As fichas foram alteradas em outra sess?o.',['status'=>409]);
 $id=sanitize_text_field((string)$req->get_param('version'));
 $chosen=null;
 foreach($items as $entry)if(($entry['id']??'')===$id){$chosen=$entry;break;}
 if(!$chosen||!is_array($chosen['state']??null))
   return new WP_Error('anst_version','Vers?o das fichas n?o encontrada.',['status'=>404]);
 $backup=anst_elements_snapshot($project,'antes_da_restauracao',true,$current);
 if(is_wp_error($backup))return $backup;
 $state=$chosen['state'];$state['revision']=$current['revision']+1;
 $json=wp_json_encode($state,JSON_UNESCAPED_UNICODE|JSON_INVALID_UTF8_SUBSTITUTE);
 if(!is_string($json))return new WP_Error('anst_json','Estado inv?lido.',['status'=>400]);
 anst_meta_update($project,'_anst_elements_v1',wp_slash($json));
 $confirmed=anst_elements_read($project);
 if($confirmed!==$state)return new WP_Error('anst_restore','Restaura??o n?o confirmada.',['status'=>503]);
 return rest_ensure_response(['ok'=>true,'elements'=>$confirmed]);
}

function anst_review_types(){
 return ['trama'=>'Trama','personagem'=>'Personagem','narrador'=>'Narrador',
 'descricao'=>'Descrição','dialogo'=>'Diálogo','tensao'=>'Tensão','concisa'=>'Concisão',
 'causalidade'=>'Causalidade','conhecimento'=>'Conhecimento','continuidade'=>'Continuidade',
 'elementos'=>'Elementos recorrentes','outro'=>'Outro'];
}
function anst_review_read($project){
 $json=(string)anst_meta_get(absint($project),'_anst_review_v1',true);
 $value=json_decode($json,true);
 if(!is_array($value))$value=[];
 return ['revision'=>max(0,(int)($value['revision']??0)),
  'tasks'=>is_array($value['tasks']??null)?array_values($value['tasks']):[],
  'checklist'=>is_array($value['checklist']??null)?$value['checklist']:[]];
}
function anst_review_manage($req){
 $project=absint($req['id']);
 if(!anst_own($project,'anst_projeto'))return new WP_Error('anst_project','Projeto indisponível.',['status'=>404]);
 $state=anst_review_read($project);
 if($req->get_method()==='GET')return rest_ensure_response(['ok'=>true,'review'=>$state]);
 $revision=$req->get_param('revision');
 if(!is_numeric($revision)||(int)$revision!==$state['revision'])
   return new WP_Error('anst_conflict','A revisão foi alterada em outra janela. Atualize antes de salvar.',['status'=>409]);
 $action=sanitize_key((string)$req->get_param('action'));
 $types=anst_review_types();
 if($action==='create'){
  $chapter=absint($req->get_param('chapter'));
  if($chapter){
   $post=anst_own($chapter,'anst_capitulo');
   if(!$post||(int)anst_meta_get($chapter,'_anst_project',true)!==$project)
      return new WP_Error('anst_chapter','Capítulo inválido neste projeto.',['status'=>400]);
  }
  $quote=mb_substr(sanitize_textarea_field((string)$req->get_param('quote')),0,600);
  $offset=$req->get_param('offset');
  $offset=is_numeric($offset)?max(0,(int)$offset):-1;
  $note=trim(sanitize_textarea_field((string)$req->get_param('note')));
  $type=sanitize_key((string)$req->get_param('type'));
  $priority=sanitize_key((string)$req->get_param('priority'));
  if($note===''||mb_strlen($note)>5000||!isset($types[$type])||!in_array($priority,['baixa','normal','alta'],true))
    return new WP_Error('anst_review','Preencha o comentário e escolha tipo e prioridade válidos.',['status'=>400]);
  if(count($state['tasks'])>=400)return new WP_Error('anst_limit','Limite de 400 tarefas neste projeto.',['status'=>413]);
  $state['tasks'][]=['id'=>wp_generate_uuid4(),'chapter'=>$chapter,'quote'=>$quote,'offset'=>$offset,
    'note'=>$note,'type'=>$type,'priority'=>$priority,'status'=>'aberta',
    'created'=>current_time('mysql',true),'updated'=>current_time('mysql',true)];
 }elseif(in_array($action,['status','delete'],true)){
  $id=sanitize_text_field((string)$req->get_param('item'));
  $found=false;
  foreach($state['tasks'] as $i=>&$item){
   if(($item['id']??'')!==$id)continue;
   $found=true;
   if($action==='delete')unset($state['tasks'][$i]);
   else{
    $status=sanitize_key((string)$req->get_param('status'));
    if(!in_array($status,['aberta','resolvida'],true))
      return new WP_Error('anst_status','Status inválido.',['status'=>400]);
    $item['status']=$status;
    $item['updated']=current_time('mysql',true);
   }
   break;
  }unset($item);
  if(!$found)return new WP_Error('anst_task','Comentário não encontrado.',['status'=>404]);
  $state['tasks']=array_values($state['tasks']);
 }elseif($action==='checklist'){
  $key=sanitize_key((string)$req->get_param('type'));
  $status=(bool)$req->get_param('checked');
  if(!isset($types[$key]))return new WP_Error('anst_type','Técnica inválida.',['status'=>400]);
  $state['checklist'][$key]=$status;
 }else return new WP_Error('anst_action','Ação inválida.',['status'=>400]);
 $state['revision']++;
 $json=wp_json_encode($state,JSON_UNESCAPED_UNICODE|JSON_INVALID_UTF8_SUBSTITUTE);
 if(!is_string($json)||strlen($json)>600000)return new WP_Error('anst_size','Revisão acima do limite.',['status'=>413]);
 anst_meta_update($project,'_anst_review_v1',wp_slash($json));
 if(anst_review_read($project)!==$state)return new WP_Error('anst_verify','Revisão não confirmada.',['status'=>503]);
 return rest_ensure_response(['ok'=>true,'review'=>$state]);
}
/** Versões locais imutáveis do capítulo, com restauração reversível. */
function anst_version_read($chapter){
 $raw=json_decode((string)anst_meta_get($chapter,'_anst_versions_v1',true),true);
 return is_array($raw)&&is_array($raw['items']??null)?array_values($raw['items']):[];
}
function anst_version_snapshot($chapter,$source='manual',$force=false){
 $saved=anst_version_read($chapter);
 $last=end($saved);
 if(!$force&&$last&&!empty($last['created_epoch'])&&time()-(int)$last['created_epoch']<900)
   return $saved;
 $post=get_post($chapter);
 if(!$post||$post->post_type!=='anst_capitulo')return new WP_Error('anst_chapter','Capítulo indisponível.');
 $delta=json_decode((string)anst_meta_get($chapter,'_anst_delta',true),true);
 if(!is_array($delta)||!isset($delta['ops']))return new WP_Error('anst_delta','Texto indisponível.');
 $saved[]=['id'=>wp_generate_uuid4(),'created'=>current_time('mysql',true),'created_epoch'=>time(),
  'source'=>$source,'title'=>$post->post_title,'delta'=>$delta];
 $saved=array_slice($saved,-12);
 $json=wp_json_encode(['items'=>$saved],JSON_UNESCAPED_UNICODE|JSON_INVALID_UTF8_SUBSTITUTE);
 while(strlen($json)>18000000&&count($saved)>1){
  array_shift($saved);$json=wp_json_encode(['items'=>$saved],JSON_UNESCAPED_UNICODE|JSON_INVALID_UTF8_SUBSTITUTE);
 }
 if(!is_string($json)||strlen($json)>18000000)return new WP_Error('anst_version_size','Versão acima do limite de segurança.');
 anst_meta_update($chapter,'_anst_versions_v1',wp_slash($json));
 $verify=anst_version_read($chapter);
 if(count($verify)!==count($saved)||end($verify)['id']!==end($saved)['id'])
   return new WP_Error('anst_version_verify','Backup da versão não confirmado.');
 return $verify;
}
function anst_version_manage($req){
 $p=anst_own($req['id'],'anst_capitulo');
 if(!$p)return new WP_Error('anst_missing','Capítulo indisponível.',['status'=>404]);
 if(!anst_own((int)anst_meta_get($p->ID,'_anst_project',true),'anst_projeto'))
   return new WP_Error('anst_project','Projeto indisponível.',['status'=>404]);
 $items=anst_version_read($p->ID);
 if($req->get_method()==='GET'){
  $full=sanitize_text_field((string)$req->get_param('version'));
  if($full!==''){
   foreach($items as $entry)if(($entry['id']??'')===$full)
    return rest_ensure_response(['ok'=>true,'version'=>$entry]);
   return new WP_Error('anst_version','Versão não encontrada.',['status'=>404]);
  }
  return rest_ensure_response(['ok'=>true,'versions'=>array_map(static fn($x)=>[
    'id'=>$x['id'],'created'=>$x['created'],'title'=>$x['title'],'source'=>$x['source']
  ],array_reverse($items))]);
 }
 $action=sanitize_key((string)$req->get_param('action'));
 if($action==='snapshot'){
  $out=anst_version_snapshot($p->ID,'manual',true);
  if(is_wp_error($out))return $out;
  return rest_ensure_response(['ok'=>true,'versions'=>array_map(static fn($x)=>[
    'id'=>$x['id'],'created'=>$x['created'],'title'=>$x['title'],'source'=>$x['source']
  ],array_reverse($out))]);
 }
 if($action==='restore'){
  $expected=(string)$req->get_param('expected_hash');
  if(!preg_match('/^[a-f0-9]{64}$/',$expected))
    return new WP_Error('anst_precondition','Recarregue o capítulo para confirmar a versão antes da restauração.',['status'=>428]);
  global $wpdb;
  $mutex='anst_chapter_save_'.(int)$p->ID;
  $locked=(int)$wpdb->get_var($wpdb->prepare('SELECT GET_LOCK(%s, 4)',$mutex));
  if($locked!==1)
    return new WP_Error('anst_busy','Outro salvamento está em andamento.',['status'=>409]);
  try{
   $p=get_post($p->ID);
   $raw=(string)anst_meta_get($p->ID,'_anst_delta',true);
   if(!hash_equals(hash('sha256',$p->post_title."\0".$raw),$expected))
     return new WP_Error('anst_conflict','O capítulo foi alterado em outra janela. Recarregue antes de restaurar.',['status'=>409]);
   $items=anst_version_read($p->ID);
   $id=sanitize_text_field((string)$req->get_param('version'));
   $entry=null;
   foreach($items as $row)if(($row['id']??'')===$id){$entry=$row;break;}
   if(!$entry)return new WP_Error('anst_version','Versão não encontrada.',['status'=>404]);
   $before=anst_version_snapshot($p->ID,'antes_da_restauracao',true);
   if(is_wp_error($before))return $before;
   $delta=wp_json_encode($entry['delta'],JSON_UNESCAPED_UNICODE|JSON_INVALID_UTF8_SUBSTITUTE);
   if(!is_string($delta))return new WP_Error('anst_delta','Versão inválida.',['status'=>400]);
   anst_meta_update($p->ID,'_anst_delta',wp_slash($delta));
   wp_update_post(['ID'=>$p->ID,'post_title'=>mb_substr(sanitize_text_field($entry['title']),0,140)]);
   if(json_decode((string)anst_meta_get($p->ID,'_anst_delta',true),true)!==$entry['delta'])
     return new WP_Error('anst_restore','Restaurar não confirmado. O estado anterior foi preservado nas versões.',['status'=>503]);
   return rest_ensure_response(['ok'=>true,'chapter'=>anst_chapter_data(get_post($p->ID))]);
  }finally{
   $wpdb->get_var($wpdb->prepare('SELECT RELEASE_LOCK(%s)',$mutex));
  }
 }
 return new WP_Error('anst_action','Operação inválida.',['status'=>400]);
}

function anst_routes() {
    $routes = [
        ['/bootstrap', 'GET', 'anst_bootstrap'],
        ['/projects', 'POST', 'anst_create_project'],
        ['/trash', 'GET', 'anst_trash_list'],
        ['/trash/(?P<id>\d+)/restore', 'POST', 'anst_trash_restore'],
        ['/trash/(?P<id>\d+)', 'DELETE', 'anst_trash_forever'],
        ['/items/(?P<id>\d+)', 'DELETE', 'anst_trash_single'],
        ['/cards', 'POST', 'anst_card_create'],
        ['/cards/reorder', 'POST', 'anst_cards_reorder'],
        ['/cards/(?P<id>\d+)', 'POST', 'anst_card_update'],
        ['/cards/(?P<id>\d+)', 'DELETE', 'anst_card_delete'],
        ['/projects/(?P<id>\d+)/columns', 'POST', 'anst_board_add_column'],
        ['/projects/(?P<id>\d+)/columns/rename', 'POST', 'anst_board_rename_column'],
        ['/projects/(?P<id>\d+)/columns/reorder', 'POST', 'anst_board_reorder_columns'],
        ['/projects/(?P<id>\d+)/zoom', 'POST', 'anst_board_zoom_update'],
        ['/projects/(?P<id>\\d+)/elements', 'POST', 'anst_elements_update'],
        ['/projects/(?P<id>\\d+)/elements/versions', 'GET', 'anst_elements_versions_manage'],
        ['/projects/(?P<id>\\d+)/elements/versions', 'POST', 'anst_elements_versions_manage'],
        ['/projects/(?P<id>\\d+)/review', 'GET', 'anst_review_manage'],
        ['/projects/(?P<id>\\d+)/review', 'POST', 'anst_review_manage'],
        ['/chapters/(?P<id>\\d+)/versions', 'GET', 'anst_version_manage'],
        ['/chapters/(?P<id>\\d+)/versions', 'POST', 'anst_version_manage'],
        ['/projects/(?P<id>\d+)/import-ideas', 'POST', 'anst_board_import'],
        ['/projects/(?P<id>\d+)', 'DELETE', 'anst_delete_project'],
        ['/projects/(?P<id>\d+)', 'POST', 'anst_update_project'],
        ['/notes', 'POST', 'anst_create_note'],
        ['/projects/(?P<id>\d+)/unlock', 'POST', 'anst_unlock_update'],
        ['/chapters', 'POST', 'anst_create_chapter'],
        ['/chapters/import', 'POST', 'anst_import_chapter'],
        ['/chapters/reorder', 'POST', 'anst_reorder_chapters'],
        ['/chapters/(?P<id>\\d+)/reimport', 'POST', 'anst_reimport_chapter'],
        ['/chapters/(?P<id>\d+)', 'POST', 'anst_save_chapter'],
        ['/chapters/(?P<id>\d+)/structure', 'POST', 'anst_structure_update'],
    ];
    register_rest_route('anthares-studio/v1','/lesson/(?P<section>mural|assunto|premissa|logline|storyline|tema|outline)',[
      'methods'=>'POST','callback'=>'anst_video_update','permission_callback'=>'anst_lesson_permission'
    ]);
    foreach ($routes as [$path, $method, $callback]) {
        register_rest_route('anthares-studio/v1', $path, [
            'methods' => $method, 'callback' => $callback, 'permission_callback' => 'anst_permission',
        ]);
    }
}
add_action('rest_api_init', 'anst_routes');

// Ferramenta G3 executada exclusivamente em WP-CLI (dry-run por padrão).
if (defined('WP_CLI') && WP_CLI) { require_once __DIR__ . '/includes/migration/class-anst-legacy-migrator.php'; }
