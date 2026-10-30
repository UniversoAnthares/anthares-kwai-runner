<?php
declare(strict_types=1);
header('Content-Type: application/json');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
function finish(int $status,array $body): never {http_response_code($status);echo json_encode($body);exit;}
if(($_SERVER['REQUEST_METHOD']??'')!=='GET')finish(405,['error'=>'method_not_allowed']);
if((int)($_SERVER['CONTENT_LENGTH']??0)>0)finish(400,['error'=>'unexpected_body']);
$parts=parse_url($_SERVER['REQUEST_URI']??'');
if(($parts['path']??'')!=='/anthares-independent/status.php'||isset($parts['query']))finish(400,['error'=>'invalid_path']);
$input=['method'=>'GET','path'=>'/anthares-independent/status.php','query'=>'',
 'signer'=>$_SERVER['HTTP_X_ARA_SIGNER']??'','timestamp'=>$_SERVER['HTTP_X_ARA_TIMESTAMP']??'',
 'signature'=>$_SERVER['HTTP_X_ARA_SIGNATURE']??''];
if($input['signer']!=='anthares-remote-mcp'||!preg_match('/^[0-9]{13}$/D',$input['timestamp'])||
 !preg_match('/^[A-Za-z0-9_-]{86}$/D',$input['signature'])||
 abs((int)floor(microtime(true)*1000)-(int)$input['timestamp'])>30000)finish(401,['error'=>'unauthorized']);
$private=dirname(__DIR__,2).'/anthares-secure/independent-service';
$config=json_decode(@file_get_contents($private.'/config.json'),true);
if(!is_array($config)||!isset($config['node_binary'])||!is_executable($config['node_binary'])||
 !function_exists('proc_open'))finish(503,['error'=>'service_unavailable']);
umask(0077);
$lock=@fopen($private.'/rate.json','c+');
if(!$lock||!flock($lock,LOCK_EX))finish(503,['error'=>'service_unavailable']);
try {
 $raw=stream_get_contents($lock);$rate=json_decode($raw?:'{}',true);$window=intdiv(time(),60);
 $count=(($rate['window']??-1)===$window)?(int)($rate['count']??0):0;
 if($count>=20)finish(429,['error'=>'request_budget_exhausted']);
 ftruncate($lock,0);rewind($lock);fwrite($lock,json_encode(['window'=>$window,'count'=>$count+1]));fflush($lock);
}finally{flock($lock,LOCK_UN);fclose($lock);}
$pipes=[];$process=null;$output='';
try {
 $process=proc_open([$config['node_binary'],$private.'/handler.mjs'],
   [0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes,$private);
 if(!is_resource($process))throw new RuntimeException('start_failed');
 fwrite($pipes[0],json_encode($input));fclose($pipes[0]);unset($pipes[0]);
 stream_set_blocking($pipes[1],false);stream_set_blocking($pipes[2],false);
 $deadline=microtime(true)+6.0;
 while(true){
  $output.=stream_get_contents($pipes[1]);stream_get_contents($pipes[2]);
  if(strlen($output)>65536)throw new RuntimeException('oversized_output');
  $state=proc_get_status($process);if(!$state['running'])break;
  if(microtime(true)>$deadline)throw new RuntimeException('deadline');
  usleep(20000);
 }
 $output.=stream_get_contents($pipes[1]);
 $data=json_decode($output,true);if(!is_array($data))throw new RuntimeException('invalid_output');
 $status=(int)($data['_http_status']??503);unset($data['_http_status']);
 if(!in_array($status,[200,401,503],true))throw new RuntimeException('invalid_status');
}catch(Throwable $e){$status=503;$data=['error'=>'service_unavailable'];}
finally {
 if(is_resource($process)){
  $state=proc_get_status($process);
  if($state['running']){proc_terminate($process,15);usleep(100000);$state=proc_get_status($process);if($state['running'])proc_terminate($process,9);}
 }
 foreach($pipes as $pipe)if(is_resource($pipe))fclose($pipe);
 if(is_resource($process))proc_close($process);
}
finish($status,$data);
