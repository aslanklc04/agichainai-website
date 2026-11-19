/*
 * AGIChainAI Merkle kütüphanesi — Meydan sunucusu ve doğrulama sayfası aynı kodu kullanır.
 * OpenZeppelin StandardMerkleTree ile uyumlu düzen:
 *   yaprak  = keccak256(keccak256(abi.encode(tipler, değerler)))   (çift hash: ikinci-ön-görüntü saldırısına karşı)
 *   düğüm   = keccak256(küçük || büyük)                             (sıralı çift: kanıtta sol/sağ bilgisi gerekmez)
 * Tarayıcıda window.KayitMerkle, Node'da require() ile kullanılır. ethers v6 gerekir.
 */
(function (kok, fabrika) {
  if (typeof module === "object" && module.exports) module.exports = fabrika(require("ethers"));
  else kok.KayitMerkle = fabrika(kok.ethers);
})(typeof self !== "undefined" ? self : this, function (ethers) {
  "use strict";
  const kodlayici = ethers.AbiCoder.defaultAbiCoder();

  // Kayıt türleri: alan sırası ve tipleri SABİTTİR; değiştirmek için yeni sürüm (v2) eklenir.
  const TURLER = {
    "meydan:tahmin:v1": [
      ["tahminId", "string"], ["etkinlikId", "string"], ["secenekId", "string"],
      ["kullaniciOzeti", "bytes32"], ["zaman", "uint64"],
    ],
    "meydan:sonuc:v1": [
      ["etkinlikId", "string"], ["sonucSecenekId", "string"], ["zaman", "uint64"],
    ],
    "consensus:v1": [
      ["soruOzeti", "bytes32"], ["cevapOzeti", "bytes32"], ["zaman", "uint64"],
    ],
  };

  function yaprakHash(kayit) {
    const sema = TURLER[kayit && kayit.tur];
    if (!sema) throw new Error("Bilinmeyen kayıt türü: " + (kayit && kayit.tur));
    const tipler = ["string"].concat(sema.map((a) => a[1]));
    const degerler = [kayit.tur].concat(sema.map(([ad, tip]) => {
      const v = kayit[ad];
      if (v === undefined || v === null) throw new Error("Eksik alan: " + ad);
      if (tip === "uint64") { const n = BigInt(v); if (n < 0n || n >= 2n ** 64n) throw new Error("Geçersiz sayı: " + ad); return n; }
      if (tip === "bytes32" && !/^0x[0-9a-fA-F]{64}$/.test(v)) throw new Error("Geçersiz bytes32: " + ad);
      return v;
    }));
    return ethers.keccak256(ethers.keccak256(kodlayici.encode(tipler, degerler)));
  }

  function ciftHash(a, b) {
    const [x, y] = BigInt(a) < BigInt(b) ? [a, b] : [b, a];
    return ethers.keccak256(ethers.concat([x, y]));
  }

  /** Yaprak hash'lerinden ağaç kurar (OpenZeppelin StandardMerkleTree ile birebir aynı algoritma:
   *  yapraklar artan sırada dizilir, ağaç dizi olarak tutulur, i. yaprak dizinin sonundan i. konumdadır). */
  function agacKur(yapraklar) {
    if (!yapraklar.length) throw new Error("Boş ağaç kurulamaz");
    const sirali = yapraklar.map((h) => h.toLowerCase()).sort((a, b) => (BigInt(a) < BigInt(b) ? -1 : BigInt(a) > BigInt(b) ? 1 : 0));
    for (let i = 1; i < sirali.length; i++) if (sirali[i] === sirali[i - 1]) throw new Error("Aynı kayıt iki kez eklenmiş");
    const n = sirali.length, agac = new Array(2 * n - 1);
    sirali.forEach((h, i) => { agac[agac.length - 1 - i] = h; });
    for (let i = agac.length - 1 - n; i >= 0; i--) agac[i] = ciftHash(agac[2 * i + 1], agac[2 * i + 2]);
    return {
      kok: agac[0],
      kanit(yaprak) {
        const sira = sirali.indexOf(yaprak.toLowerCase());
        if (sira < 0) throw new Error("Yaprak ağaçta yok");
        let i = agac.length - 1 - sira; const k = [];
        while (i > 0) { k.push(agac[i % 2 === 1 ? i + 1 : i - 1]); i = Math.floor((i - 1) / 2); }
        return k;
      },
    };
  }

  function kokHesapla(yaprak, kanit) {
    return kanit.reduce((h, es) => ciftHash(h, es), yaprak);
  }

  /** Kullanıcı kimliğini gizli tuzla özetler: zincirde/kanıtta kimlik görünmez, geri çevrilemez. */
  function kullaniciOzeti(gizliTuz, kullaniciId) {
    if (!gizliTuz || gizliTuz.length < 16) throw new Error("Gizli tuz en az 16 karakter olmalı");
    return ethers.keccak256(kodlayici.encode(["string", "string", "string"], ["meydan:kullanici:v1", gizliTuz, String(kullaniciId)]));
  }

  return { TURLER, yaprakHash, agacKur, kokHesapla, kullaniciOzeti, ciftHash };
});
