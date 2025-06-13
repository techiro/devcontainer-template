# Flutter Dev Container Templates 🚀

**A collection of Dev Container Templates for Flutter development**

This repository provides ready-to-use Dev Container Templates for Flutter app development with VS Code or GitHub Codespaces.

## Available Templates

### Flutter 🦋

Instant Flutter development environment — just launch and start coding!

- **Template ID**: `flutter`
- **Description**: Complete Flutter development setup with Dart SDK and VS Code extensions
- **Documentation**: [src/flutter/README.md](src/flutter/README.md)

## Quick Start ✨

### Option 1: Use in VS Code Dev Containers

1. Open VS Code
2. Install the "Dev Containers" extension
3. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
4. Select "Dev Containers: Add Dev Container Configuration Files..."
5. Choose "Show All Definitions..."
6. Search for "Flutter" and select this template

### Option 2: Use in GitHub Codespaces

1. Create a new repository or open an existing one
2. Click "Code" → "Codespaces" → "Configure dev container"
3. Search for "Flutter" template
4. Select and customize as needed

### Option 3: Manual Setup

Add to your project's `.devcontainer/devcontainer.json`:

```json
{
  "name": "Flutter DevContainer",
  "image": "ghcr.io/techiro/flutter-devcontainer/flutter:latest"
}
```

## Features 🌟

- Latest **Flutter** and **Dart** SDKs 🐦
- Pre-installed VS Code extensions: Dart & Flutter 🧑‍💻
- Works out-of-the-box with VS Code Dev Containers and GitHub Codespaces 💻
- Automatic build & distribution via GitHub Container Registry (GHCR) 📦

## Template Structure

```
├── src/
│   └── flutter/
│       ├── devcontainer-template.json
│       ├── .devcontainer/
│       │   └── devcontainer.json
│       ├── Dockerfile
│       └── README.md
├── test/
│   ├── flutter/
│   │   └── test.sh
│   └── test-utils/
│       └── test-utils.sh
└── .github/
    └── workflows/
        └── publish.yml
```

## Development & Contribution 🤝

### Local Testing

```bash
# Test the Flutter template
./test/flutter/test.sh
```

### Publishing

Templates are automatically published to GHCR when changes are pushed to the `main` branch.

## License 📄

MIT License - See the [LICENSE](LICENSE) file for details.

This template collection is based on the [devcontainers/template-starter](https://github.com/devcontainers/template-starter) and follows the [Dev Container Template specification](https://containers.dev/implementors/templates-distribution/).
