#!/usr/bin/env bash
# Read-only public connectivity checks. Does not change DNS, proxy or TLS settings.
set -uo pipefail
SITE='https://mphill-lab-tracker.github.io/MPHILL-research-2026'
HOST='mphill-lab-tracker.github.io'
command -v curl >/dev/null || { echo 'curl is required: sudo apt install curl' >&2; exit 1; }
printf 'TED2 public connectivity report | %s UTC\n' "$(date -u '+%Y-%m-%d %H:%M:%S')"
printf 'Run once on Wi-Fi and again through your phone hotspot with Wi-Fi disabled on the phone.\nDo not publish private account information; this report only probes public URLs.\n\n'
printf 'Local clock: '; date -u
printf '\nDNS answers via the operating system:\n'
if command -v getent >/dev/null; then getent ahosts "$HOST" || true; fi
for family in 4 6; do
  for path in '/' '/connection-check/' '/light/' '/release.json'; do
    printf '\nIPv%s %s%s\n' "$family" "$SITE" "$path"
    code=0
    curl "-$family" --proto '=https' --proto-redir '=https' --location --max-redirs 3 \
      --connect-timeout 12 --max-time 25 --silent --show-error --output /dev/null \
      --write-out 'HTTP %{http_code} | address %{remote_ip} | DNS %{time_namelookup}s | TLS %{time_appconnect}s | total %{time_total}s | bytes %{size_download}\n' \
      "$SITE$path" || code=$?
    case "$code" in
      0) ;;
      6) printf 'DNS lookup failed on this network. No website code was received.\n';;
      7) printf 'The destination could not be reached (routing, firewall or host).\n';;
      28) printf 'Connection or transfer timed out. Compare the Wi-Fi result.\n';;
      35|51|60) printf 'TLS/certificate negotiation failed. Check the device clock and trusted certificates; do not disable verification.\n';;
      *) printf 'curl exit status: %s\n' "$code";;
    esac
  done
done
printf '\nAn IPv6 failure alone is not a site failure when IPv4 succeeds. A 404 on new diagnostic pages means V6.1 has not yet been published there.\n'
printf 'If both network tests succeed but the phone browser fails, record the exact browser error, phone OS/browser and mobile carrier.\n'
