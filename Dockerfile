# Flutter DevContainer
FROM cirrusci/flutter:latest

# 作業ディレクトリを設定
WORKDIR /workspace

# 必要なファイルをコピー（現時点では基本的な設定のみ）
COPY . .

# Flutter の pub cache を設定
ENV PUB_CACHE=/workspace/.pub-cache

# Flutter コマンドのパスを通す
ENV PATH="$PATH:/home/cirrus/sdks/flutter/bin"

# デフォルトコマンド
CMD ["/bin/bash"]
