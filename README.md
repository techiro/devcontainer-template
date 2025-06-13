# Flutter DevContainer

VS Code/Codespaces 向け Flutter 開発用 DevContainer イメージ

## 概要

このリポジトリは、VS Code の Remote-Containers 機能や GitHub Codespaces で Flutter 開発を行うための DevContainer 設定を提供します。

## 特徴

- **Flutter (latest)** をベースとしたコンテナ環境
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
2. 自動で Flutter 開発環境が構築されます

### 3. カスタムプロジェクトでの使用

既存の Flutter プロジェクトに追加する場合：

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

## 含まれるツール・設定

- Flutter SDK (latest)
- Dart SDK
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

## GHCR（GitHub Container Registry）への公開手順

1. **リポジトリをパブリックに設定**
   - GitHubリポジトリの「Settings」→「Danger Zone」→「Change repository visibility」から「Public」に変更

2. **イメージのパブリック化**
   - 初回push後、[パッケージページ](https://github.com/users/<ユーザー名>/packages/container/<パッケージ名>)にアクセス
   - 「Package settings」→「Public」に変更

3. **（必要に応じて）PATの作成と利用**
   - [Personal access tokens (classic)](https://github.com/settings/tokens/new?scopes=write:packages) で `write:packages` スコープを付与して作成
   - 手動pushや他リポジトリからpullする場合は、以下のコマンドでログイン
     ```bash
     echo $CR_PAT | docker login ghcr.io -u <GitHubユーザー名> --password-stdin
     ```


5. **CI/CD（GitHub Actions）による自動ビルド・公開**
   - `main`ブランチにpushすると自動でGHCRにイメージが公開されます
   - `.github/workflows/publish.yml`を参照

## 公開イメージの使い方

### 1. Docker コマンドで直接利用

パブリックイメージの場合、どなたでも以下のコマンドでイメージを取得できます。

```bash
docker pull ghcr.io/techiro/flutter-devcontainer:latest
```

### 2. devcontainer.json での利用

VS Code Dev Containers や GitHub Codespaces で利用する場合は、
`devcontainer.json` の `image` プロパティに指定してください。

```json
{
  "image": "ghcr.io/techiro/flutter-devcontainer:latest"
}
```

### 3. Dockerfile のベースイメージとして利用

独自のカスタマイズを加えたい場合は、Dockerfile の `FROM` 行で指定できます。

```dockerfile
FROM ghcr.io/techiro/flutter-devcontainer:latest
```

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照してください。

本イメージは cirruslabs/flutter（MIT）および Flutter SDK（BSD 3-Clause）をベースにしています。
