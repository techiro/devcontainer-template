
# Flutter (flutter)

A non-root Flutter environment for VS Code Dev Containers and Codespaces on `linux/amd64` and `linux/arm64`. The default SDK is **Flutter 3.47.8** (security fix for GHSA-frr6-h895-5pxp; bundled Dart 3.13.7); Dart comes bundled with Flutter.

The container installs the [official Flutter SDK](https://github.com/flutter/flutter), Chromium, and the dependencies for Flutter Web and Linux desktop builds. The previous Cirrus Labs image is no longer used because its publisher [announced the end of updates](https://github.com/cirruslabs/docker-images-flutter).

## Apply to an existing project

Start a Docker-compatible runtime and install VS Code's [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).

The template writes `Dockerfile` and `.devcontainer/` into the target folder. Commit or back up existing configuration first, or apply it to an empty folder to inspect the files. From your project's root folder, apply the published template:

```sh
npx --yes @devcontainers/cli@0.89.0 templates apply \
  --template-id ghcr.io/techiro/devcontainer-template/flutter:2 \
  --template-args '{"flutterVersion":"3.47.8"}'
```

Then open the folder in VS Code and run **Dev Containers: Reopen in Container**.

For a local checkout before publication, copy `Dockerfile` and `.devcontainer/` from this template into your project root, then replace `${templateOption:flutterVersion}` in `.devcontainer/devcontainer.json` with `3.47.8`. The workspace uses VS Code's default mount location, so the opened folder is the same folder shown in the Explorer and terminal. The supplied debug configurations are installed as container settings; no `.vscode/launch.json` needs to be overwritten.

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
| `flutterVersion` | Upstream Flutter tag, or `stable` for the stable branch | `3.47.8` |

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

Each architecture produces a `security-*` artifact containing SDK versions/advisory results, the installed CLI's npm audit and lockfile, the tested image ID, the complete Trivy **OS package** report, an OS SBOM, and a security summary. The scanner image and workflow actions use immutable digests/commit SHAs.

The SDK check queries published advisories from `dart-lang/sdk` and `flutter/flutter`. A vulnerable stable SDK, unavailable/incomplete feed, or an unsupported High/Critical advisory format fails the check. The CLI npm audit gates reported High/Critical npm findings; it does not independently analyze every dependency bundled into the CLI's JavaScript.

The OS gate blocks **fixable High/Critical** findings. Unfixed findings remain in the full report and summary and require explicit release review; passing CI does not mean zero CVEs. The image check verifies that the scanner inspected the same image used by the smoke test. It does not scan arbitrary future project dependencies or claim complete third-party library coverage.

The publish job targets the `ghcr` GitHub Environment. Before merging a release change, an administrator must configure its required reviewer and main-only deployment policy. Repository branch rules, Actions SHA enforcement, and secret protection are GitHub settings and must be verified separately from these source files.
