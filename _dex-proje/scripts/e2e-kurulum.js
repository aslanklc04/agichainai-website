const fs = require("fs");
const { ethers } = require("hardhat");
(async () => {
  const C = {}; eval(fs.readFileSync("frontend/config.js", "utf8").replace("window.DEX_CONFIG", "C.x"));
  const [s, , saldirgan] = await ethers.getSigners();
  const tkb = await ethers.deployContract("BasitToken", ["TKB"]);
  const xss = await ethers.deployContract("BasitToken", ['<img src=x onerror="window.__xss=1">']);
  await tkb.bas(s.address, ethers.parseEther("1000000"));
  await xss.bas(s.address, ethers.parseEther("1000000"));
  const router = await ethers.getContractAt("UniswapV2Router02", C.x.router);
  const data = router.interface.encodeFunctionData("swapExactETHForTokens", [0, [C.x.weth, C.x.tokens[0].address], saldirgan.address, 9999999999]);
  fs.writeFileSync(require("path").join(__dirname, "../test-arayuz/kurulum.json"), JSON.stringify({
    tkb: await tkb.getAddress(), xss: await xss.getAddress(), alc: C.x.tokens[0].address,
    saldiri: { from: saldirgan.address, to: C.x.router, data, value: "0x" + ethers.parseEther("3").toString(16) },
  }, null, 2));
  console.log("ok");
})();
