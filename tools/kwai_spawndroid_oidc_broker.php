<?php
/**
 * Kwai APK signed-link broker, authenticated only by GitHub Actions OIDC.
 * Deployment path: .well-known/anthares-kwai-apks/oidc-broker.php
 *
 * Independent of WordPress; never alters private APKs, handles uploads, or
 * authenticates Kwai accounts. No long-lived key leaves the Hostinger server.
 * PHP 7.4 compatible. The public endpoint is fail-closed.
 */
declare(strict_types=1);

header('Cache-Control: private, no-store, max-age=0');
header('Pragma: no-cache');
header('X-Content-Type-Options: nosniff');
header("Content-Security-Policy: default-src 'none'");

function refuse(int $code): void {
    if ($code === 503) {
        // One non-sensitive code location. Never store JWT or signed URLs.
        $trace = debug_backtrace(DEBUG_BACKTRACE_IGNORE_ARGS, 1);
        $line = (int)($trace[0]['line'] ?? 0);
        @file_put_contents(
            '/home/u566597497/.anthares-spawndroid-apks/oidc-broker-denials.log',
            gmdate('Y-m-d') . ' BROKER_INVENTORY_503_LINE_' . $line . PHP_EOL,
            FILE_APPEND | LOCK_EX
        );
    }
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    echo '{"ok":false}';
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    refuse(405);
}
$jwt = (string)($_SERVER['HTTP_X_GITHUB_OIDC_TOKEN'] ?? '');
if (strlen($jwt) < 100 || strlen($jwt) > 16000 ||
    !preg_match('/\A[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\z/D', $jwt)) {
    refuse(403);
}

function b64url(string $encoded): string {
    if (!preg_match('/\A[A-Za-z0-9_-]+\z/D', $encoded)) {
        throw new RuntimeException('INVALID_B64URL');
    }
    $value = base64_decode(strtr($encoded, '-_', '+/') .
        str_repeat('=', (4 - (strlen($encoded) % 4)) % 4), true);
    if ($value === false) {
        throw new RuntimeException('INVALID_B64URL');
    }
    return $value;
}
function derLen(int $length): string {
    if ($length < 128) return chr($length);
    if ($length < 256) return "\x81" . chr($length);
    if ($length < 65536) return "\x82" . pack('n', $length);
    throw new RuntimeException('INVALID_DER_LENGTH');
}
function derInt(string $bytes): string {
    $bytes = ltrim($bytes, "\x00");
    if ($bytes === '') $bytes = "\x00";
    if ((ord($bytes[0]) & 0x80) !== 0) $bytes = "\x00" . $bytes;
    return "\x02" . derLen(strlen($bytes)) . $bytes;
}
function publicKeyFromJwk(array $entry): string {
    if (($entry['kty'] ?? '') !== 'RSA' || ($entry['alg'] ?? '') !== 'RS256' ||
        ($entry['use'] ?? '') !== 'sig') {
        throw new RuntimeException('JWKS_KEY_INVALID');
    }
    $rsa = derInt(b64url((string)$entry['n'])) . derInt(b64url((string)$entry['e']));
    $rsa = "\x30" . derLen(strlen($rsa)) . $rsa;
    $algorithm = hex2bin('300d06092a864886f70d0101010500');
    $bit = "\x03" . derLen(strlen($rsa) + 1) . "\x00" . $rsa;
    $spki = "\x30" . derLen(strlen($algorithm) + strlen($bit)) . $algorithm . $bit;
    return "-----BEGIN PUBLIC KEY-----\n" .
        chunk_split(base64_encode($spki), 64, "\n") .
        "-----END PUBLIC KEY-----\n";
}
function fetchJwks(): array {
    $curl = curl_init('https://token.actions.githubusercontent.com/.well-known/jwks');
    if ($curl === false) throw new RuntimeException('JWKS_UNAVAILABLE');
    curl_setopt_array($curl, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => false,
        CURLOPT_CONNECTTIMEOUT => 5,
        CURLOPT_TIMEOUT => 9,
        CURLOPT_SSL_VERIFYPEER => true,
        CURLOPT_SSL_VERIFYHOST => 2,
        CURLOPT_MAXREDIRS => 0,
        CURLOPT_USERAGENT => 'Anthares-Kwai-OIDC-Broker/1.0',
    ]);
    $body = curl_exec($curl);
    $status = (int)curl_getinfo($curl, CURLINFO_RESPONSE_CODE);
    curl_close($curl);
    if (!is_string($body) || strlen($body) > 200000 || $status !== 200) {
        throw new RuntimeException('JWKS_UNAVAILABLE');
    }
    $parsed = json_decode($body, true);
    if (!is_array($parsed) || !isset($parsed['keys']) ||
        !is_array($parsed['keys'])) throw new RuntimeException('JWKS_INVALID');
    return $parsed['keys'];
}
function verifyGitHubOidc(string $jwt): void {
    $segments = explode('.', $jwt);
    if (count($segments) !== 3) throw new RuntimeException('JWT_SEGMENTS_INVALID');
    $header = json_decode(b64url($segments[0]), true);
    $claims = json_decode(b64url($segments[1]), true);
    if (!is_array($header) || !is_array($claims) ||
        ($header['alg'] ?? '') !== 'RS256' ||
        !isset($header['kid']) || !is_string($header['kid']) ||
        !preg_match('/\A[A-Za-z0-9._-]{5,128}\z/D', $header['kid'])) {
        throw new RuntimeException('JWT_HEADER_INVALID');
    }
    $now = time();
    $repository = 'UniversoAnthares/anthares-kwai-runner';
    $ref = 'refs/heads/feature/spawndroid-kwai-apk-verified-upload-20261114';
    $workflowRef = $repository .
        '/.github/workflows/kwai-spawndroid-stage-cloud-audit.yml@' . $ref;
    $required = [
        'iss' => 'https://token.actions.githubusercontent.com',
        'aud' => 'urn:anthares:kwai:apk-stage:v1',
        'sub' => 'repo:' . $repository . ':ref:' . $ref,
        'repository' => $repository,
        'ref' => $ref,
        'ref_type' => 'branch',
        'event_name' => 'push',
        'workflow_ref' => $workflowRef,
        'runner_environment' => 'github-hosted',
    ];
    foreach ($required as $key => $expected) {
        if (!isset($claims[$key]) || !is_string($claims[$key]) ||
            !hash_equals($expected, $claims[$key])) {
            // Only an allowlisted claim name is reported; never its value.
            throw new RuntimeException('JWT_CLAIM_DENIED_' . $key);
        }
    }
    $iat = $claims['iat'] ?? null;
    $exp = $claims['exp'] ?? null;
    $nbf = $claims['nbf'] ?? $iat;
    if (!is_int($iat) || !is_int($exp) || !is_int($nbf) ||
        $iat > $now + 30 || $iat < $now - 600 ||
        $nbf > $now + 30 || $exp <= $now || $exp > $now + 900) {
        throw new RuntimeException('JWT_TIME_INVALID');
    }
    $signature = b64url($segments[2]);
    $input = $segments[0] . '.' . $segments[1];
    $keyMatched = false;
    foreach (fetchJwks() as $entry) {
        if (!is_array($entry) || ($entry['kid'] ?? null) !== $header['kid']) continue;
        $keyMatched = true;
        $key = openssl_pkey_get_public(publicKeyFromJwk($entry));
        if ($key === false || openssl_verify($input, $signature, $key,
                OPENSSL_ALGO_SHA256) !== 1) {
            throw new RuntimeException('JWT_SIGNATURE_INVALID');
        }
        return;
    }
    if (!$keyMatched) throw new RuntimeException('JWT_KEY_UNRECOGNIZED');
}

try {
    verifyGitHubOidc($jwt);
} catch (Throwable $exception) {
    // Private, append-only diagnostic: fixed error code; never JWT, values,
    // URLs, IP addresses or account data. The public response remains 403.
    $reason = (string)$exception->getMessage();
    if (!preg_match('/\\A[A-Za-z0-9_]{4,80}\\z/D', $reason)) {
        $reason = 'OIDC_VALIDATION_FAILED';
    }
    $auditPath = '/home/u566597497/.anthares-spawndroid-apks/oidc-broker-denials.log';
    @file_put_contents($auditPath, gmdate('Y-m-d\\TH:i:s\\Z') .
        ' ' . $reason . PHP_EOL, FILE_APPEND | LOCK_EX);
    refuse(403);
}

$private = '/home/u566597497/.anthares-spawndroid-apks';
$package = 'com.kwai.video';
$dir = $private . '/' . $package;
$manifest = $dir . '/manifest.json';
$keyFile = $private . '/staging.key';
if (!is_readable($manifest) || !is_readable($keyFile)) refuse(503);
$key = base64_decode(trim((string)file_get_contents($keyFile)), true);
if ($key === false || strlen($key) !== 32) refuse(503);
$text = (string)file_get_contents($manifest);
$doc = json_decode(preg_replace('/^\xEF\xBB\xBF/', '', $text), true);
if (!is_array($doc) || ($doc['package'] ?? '') !== $package ||
    !isset($doc['files']) || !is_array($doc['files']) ||
    count($doc['files']) !== 25) refuse(503);

$files = [];
$expiry = time() + 1500;
$seen = [];
$total = 0;
foreach ($doc['files'] as $row) {
    if (!is_array($row)) refuse(503);
    $name = $row['name'] ?? '';
    $hash = $row['sha256'] ?? '';
    $size = $row['bytes'] ?? 0;
    if (!is_string($name) ||
        !preg_match('/\A(?:base|split_[a-zA-Z0-9_.-]+)\.apk\z/D', $name) ||
        isset($seen[$name]) || !is_string($hash) ||
        !preg_match('/\A[a-f0-9]{64}\z/D', $hash) ||
        !is_int($size) || $size < 1000 || $size > 170000000 ||
        !is_file($dir . '/' . $name) || is_link($dir . '/' . $name) ||
        filesize($dir . '/' . $name) !== $size) refuse(503);
    $seen[$name] = true;
    $total += $size;
    $sig = hash_hmac('sha256', $package . '|' . $name . '|' . $expiry, $key);
    $files[] = [
        'name' => $name, 'bytes' => $size, 'sha256' => $hash,
        'url' => 'https://anthares.us/.well-known/anthares-kwai-apks/signed/' .
                 $expiry . '/' . $sig . '/' . $name,
    ];
}
if (!isset($seen['base.apk']) || $total !== 202108730) refuse(503);
header('Content-Type: application/json; charset=utf-8');
echo json_encode([
    'package' => $package, 'versionCode' => 647103,
    'files' => $files, 'expiresAt' => $expiry,
], JSON_UNESCAPED_SLASHES);
