// DEX kurulum betiği: WETH (gerekirse), Factory, Router ve isteğe bağlı token.
// Kullanım (Sepolia örneği):
//   RPC_URL=https://... PRIVATE_KEY=0x... npx hardhat run scripts/deploy.js --network hedef
// Ayarlar (isteğe bağlı ortam değişkenleri):
//   WETH_ADDRESS  Ağın resmî WETH adresi. Verilmezse yeni bir WETH9 kurulur.
//   TOKEN_AD, TOKEN_SEMBOL, TOKEN_ARZ  Verilirse sabit arzlı bir token da kurulur.
//   SAHIP_ADRESI  Verilirse kurulumdan sonra token'ların tamamı, Factory ücret yetkisi
//                 ve kalan ETH bu adrese devredilir (kurulum cüzdanında hiçbir şey kalmaz).
const fs = require("fs");
const path = require("path");
const hre = require("hardhat");
const { ethers } = hre;

async function main() {
  const [kurucu] = await ethers.getSigners();
  if (!kurucu) throw new Error("PRIVATE_KEY tanımlı değil.");
  const ag = await ethers.provider.getNetwork();
  console.log(`Ağ: ${hre.network.name} (chainId ${ag.chainId})`);
  console.log(`Kurucu: ${kurucu.address}, bakiye: ${ethers.formatEther(await ethers.provider.getBalance(kurucu.address))}`);

  const sahip = process.env.SAHIP_ADRESI ? ethers.getAddress(process.env.SAHIP_ADRESI.trim()) : null;
  if (sahip) console.log("Devredilecek adres:", sahip);

  // Bakiye kontrolü: kurulum yaklaşık 12 milyon gas harcar
  const ucret = await ethers.provider.getFeeData();
  const gasFiyati = ucret.maxFeePerGas || ucret.gasPrice || 0n;
  const gerekli = 12_500_000n * gasFiyati;
  const bakiye = await ethers.provider.getBalance(kurucu.address);
  console.log(`Gas fiyatı: ${ethers.formatUnits(gasFiyati, "gwei")} gwei, tahmini gereken: ${ethers.formatEther(gerekli)} ETH`);
  if (hre.network.name !== "hardhat" && bakiye < gerekli)
    throw new Error(`Bakiye yetersiz: ${ethers.formatEther(bakiye)} ETH var, yaklaşık ${ethers.formatEther(gerekli)} ETH gerekli. Adres: ${kurucu.address}`);

  // Güvenlik kontrolü: Router kütüphanesindeki hash, Pair bayt koduyla eşleşmeli.
  const pairArt = await hre.artifacts.readArtifact("UniswapV2Pair");
  const hash = ethers.keccak256(pairArt.bytecode).slice(2);
  const lib = fs.readFileSync(path.join(__dirname, "../contracts/periphery/libraries/UniswapV2Library.sol"), "utf8");
  if (!lib.includes(hash)) throw new Error("Init code hash uyuşmuyor. Önce: node scripts/init-hash.js && npx hardhat compile");

  let weth = process.env.WETH_ADDRESS;
  if (!weth) {
    const W = await ethers.deployContract("WETH9");
    await W.waitForDeployment();
    weth = await W.getAddress();
    console.log("WETH9 kuruldu:", weth);
  } else {
    console.log("Mevcut WETH kullanılıyor:", weth);
  }

  const factory = await ethers.deployContract("UniswapV2Factory", [kurucu.address]);
  await factory.waitForDeployment();
  console.log("Factory:", await factory.getAddress());

  const router = await ethers.deployContract("UniswapV2Router02", [await factory.getAddress(), weth]);
  await router.waitForDeployment();
  console.log("Router:", await router.getAddress());

  let token = null;
  if (process.env.TOKEN_AD && process.env.TOKEN_SEMBOL && process.env.TOKEN_ARZ) {
    const T = await ethers.deployContract("GuvenliToken", [process.env.TOKEN_AD, process.env.TOKEN_SEMBOL, BigInt(process.env.TOKEN_ARZ)]);
    await T.waitForDeployment();
    token = await T.getAddress();
    console.log(`Token ${process.env.TOKEN_SEMBOL}:`, token);
  }

  if (sahip && sahip !== kurucu.address) {
    if (token) {
      const T = await ethers.getContractAt("GuvenliToken", token);
      await (await T.transfer(sahip, await T.balanceOf(kurucu.address))).wait();
      console.log("Token'ların tamamı devredildi.");
    }
    await (await factory.setFeeToSetter(sahip)).wait();
    console.log("Factory ücret yetkisi devredildi.");
    // Kalan ETH'yi geri gönder (gas payı bırakarak)
    const kalan = await ethers.provider.getBalance(kurucu.address);
    const fd = await ethers.provider.getFeeData();
    const gp = (fd.maxFeePerGas || fd.gasPrice || 0n) * 2n;
    const pay = 21000n * gp;
    if (kalan > pay * 2n) {
      await (await kurucu.sendTransaction({ to: sahip, value: kalan - pay, gasLimit: 21000n, maxFeePerGas: gp, maxPriorityFeePerGas: fd.maxPriorityFeePerGas || 1n })).wait();
      console.log(`Kalan ${ethers.formatEther(kalan - pay)} ETH geri gönderildi.`);
    }
  }

  const cikti = {
    chainId: Number(ag.chainId),
    factory: await factory.getAddress(),
    router: await router.getAddress(),
    weth,
    tokens: token ? [{ address: token, symbol: process.env.TOKEN_SEMBOL }] : [],
  };
  fs.writeFileSync(path.join(__dirname, "../frontend/config.js"),
    `// deploy.js tarafından otomatik yazıldı\nwindow.DEX_CONFIG = ${JSON.stringify(cikti, null, 2)};\n`);
  fs.writeFileSync(path.join(__dirname, "../kurulum-sonucu.json"),
    JSON.stringify({ ag: hre.network.name, ...cikti, kurucu: kurucu.address, sahip, tarih: new Date().toISOString() }, null, 2) + "\n");
  console.log("\nAdresler frontend/config.js ve kurulum-sonucu.json dosyalarına yazıldı.");
}

main().catch((e) => { console.error(e); process.exitCode = 1; });
