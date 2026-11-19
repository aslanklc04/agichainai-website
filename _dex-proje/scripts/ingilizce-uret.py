"""frontend/ (Türkçe, test ağı) sayfalarından exchange/ (İngilizce, Base ana ağı) sayfalarını üretir.
Kullanım: python3 scripts/ingilizce-uret.py"""
import os, re, shutil, sys
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(KOK, "frontend"); E = os.path.join(KOK, "exchange")
os.makedirs(E, exist_ok=True)

ORTAK = [
  ('lang="tr"', 'lang="en"'), ('"tr-TR"', '"en-US"'),
  ('// Desteklenen test ağları: MetaMask\'ta yoksa otomatik eklenir', '// Supported networks: added to MetaMask automatically if missing'),
  ('''    84532: { chainId: "0x14a34",''', '''    8453: { chainId: "0x2105", chainName: "Base", nativeCurrency: { name: "Ether", symbol: "ETH", decimals: 18 },
             rpcUrls: ["https://mainnet.base.org"], blockExplorerUrls: ["https://basescan.org"] },
    84532: { chainId: "0x14a34",'''),
  ('{ 11155111: "Sepolia", 84532: "Base Sepolia" }', '{ 8453: "Base", 11155111: "Sepolia", 84532: "Base Sepolia" }'),
]

INDEX = [
  ('<title>AGIChainAI DEX</title>', '<title>AGIChainAI Exchange</title>'),
  ('<b>AGIChainAI <span style="color:var(--vurgu)">DEX</span></b>', '<b>AGIChainAI <span style="color:var(--vurgu)">Exchange</span></b>'),
  ('<button id="baglan">Cüzdan bağla</button>', '<button id="baglan">Connect wallet</button>'),
  ('<div class="bant">🧪 <b>TEST AĞI</b> (Base Sepolia) · Buradaki AGI ve ETH gerçek para değildir · <i>Testnet — tokens have no real value</i></div>',
   '<div class="bant">⚠️ <b>Live on Base mainnet</b> — real funds. Trade at your own risk. Not available to residents of Türkiye.</div>\n'
   '<section class="kart tr-engel gizli" id="tr-engel"><b>Not available in your region</b><p>This service is not offered to residents of Türkiye. '
   'If you are the operator, connect the operator wallet to continue.</p></section>'),
  ('<b>Borsayı ilk kez mi kullanıyorsunuz?</b>', '<b>New here?</b>'),
  ('<span id="r-cuzdan">MetaMask uygulamasını kurun:</span>', '<span id="r-cuzdan">Install the MetaMask app:</span>'),
  ("Bu sayfayı MetaMask'ta aç →", "Open this page in MetaMask →"),
  ('Base Sepolia ağını cüzdana ekle', 'Add the Base network to your wallet'),
  ('''<li>Ücretsiz test ETH'si alın (ağ: Base Sepolia):
        <a href="https://console.optimism.io/faucet" target="_blank" rel="noopener">Superchain faucet</a></li>''',
   '''<li>Have some ETH on the Base network for trading and fees.</li>'''),
  ("AGI token'ını cüzdana ekle", "Add the AGI token to your wallet"),
  ('''<li>"Cüzdan bağla" deyin ve <b>Takas</b> sekmesinden ETH ↔ AGI alıp satın.</li>''', '''<li>Tap "Connect wallet" and use the <b>Swap</b> tab to trade ETH ↔ AGI.</li>'''),
  ('<button data-sekme="takas" class="aktif">Takas</button>', '<button data-sekme="takas" class="aktif">Swap</button>'),
  ('<button data-sekme="ekle">Likidite ekle</button>', '<button data-sekme="ekle">Add liquidity</button>'),
  ('<button data-sekme="cek">Likidite çek</button>', '<button data-sekme="cek">Remove liquidity</button>'),
  ('<span>Veriyorsunuz</span>', '<span>You pay</span>'),
  ('title="Yön değiştir"', 'title="Switch direction"'),
  ('<span>Alıyorsunuz (tahmini)</span>', '<span>You receive (estimated)</span>'),
  ('Kayma toleransı:', 'Slippage tolerance:'),
  ('<button class="tam" id="t-btn" disabled>Takas et</button>', '<button class="tam" id="t-btn" disabled>Swap</button>'),
  ('<span>Varlık A</span>', '<span>Asset A</span>'), ('<span>Varlık B</span>', '<span>Asset B</span>'),
  ('<button class="tam" id="e-btn" disabled>Likidite ekle</button>', '<button class="tam" id="e-btn" disabled>Add liquidity</button>'),
  ('<div class="ince" id="c-bilgi">Havuz seçin.</div>', '<div class="ince" id="c-bilgi">Select a pool.</div>'),
  ('<span>Çekilecek oran</span>', '<span>Amount to remove</span>'),
  ('<button class="tam" id="c-btn" disabled>Likiditeyi çek</button>', '<button class="tam" id="c-btn" disabled>Remove liquidity</button>'),
  ('placeholder="Token ekle: 0x... adresi"', 'placeholder="Add token: 0x... address"'),
  ('<button id="ozel-ekle">Ekle</button>', '<button id="ozel-ekle">Add</button>'),
  ('''· Test ağı: <span id="ag-adi"></span><br><br>Bu arayüz, ağa kurduğunuz Uniswap V2 tabanlı kontratlarla çalışır. Herkes bu borsada token listeleyebilir.
  Bir token'ı almadan önce adresini resmî kaynaktan doğrulayın; işlemler geri alınamaz.</p>''',
   '''· Network: <span id="ag-adi"></span><br><br>This interface uses Uniswap V2–based smart contracts. Anyone can list a token on this exchange.
  Verify a token's address from an official source before buying. Transactions are irreversible. Crypto assets are volatile; you can lose funds.
  This service is not available to residents of Türkiye.</p>'''),
  ('''throw new Error("Bu adres bir ERC-20 token'ı gibi görünmüyor.")''', '''throw new Error("This address does not look like an ERC-20 token.")'''),
  ('"Bakiye: "', '"Balance: "'),
  ('durum("Onay (approve) bekleniyor… Cüzdanda sadece bu miktar için onay verin.");', 'durum("Waiting for approval… Approve only this amount in your wallet.");'),
  ('durum("Tarayıcıda MetaMask gibi bir cüzdan bulunamadı.", "hata");', 'durum("No wallet such as MetaMask was found in this browser.", "hata");'),
  ('durum(`Cüzdanınızı ${AG_ADI} ağına geçirin.`, "hata");', 'durum(`Switch your wallet to the ${AG_ADI} network.`, "hata");'),
  ('durum("Cüzdan bağlandı.", "ok");', 'durum("Wallet connected.", "ok");'),
  ('`En az alınacak: ', '`Minimum received: '),
  ('· İşlem ücreti %0,3${C.platformUcreti ? " (%0,25 likidite sağlayıcılarına, %0,05 platforma)" : ""}`',
   '· Fee 0.3%${C.platformUcreti ? " (0.25% to liquidity providers, 0.05% to the platform)" : ""}`'),
  ('"Bu çift için havuz yok veya likidite yetersiz."', '"No pool for this pair, or insufficient liquidity."'),
  ('durum("Takas onayı bekleniyor…");', 'durum("Waiting for swap confirmation…");'),
  ('durum("İşlem gönderildi: " + tx.hash);', 'durum("Transaction sent: " + tx.hash);'),
  ('durum("Takas tamamlandı.", "ok");', 'durum("Swap complete.", "ok");'),
  ('"İki farklı varlık seçin."', '"Select two different assets."'),
  ('"Mevcut havuz oranına göre B miktarı hesaplandı."', '"Amount B calculated from the current pool ratio."'),
  ('"Bu çift için henüz havuz yok. İlk siz eklerseniz başlangıç fiyatını siz belirlersiniz."', '"No pool for this pair yet. If you add first, you set the starting price."'),
  ('durum("Likidite onayı bekleniyor…");', 'durum("Waiting for liquidity confirmation…");'),
  ('durum("Likidite eklendi. Karşılığında LP token aldınız.", "ok");', 'durum("Liquidity added. You received LP tokens.", "ok");'),
  ('"Bu çift için havuz yok."', '"No pool for this pair."'),
  ('"Bu havuzda payınız yok."', '"You have no share in this pool."'),
  ('`Payınız: ~', '`Your share: ~'),
  ('durum("Çekme onayı bekleniyor…");', 'durum("Waiting for removal confirmation…");'),
  ('durum("Likidite çekildi.", "ok");', 'durum("Liquidity removed.", "ok");'),
  ('return "İşlemi cüzdanda reddettiniz.";', 'return "You rejected the transaction in your wallet.";'),
  ('return "Bakiyeniz (veya gas için ETH) yetersiz.";', 'return "Insufficient balance (or ETH for gas).";'),
  ('return "Fiyat çok değişti; kayma toleransını artırın veya tekrar deneyin.";', 'return "Price moved too much. Increase slippage tolerance or try again.";'),
  ('return "İşlemin süresi doldu, tekrar deneyin.";', 'return "Transaction expired. Please try again.";'),
  ('return "Hata: " + kisa.slice(0, 200);', 'return "Error: " + kisa.slice(0, 200);'),
  ('durum("Önce cüzdan bağlayın.", "hata");', 'durum("Connect your wallet first.", "hata");'),
  ('durum("Token eklendi. Adresini resmî kaynaktan doğruladığınızdan emin olun.", "ok");', 'durum("Token added. Make sure you verified its address from an official source.", "ok");'),
  ('durum(e.message || "Geçersiz adres.", "hata");', 'durum(e.message || "Invalid address.", "hata");'),
  ('"Telefondaysanız sayfayı MetaMask uygulamasında açın; değilseniz kurun:"', '"On a phone, open this page in the MetaMask app; otherwise install it:"'),
  ('''durum("Önce MetaMask gerekli. Telefondaysanız 'Bu sayfayı MetaMask'ta aç' linkine dokunun.", "hata");''', '''durum("MetaMask is required. On a phone, tap 'Open this page in MetaMask'.", "hata");'''),
  ('durum(AG_ADI + " ağı hazır.", "ok");', 'durum(AG_ADI + " network is ready.", "ok");'),
  ('durum("Önce MetaMask gerekli.", "hata");', 'durum("MetaMask is required.", "hata");'),
  ('durum(t.symbol + " cüzdanınıza eklendi.", "ok");', 'durum(t.symbol + " added to your wallet.", "ok");'),
  ('durum("config.js bulunamadı. Önce deploy betiğini çalıştırın.", "hata");', 'durum("The exchange is not set up yet.", "hata");'),
  ('"dex-rehber-gizle"', '"exchange-guide-hide"'),
]

# Türkiye erişim bildirimi (istemci tarafı; işletmeci cüzdanı hariç)
TR_KOD = '''
  // Bölge bildirimi: Türkiye'de yerleşik kişilere hizmet verilmez (istemci tarafı, işletmeci cüzdanı hariç).
  const trBolge = (() => { try { return Intl.DateTimeFormat().resolvedOptions().timeZone === "Europe/Istanbul"; } catch (e) { return false; } })()
    || /^tr\\b/i.test(navigator.language || "");
  const isletmeciMi = (adr) => !!(C.isletmeci && adr && adr.toLowerCase() === C.isletmeci.toLowerCase());
  if (trBolge) { $("tr-engel").classList.remove("gizli"); }
'''

def donustur(kaynak, hedef, ciftler, ek=None):
    s = open(os.path.join(F, kaynak), encoding="utf-8").read()
    eksik = []
    for a, b in ORTAK + ciftler:
        if a in s: s = s.replace(a, b)
        elif a not in ('lang="tr"',): eksik.append(a[:70])
    if ek: s = ek(s)
    open(os.path.join(E, hedef), "w", encoding="utf-8").write(s)
    # Kullanıcıya görünen Türkçe metin kaldı mı? (yorum satırları ve değişken adları hariç)
    kalan = []
    for i, satir in enumerate(s.split("\n"), 1):
        t = satir.strip()
        if t.startswith("//") or t.startswith("<!--"): continue
        for m in re.findall(r'(?:"[^"\n]*"|`[^`\n]*`|>[^<\n]+<)', satir):
            if re.search(r"[çğıöşüÇĞİÖŞÜ]", m) and "Türkiye" not in m: kalan.append((i, m[:90]))
    return eksik, kalan

def index_ek(s):
    s = s.replace('''  let provider, signer, hesap, router, factory;''', TR_KOD + '''  let provider, signer, hesap, router, factory;''')
    s = s.replace('''    hesap = await signer.getAddress();''', '''    hesap = await signer.getAddress();
    if (trBolge && !isletmeciMi(hesap)) {
      provider = signer = hesap = null;
      durum("This service is not available to residents of Türkiye.", "hata");
      return;
    }''', 1)
    s = s.replace('''  .bant {''', '''  .tr-engel { border-color:#6b2a2a; margin-bottom:12px; font-size:13px; } .tr-engel p { color:var(--soluk); margin:6px 0 0; }
  .bant {''')
    return s

eksik, kalan = donustur("index.html", "index.html", INDEX, index_ek)
print("index eksik eşleşme:", eksik); print("index kalan Türkçe:", kalan)
shutil.copy(os.path.join(F, "ethers.umd.min.js"), E)
shutil.copy(os.path.join(F, "kontratlar.js"), E)

KUR = [
  ('<title>AGIChainAI DEX — Kurulum</title>', '<title>AGIChainAI Exchange — Setup</title>'),
  ('<header>AGIChainAI DEX — Kurulum ', '<header>AGIChainAI Exchange — Setup '),
  ('<h2>Bu sayfa ne yapar?</h2>', '<h2>What does this page do?</h2>'),
  ('''<p class="ince">Borsanın 4 kontratını <b>kendi cüzdanınızla</b> blokzincire kurar (WETH, Factory, Router ve sizin token'ınız) ve platform komisyonunu sizin adresinize açar.
    Toplam 5 onay gerekir. Kurucu siz olursunuz; token'ların tamamı ve borsanın ücret yetkisi sizin adresinizde kalır.
    Özel anahtarınız bu sayfaya hiçbir zaman girilmez.</p>''',
   '''<p class="ince">Deploys the exchange contracts <b>with your own wallet</b> (Factory, Router and your token; Base's official WETH is reused) and turns on the platform fee to your address.
    Each step asks for a confirmation in MetaMask. You are the deployer; the full token supply and the fee-setter role stay with your address.
    Your private key is never entered on this page. <b>This uses real ETH on Base mainnet.</b></p>'''),
  ('<h2>1. Cüzdan</h2>', '<h2>1. Wallet</h2>'),
  ('<div class="ince" id="cuzdan-bilgi">Bağlı değil.</div>', '<div class="ince" id="cuzdan-bilgi">Not connected.</div>'),
  ('<button id="baglan">Cüzdan bağla</button>', '<button id="baglan">Connect wallet</button>'),
  ('<label for="ad">Token adı</label>', '<label for="ad">Token name</label>'),
  ('<label for="sembol">Sembol</label>', '<label for="sembol">Symbol</label>'),
  ('<label for="arz">Toplam arz (adet)</label>', '<label for="arz">Total supply (tokens)</label>'),
  ('<p class="ince">Sabit arz: kurulumdan sonra yeni token basılamaz, dondurulamaz, vergi konamaz.</p>', '<p class="ince">Fixed supply: after deployment no new tokens can be minted, frozen or taxed.</p>'),
  ('<h2>3. Kurulum</h2>', '<h2>3. Deploy</h2>'),
  ('<button id="basla" disabled>Kurulumu başlat</button>', '<button id="basla" disabled>Start deployment</button>'),
  ("Teknik ayrıntı (sorun olursa bunu Claude'a gönderin)", "Technical details (send this to Claude if something goes wrong)"),
  ('<h2>Kurulum tamam</h2>', '<h2>Deployment complete</h2>'),
  ("<p class=\"ince\">Bu adresleri sayfaya eklenmesi için Claude'a gönderin (aşağıdaki düğmeyle kopyalayabilirsiniz).</p>", '<p class="ince">Send these addresses to Claude so they can be connected to the exchange page (use the button below to copy).</p>'),
  ('<button id="kopyala" class="ikincil">Adresleri kopyala</button>', '<button id="kopyala" class="ikincil">Copy addresses</button>'),
  ('{ anahtar: "weth", ad: "WETH (sarılmış ETH)" }', '{ anahtar: "weth", ad: "WETH (wrapped ETH)" }'),
  ('{ anahtar: "factory", ad: "Factory (havuz fabrikası)" }', '{ anahtar: "factory", ad: "Factory (pool factory)" }'),
  ('{ anahtar: "router", ad: "Router (takas yönlendirici)" }', '{ anahtar: "router", ad: "Router (swap router)" }'),
  ('{ anahtar: "komisyon", ad: "Platform komisyonunu aç (%0,05 sizin adresinize)" }', '{ anahtar: "komisyon", ad: "Turn on platform fee (0.05% to your address)" }'),
  ('{ anahtar: "dogrula", ad: "Kontrol: kontratlar birbirine doğru bağlı mı?" }', '{ anahtar: "dogrula", ad: "Check: are the contracts wired correctly?" }'),
  ('''"WETH (ağın resmî WETH'i, kurulum gerekmez)"''', '''"WETH (network's official WETH, no deployment needed)"'''),
  ('return "Onayı reddettiniz. Kaldığınız yerden devam etmek için tekrar basın.";', 'return "You rejected the confirmation. Tap again to continue where you left off.";'),
  ("return `${AG_ADI} ağında test ETH'niz yetersiz veya henüz gelmedi. MetaMask'ta ağı ${AG_ADI} yapıp bakiyeyi kontrol edin.`;", "return `Not enough ETH on ${AG_ADI} (or it has not arrived yet). Switch MetaMask to ${AG_ADI} and check your balance.`;"),
  ('return "Cüzdanda bekleyen başka bir işlem var. Birkaç saniye bekleyip tekrar deneyin.";', 'return "Another transaction is pending in your wallet. Wait a few seconds and try again.";'),
  ('return "Ağ bağlantısı koptu. Birkaç saniye bekleyip tekrar deneyin.";', 'return "Network connection lost. Wait a few seconds and try again.";'),
  ('''return `MetaMask işlemi gönderemedi (ayrıntı vermedi). Ağın ${AG_ADI} olduğunu ve bakiyenizi kontrol edip "Kuruluma devam et"e tekrar basın. Sorun sürerse MetaMask'ı kapatıp açın.`;''',
   '''return `MetaMask could not send the transaction (no details given). Check that the network is ${AG_ADI} and your balance, then tap "Continue setup" again. If it persists, restart MetaMask.`;'''),
  ('return "Hata: " +', 'return "Error: " +'),
  ('durum("Cüzdan bulunamadı. Bu sayfayı MetaMask uygulamasının içindeki tarayıcıdan açın.", "hata");', 'durum("No wallet found. Open this page in the MetaMask app browser.", "hata");'),
  ('durum(`Cüzdanınızı ${AG_ADI} test ağına geçirin ve tekrar bağlanın.`, "hata");', 'durum(`Switch your wallet to ${AG_ADI} and connect again.`, "hata");'),
  ('`Tahmini işlem ücreti: ~${Number(ethers.formatEther(gerekli)).toFixed(4)} ETH (gas fiyatına göre değişir).`', '`Estimated network fee: ~${Number(ethers.formatEther(gerekli)).toFixed(5)} ETH (depends on gas price).`'),
  ('$("baglan").textContent = "Bağlandı";', '$("baglan").textContent = "Connected";'),
  ('''durum("Bakiye tahmini ücretin altında görünüyor. Yine de deneyebilirsiniz; yetmezse faucet'ten biraz daha alın.", "hata");''', '''durum("Your balance looks lower than the estimated fee. You can still try; add a little more ETH if it fails.", "hata");'''),
  ('kayit.factory && !kayit.dogrulandi ? "Kuruluma devam et" : kayit.dogrulandi ? "Kurulum zaten tamam" : "Kurulumu başlat"', 'kayit.factory && !kayit.dogrulandi ? "Continue setup" : kayit.dogrulandi ? "Setup already complete" : "Start deployment"'),
  ('throw new Error("İşlem blokzincirde başarısız oldu (revert). Hash: " + hash);', 'throw new Error("Transaction failed on-chain (revert). Hash: " + hash);'),
  ('throw new Error("İşlem çok uzun sürdü. Kaşifte kontrol edin: " + hash);', 'throw new Error("Transaction is taking too long. Check the explorer: " + hash);'),
  ("durum(`MetaMask'ta onay bekleniyor: ${ADIMLAR.find((a) => a.anahtar === adimAnahtari).ad}…`);", "durum(`Waiting for confirmation in MetaMask: ${ADIMLAR.find((a) => a.anahtar === adimAnahtari).ad}…`);"),
  ('durum("İşlem gönderildi, blokzincire yazılması bekleniyor… (" + hash.slice(0, 12) + "…)");', 'durum("Transaction sent, waiting for it to be mined… (" + hash.slice(0, 12) + "…)");'),
  ('throw new Error("Kontrat adresi alınamadı. Hash: " + hash);', 'throw new Error("Could not get contract address. Hash: " + hash);'),
  ('durum("Token adı ve sembolü boş olamaz.", "hata");', 'durum("Token name and symbol cannot be empty.", "hata");'),
  ('durum("Arz 1 ile 999 trilyon arasında bir tam sayı olmalı.", "hata");', 'durum("Supply must be a whole number between 1 and 999 trillion.", "hata");'),
  ('durum("Token zaten kuruldu; adı ve arzı artık değiştirilemez.", "hata");', 'durum("The token is already deployed; its name and supply cannot be changed.", "hata");'),
  ("durum(`${AG_ADI} ağında bakiyeniz 0 görünüyor. Test ETH'si henüz gelmemiş olabilir; birkaç dakika bekleyip tekrar deneyin.`, \"hata\");", "durum(`Your balance on ${AG_ADI} is 0. Fund the wallet with ETH on ${AG_ADI} and try again.`, \"hata\");"),
  ("durum(\"MetaMask'ta onay bekleniyor: platform komisyonunu açma…\");", 'durum("Waiting for confirmation in MetaMask: turning on the platform fee…");'),
  ('durum("İşlem gönderildi, bekleniyor…");', 'durum("Transaction sent, waiting…");'),
  ('durum("Kontroller yapılıyor…");', 'durum("Running checks…");'),
  ('sorunlar.push("Router → Factory bağlantısı")', 'sorunlar.push("Router → Factory link")'),
  ('sorunlar.push("Router → WETH bağlantısı")', 'sorunlar.push("Router → WETH link")'),
  ('sorunlar.push("Factory yetkisi")', 'sorunlar.push("Factory fee-setter")'),
  ('sorunlar.push("Komisyon adresi")', 'sorunlar.push("Fee address")'),
  ('sorunlar.push("Token bakiyesi")', 'sorunlar.push("Token balance")'),
  ('throw new Error("Kontrol başarısız: " + sorunlar.join(", "));', 'throw new Error("Check failed: " + sorunlar.join(", "));'),
  ('durum("Kurulum tamamlandı ve kontrol edildi.", "ok");', 'durum("Deployment complete and verified.", "ok");'),
  ('$("kopyala").textContent = "Kopyalandı ✓";', '$("kopyala").textContent = "Copied ✓";'),
  ('''$("kopyala").textContent = "Metin seçildi, Kopyala'ya basın";''', '''$("kopyala").textContent = "Text selected — tap Copy";'''),
  ('"Not: Borsa bu sitede zaten kurulu. Bu sayfayı sadece yeni bir kurulum yapmak istiyorsanız kullanın."', '"Note: The exchange is already set up on this site. Use this page only for a new deployment."'),
  ('durum("kontratlar.js yüklenemedi.", "hata");', 'durum("Could not load kontratlar.js.", "hata");'),
  ('$("basla").disabled = false; $("basla").textContent = "Kuruluma devam et";', '$("basla").disabled = false; $("basla").textContent = "Continue setup";'),
  ('$("basla").disabled = true; $("basla").textContent = "Kurulum zaten tamam";', '$("basla").disabled = true; $("basla").textContent = "Setup already complete";'),
  ('"dex-kurulum-', '"exchange-setup-'),
  ('`dex-kurulum-', '`exchange-setup-'),
]
eksik, kalan = donustur("kur.html", "setup.html", KUR)
print("setup eksik eşleşme:", eksik); print("setup kalan Türkçe:", kalan)
