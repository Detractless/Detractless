---
name: happy-mobile
description: Hand off the current project to the user's phone via Happy — spawn a Happy session bound to this exact working directory so it appears in the paired mobile app with no path typed by hand. Use when the user says they are heading out, wants to continue on their phone, asks to "set this up for mobile", "make this available on my phone", "send this to Happy", "start a remote session", or asks whether the daemon is running. Also use to stop or list those sessions. Do NOT use for ordinary local work, or for questions about Claude Code itself.
---

# Happy mobile handoff

Happy (`slopus/happy`) mirrors a Claude Code session to a paired phone. Sessions
normally only exist for terminals the user launched with `happy` themselves —
this skill removes that limit by asking Happy's local daemon to spawn one for the
directory already in play.

## Why this exists

Without it, starting a session from the phone means browsing the filesystem in
the mobile UI and typing an absolute Windows path. The user works in the Claude
Code desktop UI, not a terminal, so the path is already known here and should
never have to be retyped there.

## Do this

Run the helper from the directory you want on the phone:

```bash
node ~/.claude/skills/happy-mobile/spawn-session.mjs
```

Pass a directory explicitly when it differs from the cwd:

```bash
node ~/.claude/skills/happy-mobile/spawn-session.mjs "C:/path/to/project"
```

Flags: `--agent claude|codex|gemini` (default `claude`),
`--permission-mode <mode>`, `--create-dir`.

It prints JSON. On success, report the `sessionId` to the user and tell them the
project is now listed in the Happy app — nothing to type on the phone.

The helper starts the daemon itself if it is down, so there is no separate setup
step. It never creates a directory unless `--create-dir` is passed.

## Handling failures

- `actionRequired: "CREATE_DIRECTORY"` — the path does not exist. **Ask the user
  before re-running with `--create-dir`.** Do not create directories silently.
- "Could not start the happy daemon" — check `happy.cmd doctor`. Most likely
  `happy` is not on PATH, or Claude Code is not installed as an npm global
  (Happy resolves `@anthropic-ai/claude-code` from the npm global root; a
  hand-written `claude` shim on PATH does **not** satisfy it).
- "Could not reach the daemon control server" — stale `daemon.state.json`. Run
  `happy.cmd doctor clean`, then retry.

## Related commands

```bash
happy.cmd daemon status     # is it up, which port
happy.cmd daemon list       # active sessions
happy.cmd daemon stop       # stop daemon; existing sessions stay alive
happy.cmd doctor clean      # kill runaway happy processes
```

On Windows, prefer `happy.cmd` over `happy` — PowerShell resolves the `.ps1`
first and the user's execution policy blocks it.

## Facts worth not re-deriving

- Daemon control server: `http://127.0.0.1:<httpPort>`, port in
  `~/.happy/daemon.state.json`. Endpoint `POST /spawn-session`, body
  `{directory, sessionId?, agent?, permissionMode?, modelMode?, effortLevel?,
  environmentVariables?, approvedNewDirectoryCreation?}`.
- The phone reaches the same code path through the machine RPC handler
  `spawn-happy-session`.
- State lives in `~/.happy` (`HAPPY_HOME_DIR` overrides): `sessions.json` is the
  only directory index, plus `settings.json`, `daemon.state.json`, `access.key`,
  `logs/`.
- No reboot autostart on Windows — `happy daemon install` is macOS-only. Any
  `happy` agent command auto-starts the daemon, and so does this helper.
