#!/bin/bash

FAILED=()

# テストを実行して結果を確認する
runTest() {
    testName="${1}"
    shift

    echo -e "\n🧪 テスト実行: ${testName}"

    if "$@"; then
        showSuccess "${testName}"
        return 0
    else
        showFailure "${testName}"
        return 1
    fi
}

# テスト成功時の処理
showSuccess() {
    echo "✅ テスト成功!"
}

# テスト失敗時の処理
showFailure() {
    testName="${1}"
    echo "❌ テスト失敗: ${testName}"
    FAILED+=("${testName}")
}

# 最終的なテスト結果を表示
showTestSummary() {
    if [[ ${#FAILED[@]} -eq 0 ]]; then
        echo -e "\n💯 すべてのテストが成功しました!"
        exit 0
    else
        echo -e "\n💥 失敗したテスト: ${FAILED[*]}"
        exit 1
    fi
}
