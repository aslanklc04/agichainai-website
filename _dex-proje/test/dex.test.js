const assert = require("assert");
const { ethers } = require("hardhat");

describe("DEX", function () {
  let sahip, alici, weth, factory, router, token;
  const e = (n) => ethers.parseEther(String(n));
  const sonra = async () => (await ethers.provider.getBlock("latest")).timestamp + 600;

  before(async () => {
    [sahip, alici] = await ethers.getSigners();
    weth = await ethers.deployContract("WETH9");
    factory = await ethers.deployContract("UniswapV2Factory", [sahip.address]);
    router = await ethers.deployContract("UniswapV2Router02", [await factory.getAddress(), await weth.getAddress()]);
    token = await ethers.deployContract("GuvenliToken", ["Test Token", "TST", 1_000_000n]);
  });

  it("token sabit arzla kuruldu ve mint fonksiyonu yok", async () => {
    assert.equal(await token.totalSupply(), e(1_000_000));
    assert.equal(typeof token.mint, "undefined");
  });

  it("ETH-token havuzuna likidite eklenir ve havuz adresi doğru hesaplanır", async () => {
    await token.approve(await router.getAddress(), e(100_000));
    await router.addLiquidityETH(await token.getAddress(), e(100_000), 0, 0, sahip.address, await sonra(), { value: e(10) });
    const pair = await factory.getPair(await token.getAddress(), await weth.getAddress());
    assert.notEqual(pair, ethers.ZeroAddress);
    // Router'ın hesapladığı adres ile Factory'nin kurduğu adres aynı olmalı (init hash kontrolü)
    const tutar = await router.getAmountsOut(e(1), [await weth.getAddress(), await token.getAddress()]);
    assert.ok(tutar[1] > 0n);
  });

  it("başka bir kullanıcı ETH ile token alabilir", async () => {
    const yol = [await weth.getAddress(), await token.getAddress()];
    const once = await token.balanceOf(alici.address);
    await router.connect(alici).swapExactETHForTokens(0, yol, alici.address, await sonra(), { value: e(1) });
    const fark = (await token.balanceOf(alici.address)) - once;
    // 10 ETH / 100.000 token havuzunda 1 ETH, %0,3 ücret sonrası yaklaşık 9.066 token eder
    assert.ok(fark > e(9000) && fark < e(9100), `beklenmeyen miktar: ${ethers.formatEther(fark)}`);
  });

  it("kullanıcı token'ı tekrar ETH'ye satabilir", async () => {
    const yol = [await token.getAddress(), await weth.getAddress()];
    const miktar = await token.balanceOf(alici.address);
    await token.connect(alici).approve(await router.getAddress(), miktar);
    const once = await ethers.provider.getBalance(alici.address);
    await router.connect(alici).swapExactTokensForETH(miktar, 0, yol, alici.address, await sonra());
    assert.ok((await ethers.provider.getBalance(alici.address)) > once);
  });

  it("likidite sağlayıcı payını geri çekebilir", async () => {
    const pair = await ethers.getContractAt("UniswapV2Pair", await factory.getPair(await token.getAddress(), await weth.getAddress()));
    const lp = await pair.balanceOf(sahip.address);
    await pair.approve(await router.getAddress(), lp);
    await router.removeLiquidityETH(await token.getAddress(), lp, 0, 0, sahip.address, await sonra());
    assert.equal(await pair.balanceOf(sahip.address), 0n);
  });
});
