#!/bin/bash
# shellcheck disable=SC1091
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)" || exit
source "${SCRIPT_DIR}/../test-utils/test-utils.sh"

# Flutterの基本コマンドのテスト
runTest "Flutter CLI" flutter --version
runTest "Dart CLI" dart --version

# Flutter doctorのチェック
runTest "Flutter環境診断" flutter doctor

# テスト結果の表示
showTestSummary
