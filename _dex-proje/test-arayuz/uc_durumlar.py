"""Arayüz uç durum testleri: token-token, özel token, XSS, reddetme, sandviç saldırısı, yanlış ağ, hatalı girişler."""
import os, json, sys, urllib.request, threading, http.server, functools
from playwright.sync_api import sync_playwright

FRONT = sys.argv[1]
RPC = "http://127.0.0.1:8545"
K = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kurulum.json")))
DURUM = {"reddet": False, "sandvic": False, "zincir": None}

def ham_rpc(method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}).encode()
    return json.load(urllib.request.urlopen(urllib.request.Request(RPC, body, {"Content-Type": "application/json"})))

def rpc(method, params):
    if method == "eth_requestAccounts": method = "eth_accounts"
    if method == "eth_chainId" and DURUM["zincir"]: return json.dumps({"result": DURUM["zincir"]})
    if method == "wallet_switchEthereumChain": return json.dumps({"error": {"code": 4902, "message": "Unrecognized chain"}})
    if method == "eth_sendTransaction" and DURUM["reddet"]:
        return json.dumps({"error": {"code": 4001, "message": "User rejected the request."}})
    if method == "eth_sendTransaction" and DURUM["sandvic"] and params[0].get("value", "0x0") not in ("0x0", None):
        DURUM["sandvic"] = False
        ham_rpc("eth_sendTransaction", [K["saldiri"]])  # saldırgan kullanıcıdan önce davranır
    r = ham_rpc(method, params)
    return json.dumps({"error": r["error"]} if "error" in r else {"result": r["result"]})

Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=FRONT)
Handler.log_message = lambda *a: None
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8098), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()

SHIM = """
window.ethereum = { request: async ({method, params}) => {
  const r = JSON.parse(await window.__rpc(method, params || []));
  if (r.error) { const e = new Error(r.error.message); e.code = r.error.code; e.data = r.error.data; throw e; }
  return r.result; }, on: () => {} };
"""
sonuclar = []
def kontrol(ad, kosul, detay=""):
    sonuclar.append((ad, bool(kosul)))
    print(("  ✔ " if kosul else "  ✘ ") + ad + (f"  [{detay}]" if detay and not kosul else ""))

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get("CHROME_YOLU") or None, args=["--no-sandbox"])
    def yeni_sayfa():
        pg = b.new_page(viewport={"width": 390, "height": 860})
        pg.on("pageerror", lambda e: print("    pageerror:", e))
        diyaloglar = []
        pg.on("dialog", lambda d: (diyaloglar.append(d.message), d.dismiss()))
        pg.expose_function("__rpc", rpc)
        pg.add_init_script(SHIM)
        pg.goto("http://127.0.0.1:8098/index.html")
        return pg, diyaloglar
    def bekle(pg, *metinler, t=15000):
        for _ in range(t // 200):
            s = pg.inner_text("#durum")
            if any(m in s for m in metinler): return s
            pg.wait_for_timeout(200)
        return pg.inner_text("#durum")

    # 1) Yanlış ağ
    DURUM["zincir"] = "0x1"
    pg, _ = yeni_sayfa()
    pg.click("#baglan"); s = bekle(pg, "ağına geçirin")
    kontrol("Yanlış ağda kullanıcı uyarılır, bağlantı kurulmaz", "ağına geçirin" in s and pg.inner_text("#baglan") == "Cüzdan bağla", s)
    pg.close(); DURUM["zincir"] = None

    pg, diyaloglar = yeni_sayfa()
    pg.click("#baglan"); bekle(pg, "bağlandı")
    kontrol("Doğru ağda cüzdan bağlanır", "bağlandı" in pg.inner_text("#durum"))

    # 2) Hatalı adres / ERC-20 olmayan adres
    pg.fill("#ozel-adres", "merhaba"); pg.click("#ozel-ekle"); s = bekle(pg, "Geçersiz", "invalid", "Hata", "bad address")
    kontrol("Geçersiz adres reddedilir", pg.query_selector("#durum.hata") is not None, s)
    pg.fill("#ozel-adres", K["saldiri"]["from"]); pg.click("#ozel-ekle"); s = bekle(pg, "ERC-20")
    kontrol("Token olmayan (cüzdan) adresi reddedilir", "ERC-20" in s, s)

    # 3) XSS: kötü niyetli sembollü token
    pg.fill("#ozel-adres", K["xss"]); pg.click("#ozel-ekle"); bekle(pg, "Token eklendi")
    pg.wait_for_timeout(500)
    xss = pg.evaluate("window.__xss === 1 || document.querySelector('img') !== null")
    kontrol("Kötü niyetli token adı (XSS) kod olarak çalışmaz", not xss and not diyaloglar)
    kontrol("Uzun token adı 12 karakterle sınırlanır", all(len(o) <= 12 for o in pg.eval_on_selector_all("#t-from option", "els => els.map(e => e.textContent)")))

    # 4) Token-token havuzu: ALC + TKB
    pg.fill("#ozel-adres", K["tkb"]); pg.click("#ozel-ekle"); bekle(pg, "Token eklendi")
    pg.click("[data-sekme=ekle]")
    pg.select_option("#e-a", label="ALC"); pg.select_option("#e-b", label="TKB")
    pg.fill("#e-m1", "50000"); pg.wait_for_timeout(800)
    kontrol("Havuz yoksa ilk likidite uyarısı gösterilir", "henüz havuz yok" in pg.inner_text("#e-bilgi"))
    pg.fill("#e-m2", "10000"); pg.click("#e-btn"); s = bekle(pg, "Likidite eklendi", "Hata")
    kontrol("Token-token likidite eklenir (iki onay + ekleme)", "Likidite eklendi" in s, s)
    pg.fill("#e-m1", "5000"); pg.dispatch_event("#e-m1", "input"); pg.wait_for_timeout(1000)
    kontrol("Var olan havuzda B miktarı orana göre otomatik hesaplanır", pg.input_value("#e-m2").startswith("1000"), pg.input_value("#e-m2"))

    # 5) Token-token takas
    pg.click("[data-sekme=takas]")
    pg.select_option("#t-from", label="ALC"); pg.select_option("#t-to", label="TKB")
    pg.fill("#t-miktar", "1000"); pg.wait_for_timeout(1200)
    pg.click("#t-btn"); s = bekle(pg, "Takas tamamlandı", "Hata")
    kontrol("Token-token takas tamamlanır", "Takas tamamlandı" in s, s)

    # 6) Havuzu olmayan çift
    pg.select_option("#t-from", label="TKB"); pg.select_option("#t-to", "ETH")
    pg.fill("#t-miktar", "10"); pg.wait_for_timeout(1200)
    kontrol("Havuzu olmayan çiftte buton kapalı ve açıklama gösterilir", pg.is_disabled("#t-btn") and "havuz yok" in pg.inner_text("#t-bilgi"))

    # 7) Aynı varlık seçimi, sıfır ve negatif miktar
    pg.select_option("#t-from", "ETH"); pg.select_option("#t-to", "ETH"); pg.fill("#t-miktar", "1"); pg.wait_for_timeout(500)
    kontrol("Aynı varlık seçilince takas yapılamaz", pg.is_disabled("#t-btn"))
    pg.select_option("#t-to", label="ALC")
    for deger in ["0", "-5", "abc"]:
        pg.fill("#t-miktar", deger); pg.wait_for_timeout(500)
        kontrol(f"Geçersiz miktar ({deger}) ile takas yapılamaz", pg.is_disabled("#t-btn"))

    # 8) Kullanıcı cüzdanda reddeder
    pg.fill("#t-miktar", "0.5"); pg.wait_for_timeout(1000)
    DURUM["reddet"] = True
    pg.click("#t-btn"); s = bekle(pg, "reddettiniz", "Hata")
    kontrol("Cüzdanda reddedilen işlem anlaşılır mesajla bildirilir", "reddettiniz" in s, s)
    DURUM["reddet"] = False

    # 9) Bakiye yetersiz
    pg.fill("#t-miktar", "50000"); pg.wait_for_timeout(1000)
    pg.click("#t-btn"); s = bekle(pg, "yetersiz", "Hata")
    kontrol("Yetersiz bakiye anlaşılır mesajla bildirilir", "yetersiz" in s.lower(), s)

    # 10) Sandviç saldırısı: kullanıcının işleminden hemen önce büyük alım yapılır
    pg.select_option("#t-kayma", "0.5")
    pg.fill("#t-miktar", "1"); pg.wait_for_timeout(1000)
    once = pg.inner_text("#t-bak2")
    DURUM["sandvic"] = True
    pg.click("#t-btn"); s = bekle(pg, "kayma", "Hata", "tamamlandı")
    kontrol("Fiyat araya giren işlemle değişirse kayma koruması işlemi durdurur", "kayma toleransını" in s, s)
    pg.wait_for_timeout(800)
    kontrol("Durdurulan işlemde kullanıcının token bakiyesi değişmez", pg.inner_text("#t-bak2") == once)

    # 11) Mobil görünüm: yatay taşma yok
    genislik = pg.evaluate("document.documentElement.scrollWidth")
    kontrol("Telefon ekranında (390px) yatay taşma yok", genislik <= 390, str(genislik))
    pg.screenshot(path="ekran_uc.png", full_page=True)
    b.close()

basarili = sum(1 for _, ok in sonuclar if ok)
print(f"\n{basarili}/{len(sonuclar)} arayüz testi başarılı")
sys.exit(0 if basarili == len(sonuclar) else 1)
