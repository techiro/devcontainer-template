#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
cache_root="${XDG_CACHE_HOME:-$HOME/.cache}/devcontainer-template"
mkdir -p "$cache_root"
sample="$(mktemp -d "$cache_root/flutter.XXXXXX")"
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
# Expand these variables inside the container, not on the runner.
# shellcheck disable=SC2016
devcontainer exec --workspace-folder "$sample" bash -c '
  set -euo pipefail
  test "$(id -un)" = vscode
  test -w "$FLUTTER_ROOT"
  test -w "$PUB_CACHE"
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
