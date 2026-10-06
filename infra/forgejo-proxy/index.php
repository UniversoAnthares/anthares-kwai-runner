<?php
declare(strict_types=1);
$socket = '/home/u566597497/.anthares-forgejo/forgejo.sock';
$prefix = '/forgejo';
$uri = $_SERVER['REQUEST_URI'] ?? '/';
$path = substr($uri, strlen($prefix));
if ($path === false || $path === '') $path = '/';
$ch = curl_init();
curl_setopt($ch, CURLOPT_UNIX_SOCKET_PATH, $socket);
curl_setopt($ch, CURLOPT_URL, 'http://unix' . $path);
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $_SERVER['REQUEST_METHOD'] ?? 'GET');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, false);
curl_setopt($ch, CURLOPT_TIMEOUT, 300);
$headers = [];
foreach (getallheaders() as $k => $v) {
    $lk = strtolower($k);
    if (in_array($lk, ['host','content-length','connection'], true)) continue;
    $headers[] = $k . ': ' . $v;
}
$headers[] = 'Host: anthares.us';
$headers[] = 'X-Forwarded-Proto: https';
$headers[] = 'X-Forwarded-Host: anthares.us';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
if (!in_array($method, ['GET','HEAD'], true)) {
    curl_setopt($ch, CURLOPT_POSTFIELDS, file_get_contents('php://input'));
}
$responseHeaders = [];
curl_setopt($ch, CURLOPT_HEADERFUNCTION, function($ch, $line) use (&$responseHeaders) {
    $len = strlen($line);
    $parts = explode(':', $line, 2);
    if (count($parts) === 2) $responseHeaders[] = [trim($parts[0]), trim($parts[1])];
    return $len;
});
$body = curl_exec($ch);
if ($body === false) { http_response_code(502); echo 'Forgejo origin unavailable'; exit; }
http_response_code((int)curl_getinfo($ch, CURLINFO_RESPONSE_CODE));
foreach ($responseHeaders as [$name,$value]) {
    $ln = strtolower($name);
    if (in_array($ln, ['transfer-encoding','connection','content-length'], true)) continue;
    if ($ln === 'location') $value = str_replace('http://unix/', 'https://anthares.us/forgejo/', $value);
    header($name . ': ' . $value, false);
}
curl_close($ch);
echo $body;
