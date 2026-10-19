<?php
if(!defined('ANTHARES_AI_EXTERNAL_SECRETS_PROVIDERS'))define('ANTHARES_AI_EXTERNAL_SECRETS_PROVIDERS',array('gemini'));
if(!class_exists('Anthares_AI_Hub')||!class_exists('Anthares_AI_Provider_Gemini')){echo 'AI_HUB_CLASSES=UNAVAILABLE';exit(3);}
$settings=Anthares_AI_Hub::instance()->get_settings();
if(!isset($settings['gemini'])){echo 'GEMINI_SETTINGS=UNAVAILABLE';exit(4);}
$settings['gemini']['model']='gemini-2.5-flash';
$p=apply_filters('anthares_ai_providers',array('gemini'=>new Anthares_AI_Provider_Gemini($settings['gemini'])),$settings);
$provider=$p['gemini']??null;
if(!is_object($provider) || get_class($provider)!=='Anthares_AI_Secrets_Gemini_Provider'){echo 'SECRETS_SUBCLASS=FAIL';exit(5);}
$keys=$provider->get_api_keys();
if(count($keys)!==1){echo 'SECRETS_FAIL_CLOSED';exit(6);}
$r=$provider->request(array('prompt'=>'Responda somente OK.', 'max_tokens'=>24, 'temperature'=>0));
if(is_wp_error($r)){echo 'GEMINI_API_RESULT=ERROR_CODE_'.preg_replace('/[^a-z0-9_]/','',strtolower($r->get_error_code()));exit(7);}
if(!is_array($r)||empty($r['text'])){echo 'GEMINI_API_RESULT=EMPTY';exit(8);}
echo 'ANTHARES_GEMINI_REAL_REQUEST=PASS';
