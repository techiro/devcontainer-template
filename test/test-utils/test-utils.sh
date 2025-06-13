#!/bin/bash

FAILED=()

check() {
    LABEL=$1
    shift
    echo -e "\n🧪 Testing $LABEL"
    if "$@"; then
        echo "✅ Passed!"
        return 0
    else
        echo "❌ $LABEL check failed."
        FAILED+=("$LABEL")
        return 1
    fi
}

checkCommon() {
    check "non-root-user" id ${_REMOTE_USER}
    check "locale" [ $(locale -a | grep en_US.utf8) ]
    check "sudo" sudo echo "sudo works"
    check "git" git --version
    check "command-line-tools" which curl wget unzip
}

reportResults() {
    if [ ${#FAILED[@]} -ne 0 ]; then
        echo -e "\n💥 Failed tests: ${FAILED[*]}"
        exit 1
    else
        echo -e "\n💯 All tests passed!"
        exit 0
    fi
}
