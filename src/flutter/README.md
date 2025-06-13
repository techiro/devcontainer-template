# Flutter Dev Container Template 🚀

**Instant Flutter development environment — just launch and start coding! 🦋**

## What's Included

- Latest **Flutter** and **Dart** SDKs 🐦
- Pre-installed VS Code extensions: Dart & Flutter 🧑‍💻
- Works out-of-the-box with VS Code Dev Containers and GitHub Codespaces 💻
- Automatic build & distribution via GitHub Container Registry (GHCR) 📦

## Usage

### Option 1: Use this template directly

1. Click "Use this template" button
2. Open in VS Code
3. Select "Reopen in Container"
4. Start building your Flutter app immediately! 🎉

### Option 2: Add to existing project

Create `.devcontainer/devcontainer.json` in your project:

```json
{
  "name": "Flutter DevContainer",
  "image": "ghcr.io/techiro/flutter-devcontainer:latest",
  "customizations": {
    "vscode": {
      "extensions": [
        "Dart-Code.dart-code",
        "Dart-Code.flutter"
      ]
    }
  },
  "postCreateCommand": "flutter pub get",
  "remoteUser": "root",
  "workspaceFolder": "/workspace"
}
```

## Template Options

- **imageVariant**: Choose Flutter version (`latest` or `stable`)

## License

MIT License - See the [LICENSE](../../LICENSE) file for details.
