<?php
declare(strict_types=1);
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') { http_response_code(405); exit; }
$state = '/home/u566597497/.anthares-forgejo/sync.state';
$lockf = fopen('/home/u566597497/.anthares-forgejo/sync.lock', 'c');
if (!$lockf || !flock($lockf, LOCK_EX | LOCK_NB)) { http_response_code(409); exit; }
$last = is_file($state) ? (int)file_get_contents($state) : 0;
if (time() - $last < 300) { echo "SYNC_RECENT\n"; exit; }
$repo = '/home/u566597497/.anthares-forgejo/data/repositories/anthares-admin/anthares-kwai-runner.git';
$cmd = '/usr/bin/git --git-dir=' . escapeshellarg($repo) . ' fetch --prune origin ' .
       escapeshellarg('+refs/heads/*:refs/heads/*') . ' ' .
       escapeshellarg('+refs/tags/*:refs/tags/*') . ' 2>&1';
$out=[]; $rc=1; exec($cmd, $out, $rc);
if ($rc !== 0) { http_response_code(502); echo "SYNC_FAILED\n"; exit; }
file_put_contents($state, (string)time(), LOCK_EX);
$sha = trim((string)shell_exec('/usr/bin/git --git-dir=' . escapeshellarg($repo) . ' rev-parse refs/heads/main'));
echo "SYNC_PROVEN " . preg_replace('/[^0-9a-f]/', '', $sha) . "\n";
