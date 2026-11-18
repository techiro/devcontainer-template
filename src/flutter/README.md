
# Flutter (flutter)

A non-root Flutter environment for VS Code Dev Containers and Codespaces on `linux/amd64` and `linux/arm64`. The default SDK is **Flutter 3.47.9** (includes the security fix for GHSA-frr6-h895-5pxp; bundled Dart 3.13.7); Dart comes bundled with Flutter.

The container installs the [official Flutter SDK](https://github.com/flutter/flutter), Chromium, and the dependencies for Flutter Web and Linux desktop builds. The previous Cirrus Labs image is no longer used because its publisher [announced the end of updates](https://github.com/cirruslabs/docker-images-flutter).

## Apply to an existing project

Start a Docker-compatible runtime and install VS Code's [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).

The template writes `Dockerfile` and `.devcontainer/` into the target folder. Commit or back up existing configuration first, or apply it to an empty folder to inspect the files. From your project's root folder, apply the published template:

```sh
npx --yes @devcontainers/cli@0.90.0 templates apply \
  --template-id ghcr.io/techiro/devcontainer-template/flutter:2 \
  --template-args '{"flutterVersion":"3.47.9"}'
```

Then open the folder in VS Code and run **Dev Containers: Reopen in Container**.

For a local checkout before publication, copy `Dockerfile` and `.devcontainer/` from this template into your project root, then replace `${templateOption:flutterVersion}` in `.devcontainer/devcontainer.json` with `3.47.9`. The workspace uses VS Code's default mount location, so the opened folder is the same folder shown in the Explorer and terminal. The supplied debug configurations are installed as container settings; no `.vscode/launch.json` needs to be overwritten.

## Start a new application

Opening an empty project works: dependency installation runs only when `pubspec.yaml` exists. In the container terminal, run:

```sh
flutter create --platforms=web,linux .
flutter analyze
flutter test
```

When opening this template repository itself, create your sample in a subfolder to preserve the repository README:

```sh
flutter create --platforms=web,linux /tmp/flutter_sample
cd /tmp/flutter_sample
flutter analyze
flutter test
```

Open `/tmp/flutter_sample` with **File: Open Folder** inside the connected container before using its debug configurations.

## Run and debug

For a browser preview, start the web server in the container:

```sh
flutter run -d web-server --web-hostname=0.0.0.0 --web-port=3000
```

Open port **3000** from VS Code's **Ports** panel in your host browser. In Codespaces, keep the forwarded port private. The web-server device has [limited debugging support](https://docs.flutter.dev/platform-integration/web/setup).

For full Dart breakpoint debugging without a container desktop, select **Flutter Web (headless Chrome)** in VS Code's Run and Debug view, set a breakpoint in `lib/main.dart`, and press **F5**. This debugs the Chromium session inside the container; opening the preview in a host browser creates a separate browser session. Chromium must run with its namespace and Seccomp-BPF sandboxes enabled, as the unprivileged `vscode` user. The launcher strips the unsafe `--no-sandbox` argument that Flutter injects into headless test launches. Passwordless sudo is removed.

The second supplied configuration, **Flutter Web (browser preview)**, starts the web-server device on port 3000. Use this for interactive preview in your host browser, subject to the web-server debugging limits described above.

Widget tests can also be debugged directly: open `test/widget_test.dart`, set a breakpoint, then click **Debug** above the test. Linux desktop compilation works with `flutter build linux`; displaying a Linux desktop app requires a display server.

## SDK selection and updates

| Option | Description | Default |
|---|---|---|
| `flutterVersion` | Upstream Flutter tag, or `stable` for the stable branch | `3.47.9` |

Select `stable` to resolve the newest stable SDK on a fresh image build. To refresh a cached SDK, use **Dev Containers: Rebuild Container Without Cache**. An existing project can also edit `build.args.FLUTTER_VERSION` in its generated `.devcontainer/devcontainer.json` and rebuild. The SDK and pub cache are writable by `vscode`; neither is stored under the workspace mount.

Version 2 replaces the unused `imageVariant` option with `flutterVersion` and ships the Dockerfile with the template. Dependabot checks the actual Dockerfile directory and GitHub Actions weekly. CI validates both architectures before publishing. Workflow actions use full commit SHAs; scheduled validation does not publish releases.

## Platform limits

Android SDKs, emulators, and connected-device forwarding are not bundled. Android support is disabled to match the installed tools; add an Android toolchain appropriate to your project and run `flutter config --enable-android` if needed. Building or running iOS/macOS apps requires a macOS host with Xcode outside this Linux container.

## Security update requirements

Flutter 3.47.8 / Dart 3.13.7 is the minimum for [GHSA-frr6-h895-5pxp](https://github.com/dart-lang/sdk/security/advisories/GHSA-frr6-h895-5pxp). Rebuild existing containers without cache and rebuild Linux binaries; updating template metadata does not repair previously built images or binaries.

Before downloading the SDK, the Dockerfile updates installed Debian packages and requires `ca-certificates >= 20250419~deb12u2`. It fails the build if upgrades remain pending. A successful build and smoke test alone do not establish the absence of vulnerabilities; inspect the SDK advisory and image scan results separately.

### Chromium sandbox profile

The included seccomp profile is derived from [Playwright's Docker profile at commit ae935a4](https://github.com/microsoft/playwright/blob/ae935a43d9e376e4759548f6b3c6905c7b282333/utils/docker/seccomp_profile.json), under the included `LICENSE.seccomp` (Apache-2.0). It retains a deny-by-default syscall policy while allowing `clone`, `setns`, and `unshare` for Chromium's user namespaces. The local compatibility adjustment returns `ENOSYS` for `clone3`, allowing glibc to fall back to `clone`. The container does not request `SYS_ADMIN`, privileged mode, or an unconfined seccomp policy.

The devcontainer configuration resolves this profile on the Docker client's filesystem. If a host's AppArmor or namespace restrictions prevent startup, investigate the host's per-application policy; do not work around the failure with `--no-sandbox`. CI requires Chromium's own diagnostic page to report PID and network namespaces and Seccomp-BPF enabled. That check deliberately supplies Flutter's unsafe argument to verify that the launcher removes it.

### CI reports and release policy

Audits run on pull requests, pushes to `main`, and every Monday at 03:17 UTC (12:17 Japan time), on both amd64 and arm64 runners. To run an audit manually, open **Actions → Validate and Publish Dev Container Templates → Run workflow** and leave **publish** unchecked. PRs, scheduled runs, and manual audits with `publish=false` do not publish templates. A push to `main`, or an explicit manual `publish=true` run on `main`, can publish only after both validation jobs succeed and the `ghcr` environment permits deployment.

Each validation job writes an audit table to its Actions **Summary**. The states are `pass` (合格), `findings` (blocking vulnerabilities), `error` (execution/report failure), and `skipped` (missing prerequisite). It also shows build/test outcomes and unfixed OS High/Critical findings requiring review. Counts refer to packages for npm, package/advisory pairs for SDKs, and package/CVE pairs for the OS; they are not interchangeable unique-CVE counts.

Download the architecture-specific `security-*` **Artifacts** from the run page. Reports are retained for 14 days:

- `audit-summary.json` and `.md`: combined decision, per-audit states, failure reasons, commit SHA, run URL/attempt, timestamp, architecture, image ID, SDK and tool versions.
- `cli-audit.json`, `cli-package-lock.json`, and npm logs: the installed CLI's audit and dependency evidence.
- `sdk-version.json` and `sdk-advisories.json`: actual SDK versions, fetched advisory pages (including partial results), evaluations and errors.
- `image-id.txt`, `image-ref.txt`, `os-vulnerabilities.json`, `os-sbom.cdx.json`, `security-summary.json`, and Trivy version/logs: tested-image identity, the complete **OS package** scan, SBOM, and fixable/unfixed findings.

The scanner image and workflow actions use immutable digests/commit SHAs. Audit steps run independently once their prerequisites exist: an npm finding does not skip the build, and a later smoke-test failure does not suppress SDK/OS audits when their evidence was already captured. Missing or malformed reports, failed mandatory steps, and incomplete audits block publication. The final gate runs after report collection; a cancelled or forcibly timed-out runner may be unable to upload artifacts and is not a successful validation.

The SDK check queries published advisories from `dart-lang/sdk` and `flutter/flutter`. A vulnerable stable SDK, unavailable/incomplete feed, or an unsupported High/Critical advisory format fails the check. The CLI npm audit gates reported High/Critical npm findings; it does not independently analyze every dependency bundled into the CLI's JavaScript.

The OS gate blocks **fixable High/Critical** findings. Unfixed findings remain in the full report and summary and require explicit release review; passing CI does not mean zero CVEs. The image check verifies that the scanner inspected the same image used by the smoke test. It does not scan arbitrary future project dependencies or claim complete third-party library coverage.

### Investigating and rerunning audits

For `findings`, inspect the advisory/package and upgrade the affected SDK, CLI, or OS packages, then rerun validation. Unfixed OS High/Critical findings remain **要確認** even when the automated gate passes. The gate is not a claim of zero vulnerabilities.

For `error`, inspect the named raw report and stderr file or step log. SDK HTTP 401/403 indicates an authentication or permission problem: verify the workflow's `GITHUB_TOKEN` and repository/organization Actions policy. Do not paste tokens into reports or disable the check. SDK connection failures, HTTP 429 and 5xx receive up to three retries after the initial request (1, 2, and 4 seconds); persistent failures remain errors. Malformed or incomplete advisory feeds also remain errors.

For `skipped`, fix the failed prerequisite listed in the summary, such as CLI installation or container startup. GitHub-hosted runners must reach npm, GitHub's advisory API, container registries, Debian mirrors, Flutter downloads/pub.dev, and Trivy's vulnerability database. An unavailable endpoint is an incomplete audit, not a clean result.

After correcting the cause, use **Re-run failed jobs** (or **Re-run all jobs**) on the run page, or start a new manual audit with **publish** unchecked. Rerunning a publishing run retains its original publication intent, so use a new manual audit when only verification is wanted. The weekly trigger takes effect once this workflow is merged into the default branch. The shell smoke test now performs build/runtime validation only; CI invokes the independent audit scripts and aggregate gate separately.

The publish job targets the `ghcr` GitHub Environment. Before merging a release change, an administrator must configure its required reviewer and main-only deployment policy. Repository branch rules, Actions SHA enforcement, and secret protection are GitHub settings and must be verified separately from these source files.
