#!/usr/bin/env bash
# Kod kapsamı ölçümü. Coverage aracı Pair kontratını değiştirdiği için (sayaç ekler)
# Router'daki init code hash geçici olarak ölçüm sürümüne göre ayarlanır, sonra geri alınır.
set -e
cd "$(dirname "$0")/.."
LIB=contracts/periphery/libraries/UniswapV2Library.sol
cp "$LIB" /tmp/lib.yedek
trap 'cp /tmp/lib.yedek "$LIB"; npx hardhat compile >/dev/null 2>&1 || true' EXIT
npx hardhat coverage >/dev/null 2>&1 || true
node scripts/init-hash.js >/dev/null
npx hardhat coverage
