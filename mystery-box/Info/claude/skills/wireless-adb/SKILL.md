---
name: wireless-adb
description: Connect to the user's Android phone over wireless ADB (same Wi-Fi as this PC). Use whenever a task needs `adb` against the phone, ADB says "no devices", or a prior connection went stale. Handles first-time pairing, mDNS auto-discovery, and the case where the phone's paired session expired and the user must re-open Wireless Debugging settings to hand over a fresh pairing code.
---

# Wireless ADB to the user's phone

## What this covers
The user's test phone (Pixel 9 Pro XL) is paired to this PC over wireless ADB. There is **no USB connection** — everything is Wi-Fi. Both devices must be on the same LAN.

The ADB path on this machine is:
`C:\Users\Calibro1\AppData\Local\Android\Sdk\platform-tools\adb.exe`

## Step 1 — Try to reconnect (fast path)

Most of the time the phone is still paired and just needs `adb connect`. Run mDNS discovery, grab the `_adb-tls-connect._tcp` line, and connect.

```bash
ADB="$LOCALAPPDATA/Android/Sdk/platform-tools/adb.exe"
"$ADB" mdns services 2>&1 | grep "_adb-tls-connect"
# Example line:
#   adb-46131FDAS007SR-cYRwmA  _adb-tls-connect._tcp  192.168.1.201:36285
"$ADB" connect 192.168.1.201:36285      # use the IP:port from the line above
"$ADB" devices                          # should list the device as "device", not "unauthorized"
```

If `adb devices` shows the device — done. Skip to "Cleanup tips".

## Step 2 — Reconnect fails? Ask the user to re-pair

Wireless ADB sessions expire (reboot, network change, timeout). When they do, `mdns services` may return nothing OR the connect will fail. **You cannot fix this from the PC alone — the user must walk through the phone's Wireless Debugging screen.**

Tell the user this, verbatim-ish:

> Your phone's ADB pairing expired. On the phone:
> 1. Open **Settings → System → Developer options → Wireless debugging**.
> 2. Make sure "Wireless debugging" is toggled **on**.
> 3. Tap **"Pair device with pairing code"** — this shows a **6-digit code**, an IP:port, and the phone's name.
> 4. Read me the **IP:port** and the **6-digit code** (both change every time).
>
> Also make sure the phone is on the same Wi-Fi network as this PC. If you switched networks recently, re-connect to Wi-Fi first.

Then pair using what they give you:

```bash
ADB="$LOCALAPPDATA/Android/Sdk/platform-tools/adb.exe"
"$ADB" pair 192.168.1.201:41234 123456    # IP:port and code from the phone
# After successful pair, connect on the (different) main port:
"$ADB" mdns services | grep "_adb-tls-connect"
"$ADB" connect 192.168.1.201:36285
"$ADB" devices
```

Two important gotchas:
- The **pairing port** (from "Pair device with pairing code") is DIFFERENT from the **connect port** (from mDNS or the main Wireless Debugging screen). Pair first, then connect on the connect port.
- The pairing code is **one-time** — if it times out on the phone before you pair, ask for a fresh one.

## Step 3 — Duplicate device entries

If `adb devices` shows the same phone twice — once as an IP and once as a long `adb-...tcp` mDNS name — subsequent commands will error with `more than one device/emulator`. Disconnect the mDNS entry:

```bash
"$ADB" disconnect adb-46131FDAS007SR-cYRwmA._adb-tls-connect._tcp
"$ADB" devices    # should now show only the IP:port entry
```

Prefer keeping the `IP:port` entry (short, easier to `-s` target).

## Sanity check the phone is really there

Once `adb devices` shows one `device`, confirm it's the phone (not an emulator that also happens to be running):

```bash
"$ADB" shell getprop ro.product.model     # expect "Pixel 9 Pro XL" or similar
"$ADB" shell getprop ro.build.version.release
```

## When it still won't connect

Ask the user to check, in order:
- Same Wi-Fi network as this PC? (Different SSID or a guest network won't work — devices must be able to reach each other.)
- Is Wireless Debugging still on? (Turning phone off/on flips it off sometimes.)
- Is a VPN active on the phone or PC? Disable and retry.
- If all else fails: on the phone, tap **"Forget"** on this PC's paired computer entry, then repeat Step 2 from scratch.

## Cleanup tips

- `adb kill-server` then `adb start-server` resets ADB cleanly without touching the phone side. Use when connections behave weirdly.
- Don't run `adb devices` in a tight loop while the emulator or phone is booting — ADB will get flaky.
