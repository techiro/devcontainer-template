# Flutter DevContainer
FROM ghcr.io/cirruslabs/flutter:latest

LABEL org.opencontainers.image.source="https://github.com/techiro/flutter-devcontainer"
LABEL org.opencontainers.image.description="Flutter DevContainer for VS Code and Codespaces"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /workspace

COPY . .

ENV PUB_CACHE=/workspace/.pub-cache

CMD ["/bin/bash"]
