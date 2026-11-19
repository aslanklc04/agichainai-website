import os, json, sys, urllib.request, threading, http.server, functools
from playwright.sync_api import sync_playwright
FRONT = sys.argv[1]; RPC = "http://127.0.0.1:8545"
D = {"reddet_sayac": None, "gonderim": 0, "ag_yok": True, "eklendi": False, "ekleme_istegi": None, "bakiye0": False, "ic_hata": False, "genel_hata": False}
def rpc(method, params):
    if method == "eth_requestAccounts": method = "eth_accounts"
    if D["ag_yok"] and not D["eklendi"]:
        if method == "eth_chainId": return json.dumps({"result": "0x1"})
        if method == "wallet_switchEthereumChain": return json.dumps({"error": {"code": 4902, "message": "Unrecognized chain ID"}})
    if method == "wallet_addEthereumChain":
        D["eklendi"] = True; D["ekleme_istegi"] = params[0]; return json.dumps({"result": None})
    if method == "wallet_switchEthereumChain": return json.dumps({"result": None})
    if method == "eth_getBalance" and D["bakiye0"]: return json.dumps({"result": "0x0"})
    if method == "eth_sendTransaction" and D["genel_hata"]:
        D["genel_hata"] = False
        return json.dumps({"error": {"code": -32603, "message": "Internal JSON-RPC error."}})
    if method == "eth_sendTransaction" and D["ic_hata"]:
        D["ic_hata"] = False
        return json.dumps({"error": {"code": -32603, "message": "Internal JSON-RPC error.", "data": {"code": -32000, "message": "insufficient funds for gas * price + value: balance 0"}}})
    if method == "eth_sendTransaction":
        D["gonderim"] += 1
        if D["reddet_sayac"] == D["gonderim"]:
            return json.dumps({"error": {"code": 4001, "message": "User rejected the request."}})
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params or []}).encode()
    r = json.load(urllib.request.urlopen(urllib.request.Request(RPC, body, {"Content-Type":"application/json"})))
    return json.dumps({"error": r["error"]} if "error" in r else {"result": r["result"]})
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=FRONT); H.log_message = lambda *a: None
threading.Thread(target=http.server.ThreadingHTTPServer(("127.0.0.1", 8097), H).serve_forever, daemon=True).start()
SHIM = """window.ethereum = { request: async ({method, params}) => { const r = JSON.parse(await window.__rpc(method, params || []));
 if (r.error) { const e = new Error(r.error.message); e.code = r.error.code; e.data = r.error.data; throw e; } return r.result; }, on: () => {} };"""
ok = []
def k(ad, c, d=""): ok.append(c); print(("  ✔ " if c else "  ✘ ") + ad + ("" if c else f"  [{d}]"))
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get("CHROME_YOLU") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":390,"height":900}); pg.on("pageerror", lambda e: print("pageerror", e))
    pg.expose_function("__rpc", rpc); pg.add_init_script(SHIM); pg.goto("http://127.0.0.1:8097/kur.html")
    st = lambda: pg.inner_text("#durum")
    def bekle(*m, t=30000):
        for _ in range(t//250):
            if any(x in st() for x in m): return st()
            pg.wait_for_timeout(250)
        return st()
    pg.click("#baglan"); pg.wait_for_timeout(1500)
    k("MetaMask'ta olmayan Base Sepolia ağı otomatik eklenir", D["eklendi"] and D["ekleme_istegi"]["chainId"] == "0x14a34" and "sepolia.base.org" in D["ekleme_istegi"]["rpcUrls"][0], str(D["ekleme_istegi"]))
    k("Sayfa başlığında ağ adı görünür", "Base Sepolia" in pg.inner_text("header"))
    k("Cüzdan bağlanır, bakiye ve tahmini ücret görünür", "Bakiye" in pg.inner_text("#cuzdan-bilgi") and "ücreti" in pg.inner_text("#maliyet"), pg.inner_text("#cuzdan-bilgi"))
    D["bakiye0"] = True
    pg.click("#basla"); pg.wait_for_timeout(800)
    k("Bakiye 0 iken başlamadan anlaşılır uyarı verilir", "bakiyeniz 0" in st(), st())
    D["bakiye0"] = False
    D["ic_hata"] = True
    pg.evaluate("document.getElementById('durum').textContent = ''")
    pg.click("#basla"); s0 = bekle("yetersiz", "Hata", "gönderemedi")
    k("MetaMask'ın iç içe 'yetersiz bakiye' hatası anlaşılır mesaja çevrilir", "yetersiz veya henüz gelmedi" in s0, s0)
    D["genel_hata"] = True
    pg.evaluate("document.getElementById('durum').textContent = ''")
    pg.click("#basla"); s1 = bekle("gönderemedi", "Hata")
    k("Ayrıntısız MetaMask hatası anlaşılır mesaja çevrilir, tekrar denenebilir", "gönderemedi" in s1 and pg.inner_text("#basla") == "Kuruluma devam et" and not D["genel_hata"], s1)
    pg.reload(); pg.click("#baglan"); pg.wait_for_timeout(1500)
    pg.fill("#arz", "12abc"); pg.click("#basla"); pg.wait_for_timeout(300)
    k("Geçersiz arz reddedilir", "tam sayı" in st(), st())
    pg.fill("#arz", "1000000000")
    D["reddet_sayac"] = D["gonderim"] + 3  # Router adımında reddet
    pg.evaluate("document.getElementById('durum').textContent = ''")
    pg.click("#basla"); s = bekle("reddettiniz", "Hata")
    k("3. adımda reddedilince anlaşılır mesaj ve devam düğmesi", "reddettiniz" in s and pg.inner_text("#basla") == "Kuruluma devam et", s)
    k("İlk iki kontrat kaydedildi", pg.inner_text("#adimlar").count("✅") == 2, pg.inner_text("#adimlar"))
    D["reddet_sayac"] = None
    pg.reload(); pg.click("#baglan"); pg.wait_for_timeout(1500)
    k("Sayfa yenilense bile kaldığı yer hatırlanır", pg.inner_text("#basla") == "Kuruluma devam et" and pg.inner_text("#adimlar").count("✅") == 2)
    once = D["gonderim"]
    pg.click("#basla"); s = bekle("tamamlandı", "Hata", t=60000)
    k("Kurulum tamamlanır ve kontrol edilir", "tamamlandı ve kontrol edildi" in s, s)
    k("Devam ederken sadece kalan 3 işlem gönderildi (tekrar kurulum yok)", D["gonderim"] - once == 3, str(D["gonderim"] - once))
    sonuc = json.loads(pg.inner_text("#sonuc"))
    k("Token adı ve sembolü AGI", sonuc["token"]["symbol"] == "AGI" and sonuc["token"]["ad"] == "AGI")
    k("Komisyon adresi kurucuya ayarlandı", sonuc["komisyonAdresi"] == sonuc["kurucu"])
    k("5 adımın tamamı işaretli", pg.inner_text("#adimlar").count("✅") == 6, pg.inner_text("#adimlar"))
    k("Sonuçta 4 adres var", all(sonuc[x] for x in ["weth","factory","router"]) and sonuc["token"]["address"])
    json.dump(sonuc, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kur_sonuc.json"),"w"), indent=2)
    pg.screenshot(path="ekran_kur.png", full_page=True); b.close()
print(f"{sum(bool(x) for x in ok)}/{len(ok)} kurulum sayfası testi başarılı")
