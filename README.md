# Flutter DevContainer 🚀

**Instant Flutter development environment for everyone — just launch and start coding! 🦋**

A ready-to-use DevContainer image for seamless Flutter app development with VS Code or GitHub Codespaces. No setup required.

## Getting Started ✨

1. **Clone this repository** 📥
2. **Open in VS Code** 🖥️
3. **Select "Reopen in Container"** 🧩
4. Start building your Flutter app immediately! 🎉

Or, use it in your own project by adding the following to your `.devcontainer/devcontainer.json`:

```json
{
  "image": "ghcr.io/techiro/flutter-devcontainer:latest"
}
```

---

## Features 🌟

- Latest **Flutter** and **Dart** SDKs 🐦
- Pre-installed VS Code extensions: Dart & Flutter 🧑‍💻
- Works out-of-the-box with VS Code Dev Containers and GitHub Codespaces 💻
- Automatic build & distribution via GitHub Container Registry (GHCR) 📦

## How to Use the Published Image 🐳

### 1. Use directly with Docker command

Anyone can pull the image with:

```bash
docker pull ghcr.io/techiro/flutter-devcontainer:latest
```

### 2. Use in devcontainer.json

```json
{
  "image": "ghcr.io/techiro/flutter-devcontainer:latest"
}
```

### 3. Use as a base image in Dockerfile

```dockerfile
FROM ghcr.io/techiro/flutter-devcontainer:latest
```

## Development & Contribution 🤝

### Local Build

```bash
docker build -t ghcr.io/techiro/flutter-devcontainer:latest .
docker run --rm -it ghcr.io/techiro/flutter-devcontainer:latest flutter --version
```

### CI/CD ⚙️

This repository uses GitHub Actions to automatically build and distribute the container image to GHCR.

## License 📄

MIT License - See the [LICENSE](LICENSE) file for details.

This image is based on cirruslabs/flutter (MIT) and Flutter SDK (BSD 3-Clause).
