<?php
$settings=get_option('anthares_ai_hub_settings', array());
$gem=is_array($settings)&&isset($settings['gemini'])&&is_array($settings['gemini'])?$settings['gemini']:array();
$pool=is_array($gem['api_keys']??null)?$gem['api_keys']:array();
if(isset($gem['api_key']) && is_string($gem['api_key']))array_unshift($pool,$gem['api_key']);
$pool=array_values(array_unique(array_filter(array_map('trim', array_filter($pool,'is_string')))));
foreach($pool as $key) {
    if($key==='')continue;
    $r=wp_remote_get('https://generativelanguage.googleapis.com/v1beta/models?pageSize=1', array('timeout'=>10,'headers'=>array('x-goog-api-key'=>$key)));
    if(!is_wp_error($r)&&200===(int)wp_remote_retrieve_response_code($r)){
        echo 'SELECTED_GEMINI_KEY_BASE64='.base64_encode($key);
        exit(0);
    }
}
fwrite(STDERR,'NO_GEMINI_KEY_VALIDATED');
exit(2);
