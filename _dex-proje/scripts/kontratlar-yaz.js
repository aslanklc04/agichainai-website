// Kurulum sayfası (frontend/kur.html) için derlenmiş kontratları frontend/kontratlar.js dosyasına yazar.
// Kullanım: npm run derle && node scripts/kontratlar-yaz.js
const fs = require("fs");
const path = require("path");
const { keccak256 } = require("ethers");
const A = (p) => { const a = require(path.join(__dirname, "../artifacts/contracts", p)); return { abi: a.abi, bytecode: a.bytecode }; };
const o = {
  WETH9: A("periphery/WETH9.sol/WETH9.json"),
  Factory: A("core/UniswapV2Factory.sol/UniswapV2Factory.json"),
  Router: A("periphery/UniswapV2Router02.sol/UniswapV2Router02.json"),
  Token: A("token/GuvenliToken.sol/GuvenliToken.json"),
  pairInitHash: keccak256(require("../artifacts/contracts/core/UniswapV2Pair.sol/UniswapV2Pair.json").bytecode),
};
fs.writeFileSync(path.join(__dirname, "../frontend/kontratlar.js"),
  "// scripts/kontratlar-yaz.js tarafından üretildi. Elle düzenlemeyin.\nwindow.DEX_KONTRATLAR = " + JSON.stringify(o) + ";\n");
console.log("frontend/kontratlar.js yazıldı. Pair init hash:", o.pairInitHash);
