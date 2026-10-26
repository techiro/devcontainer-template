#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
cache_root="${XDG_CACHE_HOME:-$HOME/.cache}/devcontainer-template"
mkdir -p "$cache_root"
sample="$(mktemp -d "$cache_root/flutter.XXXXXX")"
reports="${SECURITY_REPORT_DIR:-$sample/security-reports}"
mkdir -p "$reports"
printf 'Smoke workspace: %s\n' "$sample"
cleanup() {
  while IFS= read -r container_id; do
    [ -z "$container_id" ] || docker rm -f "$container_id" >/dev/null || true
  done < <(docker ps -aq --filter "label=devcontainer.local_folder=$sample")
}
trap cleanup EXIT
export SAMPLE_DIR="$sample"
python3 - <<'PY'
import json, os, pathlib, shutil
source = pathlib.Path('src/flutter')
target = pathlib.Path(os.environ['SAMPLE_DIR'])
metadata = json.loads((source / 'devcontainer-template.json').read_text())
shutil.copy(source / 'Dockerfile', target / 'Dockerfile')
shutil.copytree(source / '.devcontainer', target / '.devcontainer')
config = target / '.devcontainer/devcontainer.json'
text = config.read_text()
for name, option in metadata['options'].items():
    text = text.replace('${templateOption:' + name + '}', option['default'])
assert '${templateOption:' not in text
config.write_text(text)
PY
devcontainer up --workspace-folder "$sample"
container_id="$(docker ps -q --filter "label=devcontainer.local_folder=$sample")"
source_image="$(docker inspect --format '{{.Config.Image}}' "$container_id")"
scan_ref="flutter-template-security:${container_id:0:12}"
docker image tag "$source_image" "$scan_ref"
docker image inspect --format '{{.Id}}' "$scan_ref" > "$reports/image-id.txt"
printf '%s\n' "$scan_ref" > "$reports/image-ref.txt"
devcontainer exec --workspace-folder "$sample" flutter --version --machine > "$reports/sdk-version.json"
python3 test/sdk_security_check.py "$reports/sdk-version.json" "$reports/sdk-advisories.json"
# Expand these variables inside the container, not on the runner.
# shellcheck disable=SC2016
devcontainer exec --workspace-folder "$sample" bash -c '
  set -euo pipefail
  test "$(id -un)" = vscode
  test -w "$FLUTTER_ROOT"
  test -w "$PUB_CACHE"
  if sudo -n true >/dev/null 2>&1; then
    echo "Unexpected passwordless sudo" >&2
    exit 1
  fi
  test -u /usr/lib/chromium/chrome-sandbox
  dpkg --compare-versions "$(dpkg-query -W -f="\${Version}" ca-certificates)" ge "20250419~deb12u2"
  openssl crl2pkcs7 -nocrl -certfile /etc/ssl/certs/ca-certificates.crt |
    openssl pkcs7 -print_certs -noout > /tmp/trusted-roots.txt
  if grep -E "emSign ECC Root CA - G3|AAA Certificate Services" /tmp/trusted-roots.txt; then
    echo "Distrusted CA remains in the active trust bundle" >&2
    exit 1
  fi
  "$CHROME_EXECUTABLE" --no-sandbox --headless=new --disable-dev-shm-usage \
    --allow-chrome-scheme-url --dump-dom chrome://sandbox > /tmp/chromium-sandbox.html
  python3 -c '\''import re; s=re.sub("<[^>]+>", " ", open("/tmp/chromium-sandbox.html").read()); s=" ".join(s.split()); required=["PID namespaces Yes", "Network namespaces Yes", "Seccomp-BPF sandbox Yes", "adequately sandboxed"]; assert all(token in s for token in required), s'\''
  flutter --version
  flutter create --platforms=web,linux --project-name=template_smoke .
  flutter analyze --fatal-infos
  flutter test
  flutter test --platform chrome
  flutter build web
  flutter build linux
'
# Reopening an existing Flutter project must also run pub get successfully.
devcontainer up --workspace-folder "$sample" --remove-existing-container
printf 'Flutter template smoke test passed.\n'
