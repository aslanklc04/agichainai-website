// Kapsamlı testler: Factory, Pair, Router, token, güvenlik ve rastgele (fuzz) senaryolar.
const assert = require("assert");
const { ethers } = require("hardhat");

const e = (n) => ethers.parseEther(String(n));
const MAX = ethers.MaxUint256;

async function hataBekle(promise, metin) {
  try { await promise; } catch (err) {
    const m = err.shortMessage || err.message || "";
    if (metin && !m.includes(metin)) throw new Error(`Beklenen hata "${metin}", gelen: ${m}`);
    return;
  }
  throw new Error(`Hata bekleniyordu: ${metin}`);
}

async function kurulum() {
  const [sahip, a, b, c] = await ethers.getSigners();
  const weth = await ethers.deployContract("WETH9");
  const factory = await ethers.deployContract("UniswapV2Factory", [sahip.address]);
  const router = await ethers.deployContract("UniswapV2Router02", [await factory.getAddress(), await weth.getAddress()]);
  const tA = await ethers.deployContract("BasitToken", ["TA"]);
  const tB = await ethers.deployContract("BasitToken", ["TB"]);
  const tC = await ethers.deployContract("BasitToken", ["TC"]);
  for (const t of [tA, tB, tC]) for (const s of [sahip, a, b, c]) {
    await t.bas(s.address, e(10_000_000));
    await t.connect(s).approve(await router.getAddress(), MAX);
  }
  const son = async () => (await ethers.provider.getBlock("latest")).timestamp + 3600;
  const pairAl = async (x, y) => ethers.getContractAt("UniswapV2Pair", await factory.getPair(await x.getAddress(), await y.getAddress()));
  return { sahip, a, b, c, weth, factory, router, tA, tB, tC, son, pairAl, R: await router.getAddress() };
}

// ---------------------------------------------------------------------------
describe("Factory", () => {
  let k;
  beforeEach(async () => { k = await kurulum(); });

  it("havuz oluşturur, iki yönde de aynı adresi döndürür", async () => {
    const A = await k.tA.getAddress(), B = await k.tB.getAddress();
    await k.factory.createPair(A, B);
    assert.equal(await k.factory.getPair(A, B), await k.factory.getPair(B, A));
    assert.equal(await k.factory.allPairsLength(), 1n);
  });

  it("aynı token, sıfır adres ve tekrar oluşturma reddedilir", async () => {
    const A = await k.tA.getAddress(), B = await k.tB.getAddress();
    await hataBekle(k.factory.createPair(A, A), "IDENTICAL_ADDRESSES");
    await hataBekle(k.factory.createPair(A, ethers.ZeroAddress), "ZERO_ADDRESS");
    await k.factory.createPair(A, B);
    await hataBekle(k.factory.createPair(B, A), "PAIR_EXISTS");
  });

  it("ücret ayarlarını sadece yetkili değiştirebilir", async () => {
    await hataBekle(k.factory.connect(k.a).setFeeTo(k.a.address), "FORBIDDEN");
    await hataBekle(k.factory.connect(k.a).setFeeToSetter(k.a.address), "FORBIDDEN");
    await k.factory.setFeeTo(k.b.address);
    assert.equal(await k.factory.feeTo(), k.b.address);
  });

  it("yetki sıfır adrese bırakılınca kimse ücret ayarını değiştiremez", async () => {
    await k.factory.setFeeToSetter(ethers.ZeroAddress);
    await hataBekle(k.factory.setFeeTo(k.sahip.address), "FORBIDDEN");
    await hataBekle(k.factory.setFeeToSetter(k.sahip.address), "FORBIDDEN");
  });
});

// ---------------------------------------------------------------------------
describe("Pair (havuz)", () => {
  let k, pair;
  beforeEach(async () => {
    k = await kurulum();
    await k.router.addLiquidity(await k.tA.getAddress(), await k.tB.getAddress(), e(1000), e(4000), 0, 0, k.sahip.address, await k.son());
    pair = await k.pairAl(k.tA, k.tB);
  });

  it("ilk likiditede 1000 birim (MINIMUM_LIQUIDITY) kalıcı olarak kilitlenir", async () => {
    assert.equal(await pair.balanceOf("0x0000000000000000000000000000000000000000"), 1000n);
    const beklenen = BigInt(Math.floor(Math.sqrt(1000 * 4000))) * 10n ** 18n - 1000n;
    assert.equal(await pair.balanceOf(k.sahip.address), beklenen);
  });

  it("rezervler gerçek bakiyelerle eşleşir", async () => {
    const [r0, r1] = await pair.getReserves();
    const t0 = await ethers.getContractAt("BasitToken", await pair.token0());
    const t1 = await ethers.getContractAt("BasitToken", await pair.token1());
    assert.equal(r0, await t0.balanceOf(await pair.getAddress()));
    assert.equal(r1, await t1.balanceOf(await pair.getAddress()));
  });

  it("ücretsiz doğrudan swap (K değişmezini bozan) reddedilir", async () => {
    const P = await pair.getAddress();
    const t0 = await ethers.getContractAt("BasitToken", await pair.token0());
    await t0.transfer(P, e(1));
    const [, r1] = await pair.getReserves();
    // 1 token karşılığı ücretsiz fiyattan çıktı istemek: K hatası
    const ucretsiz = (e(1) * r1) / ((await pair.getReserves())[0] + e(1));
    await hataBekle(pair.swap(0, ucretsiz, k.sahip.address, "0x"), "UniswapV2: K");
  });

  it("havuzdaki tüm rezervi çekmek mümkün değil", async () => {
    const [r0] = await pair.getReserves();
    await hataBekle(pair.swap(r0, 0, k.sahip.address, "0x"), "INSUFFICIENT_LIQUIDITY");
  });

  it("flash swap: ücretle geri ödenirse başarılı, ücretsizse reddedilir", async () => {
    const fb = await ethers.deployContract("FlashBorrower");
    const t0 = await ethers.getContractAt("BasitToken", await pair.token0());
    await t0.bas(await fb.getAddress(), e(10));
    await fb.borrow(await pair.getAddress(), e(100), 0);
    await hataBekle(fb.borrow(await pair.getAddress(), e(100), 1), "UniswapV2: K");
  });

  it("yeniden giriş (reentrancy) kilidi çalışır", async () => {
    const fb = await ethers.deployContract("FlashBorrower");
    await hataBekle(fb.borrow(await pair.getAddress(), e(1), 2), "LOCKED");
  });

  it("skim fazla token'ı dışarı çıkarır, sync rezervleri günceller", async () => {
    const P = await pair.getAddress();
    const t0 = await ethers.getContractAt("BasitToken", await pair.token0());
    await t0.transfer(P, e(5));
    const once = await t0.balanceOf(k.c.address);
    await pair.skim(k.c.address);
    assert.equal((await t0.balanceOf(k.c.address)) - once, e(5));
    await t0.transfer(P, e(5));
    await pair.sync();
    const [r0] = await pair.getReserves();
    assert.equal(r0, await t0.balanceOf(P));
  });

  it("fiyat oracle'ı (birikimli fiyat) zamanla artar", async () => {
    const p0 = await pair.price0CumulativeLast();
    await ethers.provider.send("evm_increaseTime", [3600]);
    await pair.sync();
    assert.ok((await pair.price0CumulativeLast()) > p0);
  });

  it("uint112 sınırını aşan rezerv reddedilir", async () => {
    const P = await pair.getAddress();
    const t0 = await ethers.getContractAt("BasitToken", await pair.token0());
    await t0.bas(P, 2n ** 112n);
    await hataBekle(pair.sync(), "OVERFLOW");
  });

  it("protokol ücreti açıksa, işlemlerden sonra feeTo adresi LP payı kazanır (≈ büyümenin 1/6'sı)", async () => {
    await k.factory.setFeeTo(k.c.address);
    // feeTo açıldıktan sonra kLast kaydı için küçük bir likidite işlemi
    await k.router.addLiquidity(await k.tA.getAddress(), await k.tB.getAddress(), e(1), e(4), 0, 0, k.sahip.address, await k.son());
    for (let i = 0; i < 20; i++) {
      await k.router.connect(k.a).swapExactTokensForTokens(e(50), 0, [await k.tA.getAddress(), await k.tB.getAddress()], k.a.address, await k.son());
      await k.router.connect(k.a).swapExactTokensForTokens(e(200), 0, [await k.tB.getAddress(), await k.tA.getAddress()], k.a.address, await k.son());
    }
    assert.equal(await pair.balanceOf(k.c.address), 0n);
    await k.router.addLiquidity(await k.tA.getAddress(), await k.tB.getAddress(), e(1), e(4), 0, 0, k.sahip.address, await k.son());
    const pay = await pair.balanceOf(k.c.address);
    assert.ok(pay > 0n, "feeTo pay almadı");
    // Toplam ücretin 1/6'sı civarında olmalı: kabaca sağlama
    const toplam = await pair.totalSupply();
    assert.ok(pay * 1000n < toplam * 5n, "protokol payı beklenenden büyük");
  });

  it("LP token, imzayla onay (EIP-2612 permit) destekler", async () => {
    const P = await pair.getAddress();
    const lp = await pair.balanceOf(k.sahip.address);
    const deadline = await k.son();
    const nonce = await pair.nonces(k.sahip.address);
    const chainId = (await ethers.provider.getNetwork()).chainId;
    const sig = await k.sahip.signTypedData(
      { name: "Uniswap V2", version: "1", chainId, verifyingContract: P },
      { Permit: [{ name: "owner", type: "address" }, { name: "spender", type: "address" }, { name: "value", type: "uint256" }, { name: "nonce", type: "uint256" }, { name: "deadline", type: "uint256" }] },
      { owner: k.sahip.address, spender: k.R, value: lp, nonce, deadline });
    const { v, r, s } = ethers.Signature.from(sig);
    await k.router.removeLiquidityWithPermit(await k.tA.getAddress(), await k.tB.getAddress(), lp, 0, 0, k.sahip.address, deadline, false, v, r, s);
    assert.equal(await pair.balanceOf(k.sahip.address), 0n);
  });
});

// ---------------------------------------------------------------------------
describe("Router", () => {
  let k, A, B, C, W;
  beforeEach(async () => {
    k = await kurulum();
    [A, B, C, W] = await Promise.all([k.tA, k.tB, k.tC, k.weth].map((x) => x.getAddress()));
    await k.router.addLiquidity(A, B, e(10_000), e(20_000), 0, 0, k.sahip.address, await k.son());
    await k.router.addLiquidity(B, C, e(10_000), e(5_000), 0, 0, k.sahip.address, await k.son());
    await k.router.addLiquidityETH(A, e(10_000), 0, 0, k.sahip.address, await k.son(), { value: e(100) });
  });

  it("çıktı hesabı Uniswap formülüyle birebir aynı", async () => {
    const giris = e(100), rIn = e(10_000), rOut = e(20_000);
    const beklenen = (giris * 997n * rOut) / (rIn * 1000n + giris * 997n);
    const [, out] = await k.router.getAmountsOut(giris, [A, B]);
    assert.equal(out, beklenen);
    assert.equal(await k.router.getAmountOut(giris, rIn, rOut), beklenen);
  });

  it("süresi geçmiş işlem reddedilir (deadline)", async () => {
    const gecmis = (await ethers.provider.getBlock("latest")).timestamp - 1;
    await hataBekle(k.router.connect(k.a).swapExactTokensForTokens(e(1), 0, [A, B], k.a.address, gecmis), "EXPIRED");
  });

  it("kayma koruması: en az çıktı karşılanmazsa işlem reddedilir", async () => {
    const [, out] = await k.router.getAmountsOut(e(100), [A, B]);
    await hataBekle(k.router.connect(k.a).swapExactTokensForTokens(e(100), out + 1n, [A, B], k.a.address, await k.son()), "INSUFFICIENT_OUTPUT_AMOUNT");
  });

  it("araya başkası girerse (sandviç) kayma koruması kullanıcıyı korur", async () => {
    const [, out] = await k.router.getAmountsOut(e(100), [A, B]);
    const min = (out * 99n) / 100n; // %1 tolerans
    // Saldırgan önce büyük alım yapar
    await k.router.connect(k.c).swapExactTokensForTokens(e(500), 0, [A, B], k.c.address, await k.son());
    await hataBekle(k.router.connect(k.a).swapExactTokensForTokens(e(100), min, [A, B], k.a.address, await k.son()), "INSUFFICIENT_OUTPUT_AMOUNT");
  });

  it("çok adımlı takas (A → B → C) çalışır", async () => {
    const amounts = await k.router.getAmountsOut(e(100), [A, B, C]);
    const once = await k.tC.balanceOf(k.a.address);
    await k.router.connect(k.a).swapExactTokensForTokens(e(100), amounts[2], [A, B, C], k.a.address, await k.son());
    assert.equal((await k.tC.balanceOf(k.a.address)) - once, amounts[2]);
  });

  it("tam çıktı için takas (swapTokensForExactTokens) gerekeni kadar harcar", async () => {
    const [gerekli] = await k.router.getAmountsIn(e(50), [A, B]);
    const once = await k.tA.balanceOf(k.a.address);
    await k.router.connect(k.a).swapTokensForExactTokens(e(50), gerekli, [A, B], k.a.address, await k.son());
    assert.equal(once - (await k.tA.balanceOf(k.a.address)), gerekli);
  });

  it("swapETHForExactTokens fazla gönderilen ETH'yi geri verir", async () => {
    const [gerekli] = await k.router.getAmountsIn(e(100), [W, A]);
    const once = await ethers.provider.getBalance(k.a.address);
    const tx = await k.router.connect(k.a).swapETHForExactTokens(e(100), [W, A], k.a.address, await k.son(), { value: gerekli + e(5) });
    const r = await tx.wait();
    const harcanan = once - (await ethers.provider.getBalance(k.a.address)) - r.gasUsed * r.gasPrice;
    assert.equal(harcanan, gerekli);
  });

  it("ikinci likidite sağlayıcıdan sadece doğru oranda token alınır", async () => {
    const onceA = await k.tA.balanceOf(k.a.address), onceB = await k.tB.balanceOf(k.a.address);
    await k.router.connect(k.a).addLiquidity(A, B, e(100), e(500), 0, 0, k.a.address, await k.son());
    assert.equal(onceA - (await k.tA.balanceOf(k.a.address)), e(100));
    assert.equal(onceB - (await k.tB.balanceOf(k.a.address)), e(200)); // oran 1:2, fazlası alınmadı
  });

  it("likidite eklerken minimum miktar korunur", async () => {
    await hataBekle(k.router.connect(k.a).addLiquidity(A, B, e(100), e(500), 0, e(300), k.a.address, await k.son()), "INSUFFICIENT_B_AMOUNT");
  });

  it("token-token likidite çekme payı doğru verir", async () => {
    await k.router.connect(k.b).addLiquidity(A, B, e(100), e(200), 0, 0, k.b.address, await k.son());
    const pair = await k.pairAl(k.tA, k.tB);
    const lp = await pair.balanceOf(k.b.address);
    await pair.connect(k.b).approve(k.R, lp);
    const onceA = await k.tA.balanceOf(k.b.address);
    await k.router.connect(k.b).removeLiquidity(A, B, lp, 0, 0, k.b.address, await k.son());
    const geri = (await k.tA.balanceOf(k.b.address)) - onceA;
    assert.ok(geri > e(99.99) && geri <= e(100), `geri alınan: ${ethers.formatEther(geri)}`);
  });

  it("Router'a doğrudan ETH gönderilemez (sadece WETH'ten kabul eder)", async () => {
    await hataBekle(k.a.sendTransaction({ to: k.R, value: e(1) }));
  });

  it("geçersiz yol (tek adres veya olmayan havuz) reddedilir", async () => {
    await hataBekle(k.router.getAmountsOut(e(1), [A]), "INVALID_PATH");
    await hataBekle(k.router.getAmountsOut(e(1), [A, C]));
  });

  it("transferde kesinti yapan token: normal fonksiyon başarısız, 'Supporting' fonksiyonu çalışır", async () => {
    const kes = await ethers.deployContract("KesintiliToken");
    const K = await kes.getAddress();
    await kes.approve(k.R, MAX);
    await k.router.addLiquidityETH(K, e(10_000), 0, 0, k.sahip.address, await k.son(), { value: e(10) });
    await hataBekle(k.router.swapExactTokensForETH(e(100), 1, [K, W], k.sahip.address, await k.son()));
    const once = await ethers.provider.getBalance(k.c.address);
    await k.router.swapExactTokensForETHSupportingFeeOnTransferTokens(e(100), 0, [K, W], k.c.address, await k.son());
    assert.ok((await ethers.provider.getBalance(k.c.address)) > once);
  });
});

// ---------------------------------------------------------------------------
describe("GuvenliToken ve WETH", () => {
  it("token: sabit arz, 18 ondalık, sahip/mint/dondurma fonksiyonu yok", async () => {
    const [s, a] = await ethers.getSigners();
    const t = await ethers.deployContract("GuvenliToken", ["Alacam Token", "ALC", 1_000_000_000n]);
    assert.equal(await t.decimals(), 18n);
    assert.equal(await t.totalSupply(), e(1_000_000_000));
    const fonksiyonlar = t.interface.fragments.filter((f) => f.type === "function").map((f) => f.name);
    for (const yasak of ["mint", "burn", "owner", "pause", "blacklist", "setFee", "transferOwnership"])
      assert.ok(!fonksiyonlar.includes(yasak), `beklenmeyen fonksiyon: ${yasak}`);
    await t.transfer(a.address, e(5));
    await hataBekle(t.connect(a).transfer(s.address, e(6)));
    await hataBekle(t.connect(a).transferFrom(s.address, a.address, 1n));
    assert.equal(await t.totalSupply(), e(1_000_000_000));
  });

  it("WETH: yatır/çek birebir çalışır", async () => {
    const [s] = await ethers.getSigners();
    const w = await ethers.deployContract("WETH9");
    await w.deposit({ value: e(3) });
    assert.equal(await w.balanceOf(s.address), e(3));
    await w.withdraw(e(3));
    assert.equal(await w.balanceOf(s.address), 0n);
    await hataBekle(w.withdraw(1n));
  });
});

// ---------------------------------------------------------------------------
describe("Rastgele senaryo (fuzz) — değişmezler", function () {
  this.timeout(300000);

  it("400 rastgele işlem boyunca K azalmaz, rezerv = bakiye, toplam token korunur", async () => {
    const k = await kurulum();
    const A = await k.tA.getAddress(), B = await k.tB.getAddress();
    const kullanicilar = [k.a, k.b, k.c];
    await k.router.addLiquidity(A, B, e(50_000), e(50_000), 0, 0, k.sahip.address, await k.son());
    const pair = await k.pairAl(k.tA, k.tB);
    const P = await pair.getAddress();
    for (const u of kullanicilar) await pair.connect(u).approve(k.R, MAX);

    const toplamA0 = await k.tA.totalSupply(), toplamB0 = await k.tB.totalSupply();
    let tohum = 12345;
    const rnd = () => { tohum = (tohum * 1103515245 + 12345) % 2 ** 31; return tohum / 2 ** 31; };
    let oncekiK = 0n, sayac = { swap: 0, ekle: 0, cek: 0 };

    for (let i = 0; i < 400; i++) {
      const u = kullanicilar[Math.floor(rnd() * 3)];
      const islem = rnd();
      const miktar = e(Math.floor(rnd() * 5000) + 1);
      if (islem < 0.6) {
        const yol = rnd() < 0.5 ? [A, B] : [B, A];
        await k.router.connect(u).swapExactTokensForTokens(miktar, 0, yol, u.address, await k.son());
        sayac.swap++;
      } else if (islem < 0.85) {
        await k.router.connect(u).addLiquidity(A, B, miktar, miktar * 3n, 0, 0, u.address, await k.son());
        sayac.ekle++;
      } else {
        const lp = await pair.balanceOf(u.address);
        if (lp > 0n) { await k.router.connect(u).removeLiquidity(A, B, lp / 2n, 0, 0, u.address, await k.son()); sayac.cek++; }
      }
      const [r0, r1] = await pair.getReserves();
      const t0 = await pair.token0();
      const [bA, bB] = [await k.tA.balanceOf(P), await k.tB.balanceOf(P)];
      const [b0, b1] = t0 === A ? [bA, bB] : [bB, bA];
      assert.equal(r0, b0, `adım ${i}: rezerv0 ≠ bakiye`);
      assert.equal(r1, b1, `adım ${i}: rezerv1 ≠ bakiye`);
      // K, LP başına ölçülür (likidite ekleme/çekme K'yı meşru olarak değiştirir)
      const kPerLp = (r0 * r1 * 10n ** 18n) / ((await pair.totalSupply()) ** 2n);
      assert.ok(kPerLp >= oncekiK, `adım ${i}: LP başına K azaldı`);
      oncekiK = kPerLp;
    }
    assert.equal(await k.tA.totalSupply(), toplamA0, "A arzı değişti");
    assert.equal(await k.tB.totalSupply(), toplamB0, "B arzı değişti");
    console.log("      işlemler:", JSON.stringify(sayac));
  });
});
