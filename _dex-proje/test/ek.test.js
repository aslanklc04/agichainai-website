// Ek testler: Router'ın kalan fonksiyonları, LP transferi, protokol ücretini kapatma, WETH onayları.
const assert = require("assert");
const { ethers } = require("hardhat");
const e = (n) => ethers.parseEther(String(n));
const MAX = ethers.MaxUint256;

async function hataBekle(p, metin) {
  try { await p; } catch (err) { const m = err.shortMessage || err.message || ""; if (metin && !m.includes(metin)) throw new Error(`Beklenen "${metin}", gelen: ${m}`); return; }
  throw new Error("Hata bekleniyordu: " + metin);
}

async function permitImza(signer, pair, spender, value, deadline) {
  const chainId = (await ethers.provider.getNetwork()).chainId;
  const sig = await signer.signTypedData(
    { name: "Uniswap V2", version: "1", chainId, verifyingContract: await pair.getAddress() },
    { Permit: [{ name: "owner", type: "address" }, { name: "spender", type: "address" }, { name: "value", type: "uint256" }, { name: "nonce", type: "uint256" }, { name: "deadline", type: "uint256" }] },
    { owner: signer.address, spender, value, nonce: await pair.nonces(signer.address), deadline });
  return ethers.Signature.from(sig);
}

describe("Router — kalan fonksiyonlar", () => {
  let s, a, weth, factory, router, R, W, tok, T, kes, K, tB, B, son;
  beforeEach(async () => {
    [s, a] = await ethers.getSigners();
    weth = await ethers.deployContract("WETH9");
    factory = await ethers.deployContract("UniswapV2Factory", [s.address]);
    router = await ethers.deployContract("UniswapV2Router02", [await factory.getAddress(), await weth.getAddress()]);
    [R, W] = [await router.getAddress(), await weth.getAddress()];
    tok = await ethers.deployContract("GuvenliToken", ["T", "T", 1_000_000n]); T = await tok.getAddress();
    kes = await ethers.deployContract("KesintiliToken"); K = await kes.getAddress();
    tB = await ethers.deployContract("BasitToken", ["B"]); B = await tB.getAddress();
    await tB.bas(s.address, e(1_000_000));
    for (const t of [tok, kes, tB]) await t.approve(R, MAX);
    son = async () => (await ethers.provider.getBlock("latest")).timestamp + 3600;
    await router.addLiquidityETH(T, e(100_000), 0, 0, s.address, await son(), { value: e(10) });
    await router.addLiquidityETH(K, e(100_000), 0, 0, s.address, await son(), { value: e(10) });
    await router.addLiquidity(K, B, e(100_000), e(100_000), 0, 0, s.address, await son());
  });

  it("swapTokensForExactETH: tam ETH çıktısı için gereken token harcanır", async () => {
    const [gerekli] = await router.getAmountsIn(e(1), [T, W]);
    const once = await tok.balanceOf(s.address);
    await router.swapTokensForExactETH(e(1), gerekli, [T, W], a.address, await son());
    assert.equal(once - (await tok.balanceOf(s.address)), gerekli);
    await hataBekle(router.swapTokensForExactETH(e(1), 1n, [T, W], a.address, await son()), "EXCESSIVE_INPUT_AMOUNT");
  });

  it("quote ve getAmountIn: doğru hesap ve hatalı girişlerin reddi", async () => {
    assert.equal(await router.quote(e(1), e(10), e(20)), e(2));
    await hataBekle(router.quote(0, e(10), e(20)), "INSUFFICIENT_AMOUNT");
    await hataBekle(router.quote(e(1), 0, e(20)), "INSUFFICIENT_LIQUIDITY");
    const inn = await router.getAmountIn(e(1), e(100), e(100));
    assert.ok((await router.getAmountOut(inn, e(100), e(100))) >= e(1));
    await hataBekle(router.getAmountIn(0, e(100), e(100)), "INSUFFICIENT_OUTPUT_AMOUNT");
    await hataBekle(router.getAmountOut(0, e(100), e(100)), "INSUFFICIENT_INPUT_AMOUNT");
  });

  it("removeLiquidityETHWithPermit: imzayla tek işlemde likidite çekilir", async () => {
    const pair = await ethers.getContractAt("UniswapV2Pair", await factory.getPair(T, W));
    const lp = await pair.balanceOf(s.address), dl = await son();
    const { v, r, s: ss } = await permitImza(s, pair, R, lp, dl);
    await router.removeLiquidityETHWithPermit(T, lp, 0, 0, s.address, dl, false, v, r, ss);
    assert.equal(await pair.balanceOf(s.address), 0n);
  });

  it("geçersiz imza (permit) reddedilir", async () => {
    const pair = await ethers.getContractAt("UniswapV2Pair", await factory.getPair(T, W));
    const lp = await pair.balanceOf(s.address), dl = await son();
    const { v, r, s: ss } = await permitImza(a, pair, R, lp, dl); // yanlış kişi imzaladı
    await hataBekle(router.removeLiquidityETHWithPermit(T, lp, 0, 0, s.address, dl, false, v, r, ss), "INVALID_SIGNATURE");
  });

  it("kesintili token: ETH ile alım, token-token takas ve likidite çekme (Supporting fonksiyonları)", async () => {
    const once = await kes.balanceOf(a.address);
    await router.connect(a).swapExactETHForTokensSupportingFeeOnTransferTokens(0, [W, K], a.address, await son(), { value: e(1) });
    assert.ok((await kes.balanceOf(a.address)) > once);

    const onceB = await tB.balanceOf(a.address);
    await router.swapExactTokensForTokensSupportingFeeOnTransferTokens(e(100), 0, [K, B], a.address, await son());
    assert.ok((await tB.balanceOf(a.address)) > onceB);

    const pair = await ethers.getContractAt("UniswapV2Pair", await factory.getPair(K, W));
    const lp = (await pair.balanceOf(s.address)) / 2n;
    await pair.approve(R, MAX);
    await router.removeLiquidityETHSupportingFeeOnTransferTokens(K, lp, 0, 0, s.address, await son());
    const dl = await son(), kalan = await pair.balanceOf(s.address);
    const { v, r, s: ss } = await permitImza(s, pair, R, kalan, dl);
    await router.removeLiquidityETHWithPermitSupportingFeeOnTransferTokens(K, kalan, 0, 0, s.address, dl, false, v, r, ss);
    assert.equal(await pair.balanceOf(s.address), 0n);
  });

  it("kesintili token için kayma koruması (Supporting) çalışır", async () => {
    await hataBekle(router.swapExactTokensForTokensSupportingFeeOnTransferTokens(e(100), e(100), [K, B], a.address, await son()), "INSUFFICIENT_OUTPUT_AMOUNT");
    await hataBekle(router.connect(a).swapExactETHForTokensSupportingFeeOnTransferTokens(e(1_000_000), [W, K], a.address, await son(), { value: e(1) }), "INSUFFICIENT_OUTPUT_AMOUNT");
  });

  it("ETH yolu yanlış başlarsa reddedilir", async () => {
    await hataBekle(router.swapExactETHForTokens(0, [T, W], a.address, await son(), { value: e(1) }), "INVALID_PATH");
    await hataBekle(router.swapExactTokensForETH(e(1), 0, [W, T], a.address, await son()), "INVALID_PATH");
  });
});

describe("LP token ve protokol ücreti kapatma", () => {
  it("LP token transfer edilebilir; yeni sahibi likiditeyi çekebilir", async () => {
    const [s, a] = await ethers.getSigners();
    const weth = await ethers.deployContract("WETH9");
    const factory = await ethers.deployContract("UniswapV2Factory", [s.address]);
    const router = await ethers.deployContract("UniswapV2Router02", [await factory.getAddress(), await weth.getAddress()]);
    const t = await ethers.deployContract("GuvenliToken", ["T", "T", 1_000_000n]);
    await t.approve(await router.getAddress(), MAX);
    const son = (await ethers.provider.getBlock("latest")).timestamp + 3600;
    await router.addLiquidityETH(await t.getAddress(), e(1000), 0, 0, s.address, son, { value: e(1) });
    const pair = await ethers.getContractAt("UniswapV2Pair", await factory.getPair(await t.getAddress(), await weth.getAddress()));
    const lp = await pair.balanceOf(s.address);
    await pair.transfer(a.address, lp);
    assert.equal(await pair.balanceOf(a.address), lp);
    await pair.connect(a).approve(await router.getAddress(), lp);
    await router.connect(a).removeLiquidityETH(await t.getAddress(), lp, 0, 0, a.address, son);
    assert.equal(await pair.balanceOf(a.address), 0n);
  });

  it("protokol ücreti kapatılınca kLast sıfırlanır", async () => {
    const [s] = await ethers.getSigners();
    const weth = await ethers.deployContract("WETH9");
    const factory = await ethers.deployContract("UniswapV2Factory", [s.address]);
    const router = await ethers.deployContract("UniswapV2Router02", [await factory.getAddress(), await weth.getAddress()]);
    const t = await ethers.deployContract("GuvenliToken", ["T", "T", 1_000_000n]);
    await t.approve(await router.getAddress(), MAX);
    const son = (await ethers.provider.getBlock("latest")).timestamp + 3600;
    await factory.setFeeTo(s.address);
    await router.addLiquidityETH(await t.getAddress(), e(1000), 0, 0, s.address, son, { value: e(1) });
    const pair = await ethers.getContractAt("UniswapV2Pair", await factory.getPair(await t.getAddress(), await weth.getAddress()));
    assert.ok((await pair.kLast()) > 0n);
    await factory.setFeeTo(ethers.ZeroAddress);
    await router.addLiquidityETH(await t.getAddress(), e(10), 0, 0, s.address, son, { value: e(0.01) });
    assert.equal(await pair.kLast(), 0n);
  });

  it("WETH: onay ve toplam arz", async () => {
    const [s, a] = await ethers.getSigners();
    const w = await ethers.deployContract("WETH9");
    await w.deposit({ value: e(2) });
    assert.equal(await w.totalSupply(), e(2));
    await w.approve(a.address, e(1));
    await w.connect(a).transferFrom(s.address, a.address, e(1));
    assert.equal(await w.balanceOf(a.address), e(1));
  });
});
