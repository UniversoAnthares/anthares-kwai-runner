import { access, readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const repo = resolve(process.cwd(), '..');
const required = [
  'anthares-remote-agent/go.mod',
  'anthares-remote-agent/cmd/agent',
  'appveyor.yml',
  'azure-pipelines.yml',
  '.github/workflows/ci-primary.yml'
];

for (const rel of required) {
  await access(resolve(repo, rel));
}

const gomod = await readFile(resolve(repo, 'anthares-remote-agent/go.mod'), 'utf8');
if (!gomod.includes('github.com/UniversoAnthares/anthares-kwai-runner/anthares-remote-agent')) {
  throw new Error('unexpected Go module identity');
}

console.log('Anthares Cloudflare CI structural gate: PASS');
