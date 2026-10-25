
# Flutter (flutter)

A non-root Flutter environment for VS Code Dev Containers and Codespaces on `linux/amd64` and `linux/arm64`. The default SDK is **Flutter 3.47.7** (latest stable verified on 2026-10-26); Dart comes bundled with Flutter.

The container installs the [official Flutter SDK](https://github.com/flutter/flutter), Chromium, and the dependencies for Flutter Web and Linux desktop builds. The previous Cirrus Labs image is no longer used because its publisher [announced the end of updates](https://github.com/cirruslabs/docker-images-flutter).

## Apply to an existing project

Start a Docker-compatible runtime and install VS Code's [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).

The template writes `Dockerfile` and `.devcontainer/` into the target folder. Commit or back up existing configuration first, or apply it to an empty folder to inspect the files. From your project's root folder, apply the published template:

```sh
npx --yes @devcontainers/cli@0.89.0 templates apply \
  --template-id ghcr.io/techiro/devcontainer-template/flutter:2 \
  --template-args '{"flutterVersion":"3.47.7"}'
```

Then open the folder in VS Code and run **Dev Containers: Reopen in Container**.

For a local checkout before publication, copy `Dockerfile` and `.devcontainer/` from this template into your project root, then replace `${templateOption:flutterVersion}` in `.devcontainer/devcontainer.json` with `3.47.7`. The workspace uses VS Code's default mount location, so the opened folder is the same folder shown in the Explorer and terminal. The supplied debug configurations are installed as container settings; no `.vscode/launch.json` needs to be overwritten.

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

For full Dart breakpoint debugging without a container desktop, select **Flutter Web (headless Chrome)** in VS Code's Run and Debug view, set a breakpoint in `lib/main.dart`, and press **F5**. This debugs the Chromium session inside the container; opening the preview in a host browser creates a separate browser session. Chromium's sandbox is disabled only for this container debug launch, which runs as the unprivileged `vscode` user.

The second supplied configuration, **Flutter Web (browser preview)**, starts the web-server device on port 3000. Use this for interactive preview in your host browser, subject to the web-server debugging limits described above.

Widget tests can also be debugged directly: open `test/widget_test.dart`, set a breakpoint, then click **Debug** above the test. Linux desktop compilation works with `flutter build linux`; displaying a Linux desktop app requires a display server.

## SDK selection and updates

| Option | Description | Default |
|---|---|---|
| `flutterVersion` | Upstream Flutter tag, or `stable` for the stable branch | `3.47.7` |

Select `stable` to resolve the newest stable SDK on a fresh image build. To refresh a cached SDK, use **Dev Containers: Rebuild Container Without Cache**. An existing project can also edit `build.args.FLUTTER_VERSION` in its generated `.devcontainer/devcontainer.json` and rebuild. The SDK and pub cache are writable by `vscode`; neither is stored under the workspace mount.

Version 2 replaces the unused `imageVariant` option with `flutterVersion` and ships the Dockerfile with the template. Dependabot checks the actual Dockerfile directory and GitHub Actions weekly. CI validates both architectures before publishing.

## Platform limits

Android SDKs, emulators, and connected-device forwarding are not bundled. Android support is disabled to match the installed tools; add an Android toolchain appropriate to your project and run `flutter config --enable-android` if needed. Building or running iOS/macOS apps requires a macOS host with Xcode outside this Linux container.
