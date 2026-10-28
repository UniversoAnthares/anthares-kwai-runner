<?php
declare(strict_types=1);
// Read-only proof of the separate Hostinger Git mirror. Never fetch or prune here.
header('Content-Type: text/plain; charset=utf-8');
header('Cache-Control: no-store');
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') { http_response_code(405); exit; }
function fail_closed(): void {
    http_response_code(503);
    echo "SYNC_RECEIPT_UNAVAILABLE\n";
    exit;
}
$base = '/home/u566597497/.anthares-forgejo/';
$receiptFile = $base . 'git-mirror-hostinger-status.json';
$repo = $base . 'data/repositories/anthares-admin/anthares-kwai-runner.git';
if (!is_file($receiptFile) || !is_dir($repo)) { fail_closed(); }
$raw = file_get_contents($receiptFile);
if ($raw === false || strlen($raw) > 50000) { fail_closed(); }
$receipt = json_decode($raw, true);
if (!is_array($receipt)
    || ($receipt['schema'] ?? '') !== 'anthares-hostinger-git-redundancy-v1'
    || ($receipt['source'] ?? '') !== 'GitHub'
    || ($receipt['target'] ?? '') !== 'Hostinger Forgejo'
    || ($receipt['no_force'] ?? null) !== true
    || ($receipt['no_prune'] ?? null) !== true
    || ($receipt['failures'] ?? null) !== []) { fail_closed(); }
$checked = strtotime((string) ($receipt['checked_utc'] ?? ''));
$age = $checked === false ? -1 : time() - $checked;
if ($age < 0 || $age > 2400) { fail_closed(); }
$row = $receipt['results']['anthares-kwai-runner'] ?? null;
if (!is_array($row)
    || !in_array(($row['state'] ?? ''), ['VERIFIED_ALL_SOURCE_REFS', 'SYNCED_FAST_FORWARD_VERIFIED'], true)) {
    fail_closed();
}
$expected = (string) ($row['sha'] ?? '');
if (!preg_match('/^[0-9a-f]{40}$/', $expected)) { fail_closed(); }
$output = [];
$exitCode = 1;
exec('/usr/bin/git --git-dir=' . escapeshellarg($repo)
    . ' rev-parse --verify refs/heads/main 2>/dev/null', $output, $exitCode);
if ($exitCode !== 0 || count($output) !== 1
    || trim($output[0]) !== $expected) { fail_closed(); }
echo "SYNC_PROVEN $expected\n";
