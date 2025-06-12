# Flutter DevContainer

VS Code/Codespaces 向け Flutter 開発用 DevContainer イメージ

## 概要

このリポジトリは、VS Code の Remote-Containers 機能や GitHub Codespaces で Flutter 開発を行うためのDevContainer設定を提供します。

## 特徴

- **Flutter 3.7.7** をベースとしたコンテナ環境
- **Dart Code** と **Flutter** 拡張機能が自動でインストール
- GitHub Container Registry (GHCR) での自動ビルド・配信
- VS Code DevContainer 設定済み

## 使用方法

### 1. VS Code での使用

1. このリポジトリをクローン
2. VS Code で開く
3. 「Reopen in Container」を選択
4. Flutter 開発環境が自動で構築されます

### 2. GitHub Codespaces での使用

1. GitHub リポジトリページで「Code」→「Codespaces」→「Create codespace on main」を選択
2. 自動でFlutter開発環境が構築されます

### 3. カスタムプロジェクトでの使用

既存のFlutterプロジェクトに追加する場合：

```bash
mkdir .devcontainer
```

`.devcontainer/devcontainer.json`:
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

## 含まれるツール

- Flutter SDK (3.7.7)
- Dart SDK
- Git
- VS Code 拡張機能
  - Dart Code
  - Flutter

## 開発・貢献

### ローカルビルド

```bash
docker build -t ghcr.io/techiro/flutter-devcontainer:latest .
docker run --rm -it ghcr.io/techiro/flutter-devcontainer:latest flutter --version
```

### CI/CD

このリポジトリは GitHub Actions を使用して自動的にコンテナイメージをビルドし、GHCR に配信します。

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照してください。
