#!/usr/bin/env bash
# Tek komutla Sepolia test ağına kurulum. Kullanım: bash kur-sepolia.sh
set -e
cd "$(dirname "$0")"
echo "=== DEX kurulumu (Sepolia test ağı) ==="
echo "Sadece bu iş için açılmış, içinde gerçek para olmayan bir cüzdan kullanın."
read -r -p "RPC adresi [Enter = herkese açık Sepolia RPC]: " RPC
RPC=${RPC:-https://ethereum-sepolia-rpc.publicnode.com}
read -r -s -p "Cüzdanın özel anahtarı (yazdıkça görünmez): " PK; echo
PK=$(echo "$PK" | tr -d '[:space:]'); [[ "$PK" == 0x* ]] || PK="0x$PK"
if ! [[ "$PK" =~ ^0x[0-9a-fA-F]{64}$ ]]; then echo "Özel anahtar 64 karakterlik onaltılık sayı olmalı."; exit 1; fi
read -r -p "Token adı [Alacam Token]: " AD; AD=${AD:-Alacam Token}
read -r -p "Token sembolü [ALC]: " SEMBOL; SEMBOL=${SEMBOL:-ALC}
read -r -p "Toplam arz [1000000000]: " ARZ; ARZ=${ARZ:-1000000000}
if ! [[ "$ARZ" =~ ^[0-9]+$ ]]; then echo "Arz sadece rakam olmalı."; exit 1; fi

PRIVATE_KEY="$PK" RPC_URL="$RPC" TOKEN_AD="$AD" TOKEN_SEMBOL="$SEMBOL" TOKEN_ARZ="$ARZ" WETH_ADDRESS="${WETH_ADDRESS:-}" \
  npx hardhat run scripts/deploy.js --network hedef
unset PK

echo
echo "=== Kurulum tamam ==="
echo "Web sitesini güncellemek için şu üç komutu çalıştırın:"
echo "  git add frontend/config.js"
echo "  git commit -m 'Sepolia adresleri'"
echo "  git push"
