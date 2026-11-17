<?php
/**
 * Anthares Studio ACF migration adapter, G5. WP-CLI only; never loaded in web requests.
 * Schema remains offline in Git until G4 acceptance.
 */
if (!defined('WP_CLI') || !WP_CLI) { return; }

final class ANST_ACF_Migrator {
    private $wpdb;
    private string $root;
    private array $rows = [];
    private array $groups = [];
    private array $fields = [];
    private array $mappings = [];

    public function __construct() {
        global $wpdb;
        $this->wpdb = $wpdb;
        $this->root = dirname(__DIR__, 2);
        $this->load_contract();
    }

    private function load_contract(): void {
        $manifest = $this->root . '/docs/acf-core-migration-map.json';
        $data = json_decode((string)file_get_contents($manifest), true);
        if (!is_array($data) || ($data['schema_version'] ?? '') !== 'G5-offline-2026-11-16'
            || ($data['status'] ?? '') !== 'OFFLINE_NOT_REGISTERED') {
            throw new RuntimeException('ACF_SCHEMA_MANIFEST_INVALID');
        }
        $groups = glob($this->root . '/acf-json/group_anst*.json') ?: [];
        if (count($groups) !== 12) throw new RuntimeException('ACF_GROUP_COUNT_CHANGED');
        foreach ($groups as $path) {
            $g = json_decode((string)file_get_contents($path), true);
            if (!is_array($g) || ($g['active'] ?? true) !== false) {
                throw new RuntimeException('ACF_GROUP_NOT_OFFLINE');
            }
            $this->groups[] = $g;
            foreach ($g['fields'] ?? [] as $f) {
                $name = (string)($f['name'] ?? '');
                $key = (string)($f['key'] ?? '');
                if (!str_starts_with($name, 'studio_') ||
                    !str_starts_with($key, 'field_anst') || isset($this->fields[$key])) {
                    throw new RuntimeException('ACF_FIELD_COLLISION');
                }
                $this->fields[$key] = $f;
            }
        }
        if (count($this->fields) !== 40) throw new RuntimeException('ACF_FIELD_COUNT_CHANGED');
        $this->mappings = $data['entries'] ?? [];
        if (count($this->mappings) !== 52) throw new RuntimeException('ACF_MAPPING_COUNT_CHANGED');
        foreach ($this->mappings as $m) {
            $field = $this->fields[$m['target_field_key']] ?? null;
            if (!$field || $field['name'] !== $m['target_field_name'] ||
                $m['legacy_key'] === '_' . $field['name']) {
                throw new RuntimeException('ACF_MAPPING_INVALID');
            }
        }
    }

    private function rows(): array {
        $db = $this->wpdb;
        return $db->get_results("SELECT ID,post_type,post_status,post_author,post_title,post_content,menu_order
                                 FROM {$db->posts}
                                 WHERE post_type IN ('anst_projeto','anst_nota','anst_capitulo','anst_cartao')
                                 ORDER BY ID", ARRAY_A) ?: [];
    }

    private function current_source(): array {
        $db = $this->wpdb;
        $hash = hash_init('sha256');
        $records = $this->rows();
        $meta_count = 0;
        foreach ($records as $r) {
            hash_update($hash, serialize($r));
            $metas = $db->get_results($db->prepare(
                "SELECT meta_key,meta_value FROM {$db->postmeta} WHERE post_id=%d
                 AND (meta_key LIKE '\\_anst\\_%' OR meta_key LIKE 'anst\\_%') ORDER BY meta_id",
                (int)$r['ID']), ARRAY_A) ?: [];
            foreach ($metas as $meta) hash_update($hash, serialize($meta));
            $meta_count += count($metas);
        }
        $users = $db->get_col("SELECT DISTINCT post_author FROM {$db->posts} WHERE post_type='anst_projeto'");
        foreach ($users as $uid) {
            $meta = get_user_meta((int)$uid);
            ksort($meta);
            foreach ($meta as $k => $values) {
                if (str_starts_with($k, '_anst_board_zoom_')) hash_update($hash, serialize([(int)$uid,$k,$values]));
            }
        }
        $lesson=get_option('anst_section_lesson_videos',[]);
        if (!is_array($lesson)) throw new RuntimeException('COURSE_LEGACY_OPTION_INVALID');
        hash_update($hash,serialize(['lesson_option'=>$lesson]));
        return ['fingerprint'=>hash_final($hash),'posts'=>$records,'source_meta'=>$meta_count];
    }

    private function source_value(int $post, string $key): ?string {
        $db = $this->wpdb;
        $values = $db->get_col($db->prepare(
            "SELECT meta_value FROM {$db->postmeta} WHERE post_id=%d AND meta_key=%s ORDER BY meta_id",
            $post,$key));
        if (count($values)>1) throw new RuntimeException('SOURCE_DUPLICATE_META:' . $post . ':' . $key);
        return count($values) ? (string)$values[0] : null;
    }

    private function expected_items(array $posts): array {
        $list = [];
        $byType = [];
        $owners = [];
        foreach ($posts as $p) {
            $byType[$p['post_type']][] = $p;
            if ($p['post_type'] === 'anst_projeto') {
                $owners[(int)$p['ID']] = (int)$p['post_author'];
            }
        }
        $reference_errors = 0;
        foreach ($posts as $post) {
            $id=(int)$post['ID'];
            foreach ($this->mappings as $m) {
                if ($m['legacy_storage'] !== 'postmeta' || $m['post_type'] !== $post['post_type']) continue;
                $raw=$this->source_value($id,$m['legacy_key']);
                if ($raw === null) continue;
                $field=$this->fields[$m['target_field_key']];
                $type=$field['type'];
                if ($type === 'post_object' && $raw !== '' && $raw !== '0') {
                    $ref=(int)$raw;
                    if (!ctype_digit($raw) || !isset($owners[$ref]) ||
                        $owners[$ref] !== (int)$post['post_author']) {
                        $reference_errors++;
                    }
                }
                $list[]=['post'=>$id,'name'=>$m['target_field_name'],'key'=>$m['target_field_key'],
                    'raw'=>$raw,'type'=>$type];
            }
        }
        $zooms=[];
        $users=array_values(array_unique(array_values($owners)));
        foreach ($users as $uid) {
            $meta=get_user_meta((int)$uid);
            $z=[];
            foreach ($meta as $key=>$values) {
                if (!str_starts_with($key,'_anst_board_zoom_')) continue;
                $id=substr($key,strlen('_anst_board_zoom_'));
                if (!ctype_digit($id) || !isset($owners[(int)$id]) || $owners[(int)$id] !== (int)$uid) {
                    $reference_errors++;continue;
                }
                if (count($values)!==1) throw new RuntimeException('ZOOM_DUPLICATE_VALUE');
                $z[(string)$id]=(int)maybe_unserialize($values[0]);
            }
            if ($z) {
                ksort($z,SORT_NUMERIC);
                $zooms[(int)$uid]=wp_json_encode($z, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
            }
        }
        $course=get_option('anst_section_lesson_videos',[]);
        if (!is_array($course)) throw new RuntimeException('COURSE_OPTION_INVALID');
        $courseJson=wp_json_encode($course,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);
        if (!is_string($courseJson)) throw new RuntimeException('COURSE_ENCODE_INVALID');
        return ['items'=>$list,'zooms'=>$zooms,'course'=>$courseJson,'reference_errors'=>$reference_errors];
    }

    private function preexisting(array $values, array $zooms, string $course): int {
        $found=0;
        foreach ($values as $v) {
            if (metadata_exists('post',$v['post'],$v['name'])) $found++;
        }
        foreach ($zooms as $uid=>$json) {
            if (metadata_exists('user',$uid,'studio_user_board_zoom_index_json')) $found++;
        }
        if (get_option('options_studio_course_lesson_links_json',null)!==null) $found++;
        return $found;
    }

    private function verify_backup(string $path): void {
        $real=realpath($path);
        $root=realpath(dirname(ABSPATH) . '/anthares-private-storage');
        if (!$real || !$root || !str_starts_with($real,$root . DIRECTORY_SEPARATOR)) {
            throw new RuntimeException('BACKUP_NOT_PRIVATE');
        }
        $pass=(string)@file_get_contents($real . '/restore-verification.txt');
        if (!str_contains($pass,'RESTORE=PASS')) throw new RuntimeException('BACKUP_NOT_VERIFIED');
        $manifest=(string)@file_get_contents($real . '/backup-sha256.txt');
        foreach (['wordpress-consistent.sql.gz','anthares-estudio-original.tar.gz'] as $file) {
            if (!is_file($real . '/' . $file)) throw new RuntimeException('BACKUP_FILE_MISSING');
            $digest=hash_file('sha256',$real . '/' . $file);
            if (!str_contains($manifest,$digest . '  ' . $file)) throw new RuntimeException('BACKUP_HASH_FAILED');
        }
    }

    private function register_offline_acf(): void {
        if (!function_exists('acf_add_local_field_group') || !function_exists('update_field')) {
            throw new RuntimeException('ACF_FREE_NOT_LOADED');
        }
        foreach ($this->groups as $group) {
            // In-memory registration for the current WP-CLI process only.
            $group['active']=true;
            acf_add_local_field_group($group);
        }
        foreach ($this->fields as $key=>$field) {
            if (!acf_get_field($key)) throw new RuntimeException('ACF_FIELD_NOT_REGISTERED:' . $key);
        }
    }

    private function same_raw(string $a,string $b): bool {
        return hash_equals(hash('sha256',$a),hash('sha256',$b));
    }

    private function save_one(int|string $post, string $key, string $name, string $value, string $type): bool {
        if ($post==='option') {
            $existing=get_option('options_'.$name,null);
            if ($existing!==null) {
                $ref=(string)get_option('_options_'.$name,'');
                if (!$this->same_raw($value,(string)$existing) || $ref!==$key)
                    throw new RuntimeException('RECONCILE_ACF_OPTION_EXISTING:'.$name);
                return false;
            }
            update_field($key,wp_slash($value),'option');
            $saved=get_option('options_'.$name,null);
            $ref=(string)get_option('_options_'.$name,'');
            if (!is_string($saved) || !$this->same_raw($value,$saved) || $ref!==$key)
                throw new RuntimeException('ACF_OPTION_ROUNDTRIP_FAILED:'.$name);
            return true;
        }
        $isUser=is_string($post) && str_starts_with($post,'user_');
        $id=$isUser ? (int)substr($post,5) : (int)$post;
        $kind=$isUser ? 'user' : 'post';
        if (metadata_exists($kind,$id,$name)) {
            $current=(string)get_metadata($kind,$id,$name,true);
            $ref=(string)get_metadata($kind,$id,'_'.$name,true);
            if (!$this->same_raw($value,$current) || $ref!==$key) throw new RuntimeException('RECONCILE_ACF_EXISTING:' . $name);
            return false;
        }
        // update_field uses WordPress metadata APIs, which unslash incoming data.
        // wp_slash is required to preserve backslashes in raw Quill Delta JSON.
        $input=$type==='post_object' ? (int)$value : wp_slash($value);
        update_field($key,$input,$post);
        $stored=(string)get_metadata($kind,$id,$name,true);
        $reference=(string)get_metadata($kind,$id,'_'.$name,true);
        if (!$this->same_raw($value,$stored) || $reference!==$key) {
            throw new RuntimeException('ACF_ROUNDTRIP_FAILED:' . $name);
        }
        return true;
    }

    public function __invoke(array $args, array $opts): void {
        try {
            $snapshot=$this->current_source();
            $expected=$this->expected_items($snapshot['posts']);
            $values=$expected['items'];
            $zooms=$expected['zooms'];
            $course=$expected['course'];
            $errors=$expected['reference_errors'];
            $existing=$this->preexisting($values,$zooms,$course);
            WP_CLI::line('SOURCE_COUNT=' . count($snapshot['posts']));
            WP_CLI::line('SOURCE_META_COUNT=' . $snapshot['source_meta']);
            WP_CLI::line('SOURCE_FINGERPRINT=' . $snapshot['fingerprint']);
            WP_CLI::line('ACF_TARGET_PRESENT=' . count($values));
            WP_CLI::line('ACF_TARGET_EXISTING=' . $existing);
            WP_CLI::line('ZOOM_USER_COUNT=' . count($zooms));
            WP_CLI::line('ACF_COURSE_JSON_BYTES=' . strlen($course));
            WP_CLI::line('REFERENCE_ERRORS=' . $errors);
            if (!isset($opts['apply'])) {WP_CLI::success('DRY_RUN_ONLY');return;}
            if (!defined('ANST_ALLOW_ACF_WRITE') || ANST_ALLOW_ACF_WRITE !== true)
                throw new RuntimeException('ACF_WRITE_FLAG_OFF');
            if ((string)get_option('anst_writes_enabled','1') !== '0' ||
                (string)get_option('anst_trash_cleanup_enabled','1') !== '0')
                throw new RuntimeException('ACF_STUDIO_RUNTIME_NOT_LOCKED');
            if (count($snapshot['posts'])!==71 || $errors) throw new RuntimeException('ACF_SOURCE_COUNTS_OR_REFERENCES_CHANGED');
            if (!hash_equals($snapshot['fingerprint'],(string)($opts['expected-fingerprint']??'')))
                throw new RuntimeException('ACF_FINGERPRINT_CHANGED');
            $this->verify_backup((string)($opts['backup-dir']??''));
            $lock=(int)$this->wpdb->get_var("SELECT GET_LOCK('anst_acf_migrate_v1',0)");
            if ($lock!==1) throw new RuntimeException('ACF_MIGRATION_LOCKED');
            $started=false;
            try {
                if ($this->wpdb->query('START TRANSACTION')===false) throw new RuntimeException('ACF_TRANSACTION_FAILED');
                $started=true;
                $this->register_offline_acf();
                $written=0;$skipped=0;
                foreach ($values as $v) {
                    if ($this->save_one($v['post'],$v['key'],$v['name'],$v['raw'],$v['type']))$written++;
                    else $skipped++;
                }
                foreach ($zooms as $user=>$json) {
                    if ($this->save_one('user_'.$user,'field_anst16u_user_board_zoom_index_json_v1',
                        'studio_user_board_zoom_index_json',$json,'textarea'))$written++;
                    else $skipped++;
                }
                if ($this->save_one('option','field_anst16c_course_lesson_links_json_v1',
                    'studio_course_lesson_links_json',$course,'textarea'))$written++;
                else $skipped++;
                $after=$this->current_source();
                if (!hash_equals($snapshot['fingerprint'],$after['fingerprint'])) throw new RuntimeException('ACF_LEGACY_META_CHANGED');
                if ($this->wpdb->query('COMMIT')===false) throw new RuntimeException('ACF_COMMIT_FAILED');
                $started=false;
                WP_CLI::success('ACF_APPLY_VERIFIED written='.$written.' skipped='.$skipped);
            } catch (Throwable $e) {
                if ($started)$this->wpdb->query('ROLLBACK');
                wp_cache_flush();
                throw $e;
            } finally {
                $this->wpdb->get_var("SELECT RELEASE_LOCK('anst_acf_migrate_v1')");
            }
        } catch (Throwable $e) {
            WP_CLI::error('ACF_G5_HALTED:' . $e->getMessage());
        }
    }
}

WP_CLI::add_command('anst-acf-migrate','ANST_ACF_Migrator');
