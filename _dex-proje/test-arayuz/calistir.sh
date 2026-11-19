#!/usr/bin/env bash
# Arayüz testleri: yerel zincir kurar, DEX'i yükler, iki test dosyasını tarayıcıda çalıştırır.
# Gerekenler: pip install playwright && playwright install chromium
set -e
cd "$(dirname "$0")/.."
npx hardhat node > /tmp/dex-node.log 2>&1 &
NODE=$!; trap 'kill $NODE 2>/dev/null' EXIT
sleep 6
K=$(grep -m1 "Private Key" /tmp/dex-node.log | awk '{print $3}')
PRIVATE_KEY=$K TOKEN_AD="Alacam Token" TOKEN_SEMBOL=ALC TOKEN_ARZ=1000000000 RPC_URL=http://127.0.0.1:8545 \
  npx hardhat run scripts/deploy.js --network hedef > /dev/null
npx hardhat run scripts/e2e-kurulum.js --network localhost > /dev/null
python3 test-arayuz/temel_akis.py frontend
python3 test-arayuz/uc_durumlar.py frontend
echo "Not: Testler frontend/config.js dosyasını yerel adreslerle değiştirdi. Gerçek kurulumda deploy betiği tekrar yazar."
