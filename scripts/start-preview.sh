#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
port="${MOTIN_PREVIEW_PORT:-3000}"
[[ "$port" =~ ^[0-9]+$ ]] && ((port >= 1024 && port <= 65535)) || {
  echo 'MOTIN_PREVIEW_PORT deve estar entre 1024 e 65535.' >&2
  exit 1
}
ready() {
  local html
  html="$(curl --fail --silent --max-time 2 "http://127.0.0.1:$port/")" || return 1
  grep -q 'Remotion' <<<"$html" &&
    grep -Fq "window.remotion_publicFolderExists = \"$PWD/public\"" <<<"$html"
}

if ready; then
  echo "A prévia já está rodando na porta $port."
  exit 0
fi
if curl --silent --max-time 2 "http://127.0.0.1:$port/" >/dev/null; then
  echo "A porta $port está ocupada por outro serviço. Escolha outra com MOTIN_PREVIEW_PORT." >&2
  exit 1
fi

nohup npm run dev -- --port="$port" >/tmp/motin-preview.log 2>&1 </dev/null &
preview_pid=$!
for attempt in {1..30}; do
  if ready; then
    echo "Prévia pronta. Abra a porta $port na aba Ports do Codespaces."
    exit 0
  fi
  if ! kill -0 "$preview_pid" 2>/dev/null; then
    cat /tmp/motin-preview.log
    exit 1
  fi
  sleep 1
done
echo 'A prévia não respondeu. Consulte /tmp/motin-preview.log.' >&2
exit 1
