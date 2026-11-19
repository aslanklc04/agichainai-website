"""Base ana ağı simülasyonu: İngilizce kurulum + borsa + Türkiye bildirimi."""
import json, sys, urllib.request, threading, http.server, functools, shutil, os
from playwright.sync_api import sync_playwright
KAYNAK = sys.argv[1]; FRONT = "/tmp/exchange_test"
shutil.rmtree(FRONT, ignore_errors=True); shutil.copytree(KAYNAK, FRONT)
RPC = "http://127.0.0.1:8545"
def ham(method, params):
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params or []}).encode()
    return json.load(urllib.request.urlopen(urllib.request.Request(RPC, body, {"Content-Type":"application/json"})))
HESAPLAR = ham("eth_accounts", [])["result"]
D = {"hesap": HESAPLAR[0], "gonderim": 0}
def rpc(method, params):
    if method in ("eth_requestAccounts", "eth_accounts"): return json.dumps({"result": [D["hesap"]]})
    if method in ("wallet_switchEthereumChain", "wallet_addEthereumChain", "wallet_watchAsset"): return json.dumps({"result": None})
    if method == "eth_sendTransaction":
        D["gonderim"] += 1; params[0]["from"] = D["hesap"]
    r = ham(method, params)
    return json.dumps({"error": r["error"]} if "error" in r else {"result": r["result"]})
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=FRONT); H.log_message = lambda *a: None
threading.Thread(target=http.server.ThreadingHTTPServer(("127.0.0.1", 8092), H).serve_forever, daemon=True).start()
SHIM = """window.ethereum = { request: async ({method, params}) => { const r = JSON.parse(await window.__rpc(method, params || []));
 if (r.error) { const e = new Error(r.error.message); e.code = r.error.code; e.data = r.error.data; throw e; } return r.result; }, on: () => {} };"""
ok = []
def k(ad, c, d=""): ok.append(bool(c)); print(("  ✔ " if c else "  ✘ ") + ad + ("" if c else f"  [{d}]"))
def bekle(pg, *m, t=60000):
    for _ in range(t // 250):
        s = pg.inner_text("#durum")
        if any(x in s for x in m): return s
        pg.wait_for_timeout(250)
    return pg.inner_text("#durum")
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get("CHROME_YOLU") or None, args=["--no-sandbox"])
    # 1) Kurulum (işletmeci Türkiye'den yapar; kurulum sayfasında bölge engeli yok)
    ctx = b.new_context(viewport={"width":390,"height":900}, timezone_id="Europe/Istanbul", locale="tr-TR")
    pg = ctx.new_page(); pg.on("pageerror", lambda e: print("    pageerror:", e))
    pg.expose_function("__rpc", rpc); pg.add_init_script(SHIM)
    pg.goto("http://127.0.0.1:8092/setup.html"); pg.wait_for_timeout(500)
    k("Setup page is in English", "Setup" in pg.inner_text("header") and "Base" in pg.inner_text("header"))
    pg.click("#baglan"); pg.wait_for_timeout(1500)
    k("Official Base WETH is reused (no WETH deploy)", "official WETH" in pg.inner_text("#adimlar"), pg.inner_text("#adimlar"))
    once = D["gonderim"]
    pg.click("#basla"); s = bekle(pg, "complete and verified", "Error", "rejected")
    k("Deployment completes and verifies", "complete and verified" in s, s)
    k("Exactly 4 transactions (Factory, Router, Token, fee)", D["gonderim"] - once == 4, str(D["gonderim"] - once))
    sonuc = json.loads(pg.inner_text("#sonuc"))
    k("Result uses official WETH address", sonuc["weth"].lower() == "0x4200000000000000000000000000000000000006", sonuc["weth"])
    pg.close()
    # Adresleri borsa config'ine yaz (gerçek kurulumda Claude bunu yapar)
    cfg = {"chainId": 8453, "weth": sonuc["weth"], "factory": sonuc["factory"], "router": sonuc["router"], "isletmeci": D["hesap"],
           "platformUcreti": True, "tokens": [{"address": sonuc["token"]["address"], "symbol": sonuc["token"]["symbol"]}]}
    open(os.path.join(FRONT, "config.js"), "w").write("window.DEX_CONFIG = " + json.dumps(cfg) + ";\n")
    # 2) Türkiye'den işletmeci olmayan ziyaretçi engellenir
    D["hesap"] = HESAPLAR[1]
    pg = ctx.new_page(); pg.expose_function("__rpc", rpc); pg.add_init_script(SHIM)
    pg.goto("http://127.0.0.1:8092/index.html"); pg.wait_for_timeout(600)
    k("Exchange page is in English with mainnet warning", "Live on Base mainnet" in pg.inner_text(".bant"))
    k("Türkiye notice shown for Istanbul timezone", pg.is_visible("#tr-engel"))
    pg.click("#baglan"); pg.wait_for_timeout(1200)
    k("Non-operator wallet from Türkiye cannot connect", "not available to residents of Türkiye" in pg.inner_text("#durum") and pg.inner_text("#baglan") == "Connect wallet", pg.inner_text("#durum"))
    pg.close()
    # 3) İşletmeci Türkiye'den bağlanabilir, likidite ekler
    D["hesap"] = HESAPLAR[0]
    pg = ctx.new_page(); pg.expose_function("__rpc", rpc); pg.add_init_script(SHIM)
    pg.goto("http://127.0.0.1:8092/index.html"); pg.wait_for_timeout(600)
    pg.click("#baglan"); s = bekle(pg, "Wallet connected", "not available")
    k("Operator wallet can connect from Türkiye", "Wallet connected" in s, s)
    pg.click("[data-sekme=ekle]"); pg.select_option("#e-a", "ETH"); pg.select_option("#e-b", label="AGI")
    pg.fill("#e-m1", "1"); pg.wait_for_timeout(800); pg.fill("#e-m2", "1000000")
    pg.click("#e-btn"); s = bekle(pg, "Liquidity added", "Error")
    k("Operator adds liquidity", "Liquidity added" in s, s)
    pg.close(); ctx.close()
    # 4) Yurt dışından (ör. Berlin) kullanıcı takas yapar
    D["hesap"] = HESAPLAR[2]
    ctx = b.new_context(viewport={"width":390,"height":900}, timezone_id="Europe/Berlin", locale="en-US")
    pg = ctx.new_page(); pg.expose_function("__rpc", rpc); pg.add_init_script(SHIM)
    pg.goto("http://127.0.0.1:8092/index.html"); pg.wait_for_timeout(600)
    k("No Türkiye notice for visitor abroad", not pg.is_visible("#tr-engel"))
    pg.click("#baglan"); bekle(pg, "Wallet connected")
    pg.select_option("#t-from", "ETH"); pg.select_option("#t-to", label="AGI"); pg.fill("#t-miktar", "0.01"); pg.wait_for_timeout(1500)
    k("Quote shows English fee split", "0.05% to the platform" in pg.inner_text("#t-bilgi"), pg.inner_text("#t-bilgi"))
    pg.click("#t-btn"); s = bekle(pg, "Swap complete", "Error")
    k("Visitor abroad completes a swap", "Swap complete" in s, s)
    pg.screenshot(path="ekran_ana.png", full_page=True)
    b.close()
print(f"{sum(ok)}/{len(ok)} mainnet simulation checks passed")
