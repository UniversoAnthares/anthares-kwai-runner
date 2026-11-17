<?php
/**
 * Anthares Studio — camada ACF do domínio narrativo.
 * Padrão OFF até aprovação G4 e migração ACF concluída; jamais altera /estudio.
 */
if (!defined('ABSPATH')) { exit; }

function anst_acf_runtime_enabled(): bool {
    return defined('ANST_ACF_RUNTIME_APPROVED') && ANST_ACF_RUNTIME_APPROVED === true
        && (string)get_option('anst_acf_runtime_enabled', '0') === '1';
}
function anst_acf_require_ready(): void {
    if (!function_exists('get_field') || !function_exists('update_field') || !function_exists('acf_get_field')) {
        throw new RuntimeException('ANST_ACF_RUNTIME_REQUIRES_ACF_FREE');
    }
}
function anst_acf_field_map(): array {
    static $by_type = null;
    if ($by_type !== null) return $by_type;
    $path = dirname(__DIR__,2) . '/docs/acf-core-migration-map.json';
    $json = json_decode((string)file_get_contents($path), true);
    if (!is_array($json) || ($json['schema_version'] ?? '') !== 'G5-offline-2026-11-16'
        || (int)($json['fields'] ?? 0) !== 40 || count($json['entries'] ?? []) !== 52) {
        throw new RuntimeException('ANST_ACF_MAP_INVALID');
    }
    $by_type = [];
    foreach ($json['entries'] as $entry) {
        if (($entry['legacy_storage'] ?? '') !== 'postmeta') continue;
        $type = (string)$entry['post_type'];
        $key = (string)$entry['legacy_key'];
        if (!str_starts_with($key, '_anst_') || isset($by_type[$type][$key])) {
            throw new RuntimeException('ANST_ACF_MAP_DUPLICATE');
        }
        $by_type[$type][$key] = [
            'field_key' => (string)$entry['target_field_key'],
            'name' => (string)$entry['target_field_name']
        ];
    }
    return $by_type;
}
function anst_acf_resolve(int $id, string $legacy): ?array {
    $type = get_post_type($id);
    $map = anst_acf_field_map();
    $field = $map[$type][$legacy] ?? null;
    if ($field === null && str_starts_with($legacy, '_anst_')) {
        throw new RuntimeException('ANST_ACF_UNKNOWN_FIELD:' . $type . ':' . $legacy);
    }
    return $field;
}
function anst_meta_get($id, $key = '', $single = false) {
    if (!anst_acf_runtime_enabled() || !is_string($key) || $key === '') {
        return get_post_meta($id,$key,$single);
    }
    anst_acf_require_ready();
    $field = anst_acf_resolve((int)$id, $key);
    if (!$field) return get_post_meta($id,$key,$single);
    $name=$field['name'];
    if (!metadata_exists('post',(int)$id,$name)) return $single?'':[];
    $value=get_field($field['field_key'],(int)$id,false);
    if ($value===false && (string)get_post_meta($id,$name,true)==='0') $value='0';
    return $single?$value:[$value];
}
function anst_meta_update($id, $key, $value, $previous='') {
    if (!anst_acf_runtime_enabled() || !is_string($key)) {
        return update_post_meta($id,$key,$value,$previous);
    }
    anst_acf_require_ready();
    $field=anst_acf_resolve((int)$id, $key);
    if (!$field) return update_post_meta($id,$key,$value,$previous);
    // O chamador do plugin já usa wp_slash para JSON/Delta.
    return update_field($field['field_key'],$value,(int)$id);
}
function anst_meta_delete($id,$key,$value='') {
    if (!anst_acf_runtime_enabled() || !is_string($key)) return delete_post_meta($id,$key,$value);
    anst_acf_require_ready();
    $field=anst_acf_resolve((int)$id,$key);
    if (!$field) return delete_post_meta($id,$key,$value);
    if ($value!=='' && (string)anst_meta_get($id,$key,true)!==(string)$value) return false;
    return delete_field($field['field_key'],(int)$id);
}
function anst_meta_query_key($post_type,$legacy):string {
    if (!anst_acf_runtime_enabled()) return $legacy;
    anst_acf_require_ready();
    $map=anst_acf_field_map();
    $entry=$map[(string)$post_type][(string)$legacy]??null;
    if (!$entry && str_starts_with((string)$legacy,'_anst_'))
        throw new RuntimeException('ANST_ACF_UNKNOWN_QUERY_FIELD:' . $post_type . ':' . $legacy);
    return $entry?$entry['name']:$legacy;
}
function anst_user_meta_get($user,$key,$single=false) {
    if (!anst_acf_runtime_enabled() || !preg_match('/^_anst_board_zoom_(\d+)$/',(string)$key,$m))
        return get_user_meta($user,$key,$single);
    anst_acf_require_ready();
    $json=get_field('field_anst16u_user_board_zoom_index_json_v1','user_'.(int)$user,false);
    $map=json_decode((string)$json,true);
    $value=is_array($map)?($map[$m[1]]??''):'';
    return $single?$value:[$value];
}
function anst_user_meta_update($user,$key,$value) {
    if (!anst_acf_runtime_enabled() || !preg_match('/^_anst_board_zoom_(\d+)$/',(string)$key,$m))
        return update_user_meta($user,$key,$value);
    anst_acf_require_ready();
    $project=(int)$m[1];
    $p=get_post($project);
    if (!$p || $p->post_type!=='anst_projeto' || (int)$p->post_author!==(int)$user)
        throw new RuntimeException('ANST_ACF_ZOOM_OWNER_MISMATCH');
    $json=get_field('field_anst16u_user_board_zoom_index_json_v1','user_'.(int)$user,false);
    $map=json_decode((string)$json,true);
    if (!is_array($map))$map=[];
    $map[(string)$project]=(int)$value;
    ksort($map,SORT_NUMERIC);
    return update_field('field_anst16u_user_board_zoom_index_json_v1',
                        wp_slash(wp_json_encode($map,JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE)),
                        'user_'.(int)$user);
}
/**
 * Configuracao dos links das aulas no ACF Free como options_*, sem exigir Options Page PRO.
 * Os valores anteriores de anst_section_lesson_videos sao preservados para rollback.
 */
function anst_acf_lesson_option_get(): array {
    if (!anst_acf_runtime_enabled()) {
        $value=get_option('anst_section_lesson_videos',[]);
        return is_array($value)?$value:[];
    }
    anst_acf_require_ready();
    $value=get_field('field_anst16c_course_lesson_links_json_v1','option',false);
    if (!is_string($value)) throw new RuntimeException('ANST_ACF_COURSE_NOT_MIGRATED');
    $decoded=json_decode($value,true);
    if (!is_array($decoded)) throw new RuntimeException('ANST_ACF_COURSE_JSON_INVALID');
    return $decoded;
}
function anst_acf_lesson_option_update(array $settings): bool {
    if (!anst_acf_runtime_enabled()) return update_option('anst_section_lesson_videos',$settings,false);
    anst_acf_require_ready();
    $json=wp_json_encode($settings,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);
    if (!is_string($json)) throw new RuntimeException('ANST_ACF_COURSE_ENCODE_FAILED');
    $ok=update_field('field_anst16c_course_lesson_links_json_v1',wp_slash($json),'option');
    if (anst_acf_lesson_option_get()!==$settings) throw new RuntimeException('ANST_ACF_COURSE_ROUNDTRIP_FAILED');
    return (bool)$ok;
}

add_action('acf/init', static function(){
    if (!anst_acf_runtime_enabled())return;
    foreach (glob(__DIR__.'/../../acf-json/group_anst*.json')?:[] as $path) {
        $group=json_decode((string)file_get_contents($path),true);
        if (!is_array($group) || !isset($group['key']) || ($group['active']??true)!==false) {
            throw new RuntimeException('ANST_ACF_FIELD_GROUP_INVALID');
        }
        $group['active']=true;
        acf_add_local_field_group($group);
    }
},5);
