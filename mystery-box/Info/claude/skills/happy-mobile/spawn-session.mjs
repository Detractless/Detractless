#!/usr/bin/env node
// Spawn a Happy session bound to a directory, so it shows up on the paired
// phone without anyone typing a path there.
//
// Usage: node spawn-session.mjs [directory] [--agent claude|codex|gemini]
//                               [--permission-mode <mode>] [--create-dir]
// Prints JSON: { ok, sessionId, directory, httpPort } or { ok:false, ... }

import { readFileSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { homedir } from 'node:os';
import { execFileSync } from 'node:child_process';

const HAPPY_HOME = process.env.HAPPY_HOME_DIR || join(homedir(), '.happy');
const STATE = join(HAPPY_HOME, 'daemon.state.json');

const argv = process.argv.slice(2);
const flag = (name, fallback = null) => {
  const i = argv.indexOf(name);
  return i === -1 ? fallback : argv[i + 1];
};
const positional = argv.filter((a, i) =>
  !a.startsWith('--') && !(i > 0 && argv[i - 1].startsWith('--') && argv[i - 1] !== '--create-dir'));

const directory = resolve(positional[0] || process.cwd());
const agent = flag('--agent', 'claude');
const permissionMode = flag('--permission-mode');
const approvedNewDirectoryCreation = argv.includes('--create-dir');

const die = (msg, extra = {}) => {
  console.log(JSON.stringify({ ok: false, error: msg, ...extra }, null, 2));
  process.exit(1);
};

function readState() {
  if (!existsSync(STATE)) return null;
  try { return JSON.parse(readFileSync(STATE, 'utf8')); } catch { return null; }
}

async function alive(port) {
  try {
    const r = await fetch(`http://127.0.0.1:${port}/status`, { signal: AbortSignal.timeout(3000) });
    return r.ok;
  } catch { return false; }
}

let state = readState();
if (!state?.httpPort || !(await alive(state.httpPort))) {
  // Daemon down or stale — start it. happy.cmd on Windows, happy elsewhere.
  const bin = process.platform === 'win32' ? 'happy.cmd' : 'happy';
  try {
    execFileSync(bin, ['daemon', 'start'], { stdio: 'pipe', shell: process.platform === 'win32' });
  } catch (e) {
    die('Could not start the happy daemon. Is `happy` installed and on PATH?', {
      detail: String(e.message || e).slice(0, 400),
    });
  }
  await new Promise((r) => setTimeout(r, 2500));
  state = readState();
  if (!state?.httpPort) die('Daemon started but wrote no httpPort to ' + STATE);
}

const body = { directory, agent, approvedNewDirectoryCreation };
if (permissionMode) body.permissionMode = permissionMode;

let res;
try {
  res = await fetch(`http://127.0.0.1:${state.httpPort}/spawn-session`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(30000),
  });
} catch (e) {
  die('Could not reach the daemon control server.', {
    port: state.httpPort, detail: String(e.message || e).slice(0, 400),
  });
}

const text = await res.text();
let json;
try { json = JSON.parse(text); } catch { json = { raw: text.slice(0, 600) }; }

if (res.status === 409 && json?.actionRequired === 'CREATE_DIRECTORY') {
  die(`Directory does not exist: ${directory}. Re-run with --create-dir to have the daemon create it.`,
    { actionRequired: 'CREATE_DIRECTORY', directory });
}
if (!res.ok || json?.success === false) {
  die(`Daemon returned HTTP ${res.status}`, { response: json });
}

console.log(JSON.stringify({
  ok: true,
  sessionId: json.sessionId ?? null,
  directory,
  agent,
  httpPort: state.httpPort,
}, null, 2));
