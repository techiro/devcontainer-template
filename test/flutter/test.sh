#!/bin/bash
cd $(dirname "$0")
source ../test-utils/test-utils.sh

# Template specific tests
checkCommon

# Check if Flutter is installed and working
check "flutter" flutter --version

# Check if Dart is installed and working
check "dart" dart --version

# Check if Flutter doctor runs successfully
check "flutter-doctor" flutter doctor

# Report result
reportResults
