# DEX: Uniswap V2 tabanlı merkeziyetsiz borsa

Bu proje, gerçek bir EVM ağına (Ethereum, BNB Chain, Base, Arbitrum…) kurulabilen eksiksiz bir merkeziyetsiz borsadır:

- **Kontratlar:** Uniswap V2'nin orijinal, denetlenmiş kodu (Factory, Pair, Router02, WETH9). Kod değiştirilmedi; sadece Router'daki "init code hash" sizin derlemenize göre güncellendi.
- **Token:** Sabit arzlı, sahipsiz, mint/dondurma/vergi özelliği olmayan `GuvenliToken` (OpenZeppelin).
- **Web arayüzü:** `frontend/` klasöründe tek sayfalık arayüz. Takas, likidite ekleme ve likidite çekme yapılabilir, adres girilerek token eklenebilir.
- **Testler:** Likidite ekleme, alım, satım ve likidite çekme otomatik test ediliyor.

## Klasör yapısı

```
contracts/core/        Uniswap V2 Factory + Pair  (Solidity 0.5.16)
contracts/periphery/   Router02 + WETH9           (Solidity 0.6.6)
contracts/token/       GuvenliToken               (Solidity 0.8.24)
scripts/deploy.js      Kurulum betiği
scripts/init-hash.js   Pair hash'ini Router'a yazar
test/dex.test.js       Otomatik testler
frontend/              Web arayüzü (index.html + config.js)
```

## En kolay yol: GitHub Actions ile kurulum (bilgisayar gerekmez)

1. Bu projeyi GitHub'da herkese açık (public) bir depoya koyun.
2. **Settings → Secrets and variables → Actions → New repository secret** yolundan `DEPLOYER_KEY` adlı bir secret ekleyin. Değeri, sadece kurulum için açılmış ve içinde Sepolia ETH'si olan bir cüzdanın özel anahtarı.
3. **Settings → Pages → Source:** "GitHub Actions" seçin.
4. **Actions → "Sepolia'ya kur" → Run workflow** yolundan kendi MetaMask adresinizi girin ve çalıştırın.
5. İş akışı sırayla şunları yapar: derler, testleri çalıştırır, Sepolia'ya kurar, token'ları, yetkiyi ve kalan ETH'yi sizin adresinize devreder, adresleri depoya kaydeder ve web sitesini yayınlar.

## Bilgisayarsız, telefondan çalıştırma (GitHub Codespaces)

1. **Cüzdan:** Telefona MetaMask uygulamasını kurun ve **yeni bir hesap** açın. Ağ olarak Sepolia'yı açın (Ayarlar → Gelişmiş → Test ağlarını göster). Bu hesabın özel anahtarını kopyalayın (Hesap ayrıntıları → Özel anahtarı göster).
2. **Test ETH'si:** Google Cloud Web3 Sepolia faucet'ine Google hesabınızla girip adresinizi yapıştırın. Yaklaşık 0,05 ETH genelde yeterli.
3. **GitHub:** github.com'da hesap açın ve yeni bir depo (repository) oluşturun. Bu proje dosyalarını depoya yükleyin.
4. **Codespace:** Depo sayfasında **Code → Codespaces → Create codespace** seçin. Telefonda tarayıcının "masaüstü sitesi" modunu açın. Açılış sırasında kurulum, derleme ve testler otomatik çalışır (birkaç dakika).
5. **Kurulum:** Alttaki terminale `bash kur-sepolia.sh` yazın. RPC için Enter'a basın, özel anahtarı yapıştırın.
6. **Web sitesi:** Terminalde betiğin gösterdiği üç `git` komutunu çalıştırın. Bir kez: deponun **Settings → Pages → Source** ayarını "GitHub Actions" yapın. Birkaç dakika içinde siteniz `https://KULLANICIADI.github.io/DEPOADI/` adresinde yayına girer.
7. **Kullanım:** MetaMask uygulamasının içindeki tarayıcıdan bu adresi açın ve "Cüzdan bağla"ya basın.
8. Codespace'i işiniz bitince durdurun. Ücretsiz plan aylık sınırlı saat içerir.

## 1. Hazırlık (bir kez)

1. [Node.js](https://nodejs.org) 18 veya üzerini kurun.
2. Proje klasöründe:
   ```
   npm install --legacy-peer-deps
   npm run derle
   npm test
   ```
   5 test "passing" olarak görünmeli.

> Derleyiciler `solc0516`, `solc066`, `solc0824` npm paketlerinden gelir (`solc-local.js`). Bu yüzden internetten ayrıca indirme gerekmez.

## 2. Bilgisayarınızda deneme (ücretsiz, 2 dakika)

Bir terminalde:
```
npm run yerel-ag
```
Bu komut 20 test hesabı ve anahtarlarını listeler. İkinci bir terminalde, listedeki ilk anahtarla:
```
RPC_URL=http://127.0.0.1:8545 PRIVATE_KEY=0x...ilk_anahtar TOKEN_AD="Alacam Token" TOKEN_SEMBOL=ALC TOKEN_ARZ=1000000000 npm run kur
npm run arayuz
```
Tarayıcıda açılan adrese gidin. MetaMask'a "Localhost 8545" ağını (chainId 31337) ekleyin ve aynı test anahtarını içe aktarın.

> Windows'ta ortam değişkenleri farklı yazılır: `set RPC_URL=...` (cmd) veya `$env:RPC_URL="..."` (PowerShell), ardından `npm run kur`.

## 3. Test ağına kurulum (Sepolia, ücretsiz)

1. **Yeni ve sadece bu iş için** bir MetaMask hesabı açın. Ana cüzdanınızın anahtarını kullanmayın.
2. Bir Sepolia faucet sitesinden test ETH'si alın (yaklaşık 0,05 ETH yeterli).
3. Infura, Alchemy veya benzeri bir servisten ücretsiz bir Sepolia RPC adresi alın.
4. Kurun:
   ```
   RPC_URL=https://... PRIVATE_KEY=0x... TOKEN_AD="Alacam Token" TOKEN_SEMBOL=ALC TOKEN_ARZ=1000000000 npm run kur
   ```
   Sepolia'da `WETH_ADDRESS` vermeyin, betik kendi WETH'ini kurar.
5. Adresler `frontend/config.js` dosyasına otomatik yazılır. `npm run arayuz` ile açın, MetaMask'ı Sepolia'ya geçirin.
6. **İlk likiditeyi siz eklersiniz.** "Likidite ekle" sekmesinde örneğin 0,01 ETH + 100.000 ALC girin. Bu oran, token'ın başlangıç fiyatını belirler.

## 4. Gerçek ağa kurulum

Kurulum komutu aynıdır, sadece RPC adresi gerçek ağın adresidir ve `WETH_ADDRESS` mutlaka verilir. Yaygın resmî adresler aşağıda; kurmadan önce ağın kendi belgelerinden doğrulayın:

| Ağ | chainId | WETH_ADDRESS |
|---|---|---|
| Ethereum | 1 | `0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2` |
| Base | 8453 | `0x4200000000000000000000000000000000000006` |
| Arbitrum One | 42161 | `0x82aF49447D8a07e3bd95BD0d56f35241523fBab1` |
| BNB Chain (WBNB) | 56 | `0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c` |

**Maliyet:** Ölçülen gas kullanımı: Factory yaklaşık 3,05 milyon, Router yaklaşık 4,76 milyon, token yaklaşık 0,56 milyon, ilk havuz ve likidite yaklaşık 2,72 milyon. Toplam yaklaşık **11,1 milyon gas**. Ücret = gas × gas fiyatı. Örneğin 1 gwei'de yaklaşık 0,011 ETH, 10 gwei'de yaklaşık 0,11 ETH tutar. Base ve Arbitrum gibi L2 ağlarında genelde çok daha ucuzdur. Kurmadan önce ağın güncel gas fiyatına bakın.

**Web sitesini yayınlamak:** `frontend/` klasörü sabit dosyalardan oluşur. GitHub Pages, Netlify, Cloudflare Pages veya IPFS'e olduğu gibi yüklenebilir. Dosyayı çift tıklayarak (file://) açmayın, çünkü cüzdanlar orada çalışmayabilir.

## Gerçek kullanıma açmadan önce kontrol listesi

- [ ] **Güvenlik:** Uniswap V2 kontratları yıllardır milyarlarca dolarla çalışıyor ve denetlendi. Ama bu projedeki kurulum betiği, arayüz ve token kodu bağımsız olarak denetlenmedi. Gerçek para için bir güvenlik uzmanına inceletin.
- [ ] **Kurucu yetkisi (feeToSetter):** Factory'yi kuran adres, ileride işlem ücretinin altıda birini (%0,05) protokole yönlendirmeyi açabilir. Merkeziyetsizliği tamamlamak için bu yetkiyi `setFeeToSetter(0x000…000)` ile kalıcı olarak bırakabilir ya da çoklu imzalı (multisig) bir cüzdana devredebilirsiniz.
- [ ] **Anahtar güvenliği:** Kurulum anahtarını hiçbir dosyaya kaydetmeyin, kimseyle paylaşmayın. Kurulumdan sonra bu cüzdanda değerli bir şey bırakmayın ya da kurulumu donanım cüzdanıyla yapın.
- [ ] **Likidite:** Kendi token'ınızın likiditesini kilitlemek veya LP token'larını yakmak, alıcılara rug pull yapılmayacağı güvencesini verir.
- [ ] **Yasal durum:** Türkiye'de kripto varlık hizmetleri SPK düzenlemesine tabidir (7518 sayılı Kanun). Türkiye'de yerleşik kişilere yönelik izinsiz faaliyet suçtur. Türkiye'ye kapatmak (Türkçe arayüz yok, Türkiye'ye tanıtım yok, Türkiye IP'lerine erişim engeli) bu riski azaltır. Ama kendiniz Türkiye'de yaşıyorsanız durumun nasıl değerlendirileceği net değil, ve hizmet verdiğiniz ülkelerin kuralları ayrıca geçerlidir (örneğin AB'de MiCA). Yayına almadan önce bir avukata danışın.

## Testler

| Komut | Ne yapar |
|---|---|
| `npm test` | 46 kontrat testi (birim, entegrasyon, 400 adımlık rastgele senaryo) |
| `npm run kapsam` | Kod kapsamı raporu (`coverage/index.html`) |
| `npm run analiz` | Slither statik analizi (`pip install slither-analyzer` gerekir) |
| `npm run test-arayuz` | Tarayıcıda 21 arayüz testi (`pip install playwright && playwright install chromium` gerekir) |

Sonuçlar ve bulunan/düzeltilen hatalar için: `TEST_RAPORU.md`.

## Lisans

Uniswap V2 kontratları GPL-3.0 lisanslıdır. Bu projeyi dağıtırsanız kaynak kodunu da GPL-3.0 altında paylaşmanız gerekir. GuvenliToken MIT lisanslıdır.
