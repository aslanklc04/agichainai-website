# Test raporu

Tarih: 19 Kasım 2026 · Ortam: Hardhat yerel ağı, Chromium (telefon ekranı 390 px)

## Özet

| Test türü | Sonuç |
|---|---|
| Kontrat testleri (birim + entegrasyon + fuzz) | **46 / 46 başarılı** |
| Mutasyon testi (koda bilerek hata ekleme) | **3 / 3 hata yakalandı** |
| Kod kapsamı | **Satır %99,45 · Fonksiyon %100** · İfade %98,9 · Dal %72,9 |
| Statik analiz (Slither 0.11.6) | GuvenliToken'da **0 bulgu**. Uniswap kodundaki bulgular incelendi, gerçek açık yok (aşağıda) |
| Arayüz testi: temel akış | **Başarılı** (bağlan → likidite ekle → al → sat → likidite çek) |
| Arayüz testi: uç durumlar | **20 / 20 başarılı** |
| Temiz kurulum (sıfırdan `npm install`) | **Başarılı** |

## Testlerde bulunup düzeltilen hatalar

1. **Arayüzde zamanlama hatası:** Kullanıcı hızlı yazınca, eski bir fiyat hesabı yenisinden sonra bitip ekrandaki değeri ve düğme durumunu bozabiliyordu. Düzeltme: her hesaba sıra numarası verildi, sadece en son başlatılan hesap ekrana yazıyor.
2. **Anlaşılmayan hata mesajları:** Cüzdanların iç içe döndürdüğü hatalarda kullanıcı "could not coalesce error" gibi teknik bir mesaj görüyordu. Düzeltme: hata nesnesinin tamamı taranıyor. Kullanıcı artık "Bakiyeniz yetersiz" veya "Fiyat çok değişti, kayma toleransını artırın" gibi anlaşılır mesajlar görüyor.
3. **Mobil görünüm:** Dar ekranda token seçim kutuları kesiliyordu ("AL", "ET"). Düzeltme: seçim kutularına en az genişlik verildi.

## 1. Kontrat testleri (`npm test`)

**Factory:** havuz oluşturma, iki yönde aynı adres, aynı token / sıfır adres / tekrar oluşturmanın reddi, ücret ayarına sadece yetkilinin erişmesi, yetki bırakılınca kimsenin değiştirememesi.

**Pair (havuz):**
- 1000 birimlik minimum likiditenin kalıcı olarak kilitlenmesi
- Rezervlerin bakiyelerle eşleşmesi
- K değişmezini bozan ücretsiz swap'ın reddi
- Tüm rezervi çekme girişiminin reddi
- Flash swap: ücretle geri ödenince başarılı, ücretsiz geri ödenince reddediliyor
- **Yeniden giriş (reentrancy) kilidi**
- skim/sync, fiyat oracle'ı, uint112 taşma koruması
- Protokol ücretinin açılması ve kapatılması
- İmzayla onay (EIP-2612 permit)

**Router:**
- Fiyat hesabı Uniswap formülüyle birebir aynı
- Süre dolumu (deadline) ve kayma koruması
- **Sandviç saldırısında kullanıcının korunması**
- Çok adımlı takas (A → B → C), tam çıktılı takaslar, fazla ETH'nin iadesi
- İkinci likidite sağlayıcıdan sadece doğru oranda token alınması, minimum miktar koruması
- Likidite çekme, imzalı çekme, geçersiz imzanın reddi
- Transferde kesinti yapan token'lar (Supporting fonksiyonları)
- Router'a doğrudan ETH gönderiminin reddi, geçersiz yolların reddi

**GuvenliToken:** sabit arz, 18 ondalık. Şu fonksiyonların hiçbiri yok: `mint`, `burn`, `owner`, `pause`, `blacklist`, `setFee`, `transferOwnership`. Bakiyesiz transfer ve onaysız transferFrom reddediliyor.

**Fuzz (rastgele senaryo):** 3 kullanıcıyla 400 rastgele işlem (244 takas, 106 likidite ekleme, 50 çekme). Her adımda şunlar kontrol edildi:
- Rezervler gerçek bakiyelere eşit kalıyor
- LP başına K hiç azalmıyor, yani havuzdan değer sızmıyor
- Toplam token arzı değişmiyor

## 2. Mutasyon testi

Testlerin gerçekten hata yakalayıp yakalamadığını görmek için koda bilerek hata eklendi:

| Eklenen hata | Sonuç |
|---|---|
| Router'da süre kontrolü silindi | Yakalandı (deadline testi başarısız oldu) |
| Havuzda %0,3 ücret sıfırlandı | Yakalandı (2 test başarısız oldu) |
| Reentrancy kilidi devre dışı bırakıldı | Yakalandı (reentrancy testi başarısız oldu) |

Hatalar geri alındıktan sonra 46 testin tamamı tekrar başarılı oldu.

## 3. Kod kapsamı (`npm run kapsam`)

| Dosya | Satır | Fonksiyon |
|---|---|---|
| UniswapV2Factory | %100 | %100 |
| UniswapV2Pair | %100 | %100 |
| UniswapV2ERC20 (LP token) | %100 | %100 |
| UniswapV2Router02 | %100 | %100 |
| UniswapV2Library | %100 | %100 |
| GuvenliToken | %100 | %100 |

Dal kapsamının %73'te kalmasının nedeni, Uniswap'in SafeMath gibi taşma kontrollerindeki "olmayacak" dallar. Bu dallara normal kullanımla ulaşılamıyor.

## 4. Statik analiz (Slither)

GuvenliToken için hiçbir önem seviyesinde bulgu yok. Uniswap V2 kodunda raporlanan Yüksek ve Orta bulgular tek tek incelendi:

| Bulgu | Değerlendirme |
|---|---|
| weak-prng (Pair) | Yanlış alarm. `block.timestamp % 2**32` rastgele sayı için değil, fiyat oracle'ının zaman damgası için kullanılıyor. |
| reentrancy-balance (Router, Supporting fonksiyonları) | Bilinçli tasarım. Kesintili token'lar için bakiye önce ve sonra ölçülüyor. Kötü niyetli bir token ancak onu kullanan kişiye zarar verebilir. |
| unchecked-transfer (removeLiquidity) | Yanlış alarm. LP token'ın `transferFrom` fonksiyonu ya `true` döndürüyor ya da işlemi geri alıyor. |
| reentrancy-no-eth (Pair) | Fonksiyonlar `lock` ile korunuyor, testlerle doğrulandı. Factory'deki uyarı, kendi oluşturduğu güvenilir kontrat için. |
| incorrect-equality, unused-return | Kasıtlı kod kalıpları, risk değil. |

Bu kod, 2020'den beri Uniswap ve onlarca kopyasında çok büyük miktarlarla çalışıyor.

## 5. Arayüz testleri (`npm run test-arayuz`)

Gerçek bir tarayıcıda, yerel zincire bağlı cüzdan taklidiyle çalıştırıldı:

- Yanlış ağda uyarı verilmesi, doğru ağda bağlanma
- Geçersiz adres ve token olmayan adresin reddi
- **Kötü niyetli token adının (XSS) kod olarak çalışmaması**, uzun adların kısaltılması
- Token-token likidite ekleme (iki onay + ekleme), havuz oranından otomatik miktar hesabı
- Token-token takas
- Havuzu olmayan çift, aynı varlık seçimi, 0 / negatif / harf girişi
- Cüzdanda reddedilen işlem
- Yetersiz bakiye
- **Sandviç saldırısı:** kullanıcının işleminden hemen önce büyük bir alım yapıldı. Kayma koruması işlemi durdurdu ve kullanıcının bakiyesi değişmedi.
- 390 px telefon ekranında yatay taşma olmaması

## Bu testlerin kapsamadıkları

- **Bağımsız güvenlik denetimi:** Bu rapor bir denetim yerine geçmez. Gerçek para için bağımsız bir denetim firması önerilir.
- **Gerçek ağ koşulları:** Gerçek ağdaki MEV botları, gas dalgalanması ve RPC kesintileri yerel ağda tam taklit edilemez. Sepolia test ağında da deneyin.
- **Gerçek cüzdanlar:** Testler cüzdan taklidiyle yapıldı. MetaMask, Rabby ve mobil cüzdanlarla elle deneme önerilir.
- **Kullanıcının seçtiği token'ların güvenliği:** Borsa herkese açık. Arayüz, kullanıcıyı sahte veya kötü niyetli token'lara karşı koruyamaz, sadece uyarır.
