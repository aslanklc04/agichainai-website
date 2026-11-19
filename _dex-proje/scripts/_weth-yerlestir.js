// Yerel test: Base'in resmî WETH adresine (0x4200…0006) WETH9 kodunu yerleştirir
const { ethers, network } = require("hardhat");
(async () => {
  const a = require("../artifacts/contracts/periphery/WETH9.sol/WETH9.json");
  await network.provider.send("hardhat_setCode", ["0x4200000000000000000000000000000000000006", a.deployedBytecode]);
  const w = await ethers.getContractAt("WETH9", "0x4200000000000000000000000000000000000006");
  console.log("WETH yerleşti:", await w.symbol());
})();
