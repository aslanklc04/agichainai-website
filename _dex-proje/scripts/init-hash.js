// UniswapV2Pair bayt kodunun hash'ini hesaplar ve Router kütüphanesine yazar.
// Kendi derlemenizle kurduğunuz Factory'nin havuz adreslerini doğru bulması için şart.
// Kullanım: npx hardhat compile && node scripts/init-hash.js && npx hardhat compile
const fs = require("fs");
const path = require("path");
const { keccak256 } = require("ethers");

const pair = require("../artifacts/contracts/core/UniswapV2Pair.sol/UniswapV2Pair.json");
const hash = keccak256(pair.bytecode).slice(2);
const lib = path.join(__dirname, "../contracts/periphery/libraries/UniswapV2Library.sol");
const src = fs.readFileSync(lib, "utf8");
const yeni = src.replace(/hex'[0-9a-f]{64}' \/\/ init code hash/, `hex'${hash}' // init code hash`);
fs.writeFileSync(lib, yeni);
console.log(src === yeni ? "Hash zaten güncel:" : "Hash güncellendi:", "0x" + hash);
