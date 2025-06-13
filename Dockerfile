# Flutter DevContainer
FROM ghcr.io/cirruslabs/flutter:latest

LABEL org.opencontainers.image.source="https://github.com/techiro/flutter-devcontainer"
LABEL org.opencontainers.image.description="Flutter DevContainer for VS Code and Codespaces"
LABEL org.opencontainers.image.licenses="MIT"

# 作業ディレクトリを設定
WORKDIR /workspace

# 必要なファイルをコピー（現時点では基本的な設定のみ）
COPY . .

# Flutter の pub cache を設定
ENV PUB_CACHE=/workspace/.pub-cache

# デフォルトコマンド
CMD ["/bin/bash"]
