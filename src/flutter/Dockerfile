# syntax=docker/dockerfile:1
FROM mcr.microsoft.com/devcontainers/base:2-bookworm

ARG FLUTTER_VERSION=3.47.8

LABEL org.opencontainers.image.source="https://github.com/techiro/devcontainer-template"
LABEL org.opencontainers.image.description="Flutter DevContainer for VS Code and Codespaces"
LABEL org.opencontainers.image.licenses="MIT"

# Chromium is available for both amd64 and arm64 on Debian. Ubuntu's Chromium
# package requires snap, which is unsuitable for a development container.
RUN apt-get update \
    && apt-get upgrade -y --with-new-pkgs \
    && apt-get install -y --no-install-recommends \
        ca-certificates chromium chromium-sandbox clang cmake ninja-build pkg-config libgtk-3-dev \
        libglu1-mesa libstdc++-12-dev unzip xz-utils zip \
    && dpkg --compare-versions "$(dpkg-query -W -f='${Version}' ca-certificates)" ge '20250419~deb12u2' \
    && rm -f /etc/sudoers.d/vscode \
    && test -z "$(apt-get -s upgrade | sed -n 's/^Inst //p')" \
    && rm -rf /var/lib/apt/lists/*

ENV FLUTTER_ROOT=/home/vscode/flutter \
    PUB_CACHE=/home/vscode/.pub-cache \
    CHROME_EXECUTABLE=/usr/local/bin/chromium-sandboxed
ENV PATH="${FLUTTER_ROOT}/bin:${PUB_CACHE}/bin:${PATH}"

# Flutter's Chrome test launcher injects --no-sandbox for headless runs. Strip
# that argument so tests and IDE launches both retain Chromium's sandbox.
RUN <<'SH'
cat > /usr/local/bin/chromium-sandboxed <<'BASH'
#!/bin/bash
set -euo pipefail
args=()
for arg in "$@"; do
    case "$arg" in
        --no-sandbox) continue ;;
        --no-sandbox=*|--disable-setuid-sandbox*|--disable-seccomp-filter-sandbox*)
            printf 'Refusing to disable Chromium sandbox: %s\n' "$arg" >&2
            exit 64 ;;
    esac
    args+=("$arg")
done
exec /usr/bin/chromium "${args[@]}"
BASH
chmod 0555 /usr/local/bin/chromium-sandboxed
SH

# Install from the upstream SDK rather than an unmaintained third-party image.
# Keep the SDK and package cache writable by VS Code's non-root user.
RUN git clone --depth 1 --branch "${FLUTTER_VERSION}" https://github.com/flutter/flutter.git "${FLUTTER_ROOT}" \
    && mkdir -p "${PUB_CACHE}" \
    && chown -R vscode:vscode "${FLUTTER_ROOT}" "${PUB_CACHE}"

USER vscode
RUN flutter config --no-analytics --enable-web --enable-linux-desktop \
    && dart --disable-analytics \
    && flutter precache --web --linux \
    && flutter --version

# Match the advertised Web/Linux toolchain; Android can be enabled after adding
# an Android SDK to a project-specific derived image.
RUN flutter config --no-enable-android

WORKDIR /home/vscode

CMD ["/bin/bash"]
