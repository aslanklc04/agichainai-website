import os, json, sys, urllib.request, threading, http.server, functools, time
from playwright.sync_api import sync_playwright

FRONT = sys.argv[1]
RPC = "http://127.0.0.1:8545"

def rpc(method, params):
    if method == "eth_requestAccounts": method = "eth_accounts"
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params or []}).encode()
    req = urllib.request.Request(RPC, body, {"Content-Type":"application/json"})
    r = json.load(urllib.request.urlopen(req))
    if "error" in r: return json.dumps({"error": r["error"]})
    return json.dumps({"result": r["result"]})

Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=FRONT)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8099), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()

SHIM = """
window.ethereum = { request: async ({method, params}) => {
  const r = JSON.parse(await window.__rpc(method, params || []));
  if (r.error) { const e = new Error(r.error.message); e.code = r.error.code; e.data = r.error.data; throw e; }
  return r.result; }, on: () => {} };
"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get("CHROME_YOLU") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":420,"height":900})
    pg.on("console", lambda m: print("console:", m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: print("pageerror:", e))
    pg.expose_function("__rpc", rpc)
    pg.add_init_script(SHIM)
    pg.goto("http://127.0.0.1:8099/index.html")
    st = lambda: pg.inner_text("#durum")
    def bekle(metin, t=20):
        for _ in range(t*4):
            if metin in st(): return
            if "Hata" in st(): raise SystemExit("HATA: " + st())
            pg.wait_for_timeout(250)
        raise SystemExit(f"zaman aşımı, durum: {st()}")

    pg.click("#baglan"); bekle("bağlandı"); print("1 bağlandı:", pg.inner_text("#baglan"))
    # Likidite ekle: 1.000.000 ALC + 10 ETH
    pg.click("[data-sekme=ekle]")
    pg.select_option("#e-a", "ETH"); pg.select_option("#e-b", label="ALC")
    pg.fill("#e-m1", "10"); pg.wait_for_timeout(int(1*1000)); print("  bilgi:", pg.inner_text("#e-bilgi"))
    pg.fill("#e-m2", "1000000"); pg.click("#e-btn"); bekle("Likidite eklendi"); print("2", st())
    # Takas: 1 ETH -> ALC
    pg.click("[data-sekme=takas]")
    pg.select_option("#t-from", "ETH"); pg.select_option("#t-to", label="ALC")
    pg.fill("#t-miktar", "1"); pg.wait_for_timeout(int(1.5*1000))
    print("3 teklif:", pg.evaluate("document.getElementById('t-cikti').value"), "|", pg.inner_text("#t-bilgi"))
    pg.click("#t-btn"); bekle("Takas tamamlandı"); print("  ", st(), pg.inner_text("#t-bak2"))
    # Ters takas: 5000 ALC -> ETH (approve dahil)
    pg.click("#t-ters"); pg.fill("#t-miktar", "5000"); pg.wait_for_timeout(int(1.5*1000))
    print("4 teklif:", pg.evaluate("document.getElementById('t-cikti').value"))
    pg.click("#t-btn"); bekle("Takas tamamlandı"); print("  ", st())
    # Likidite çek %50
    pg.click("[data-sekme=cek]")
    pg.select_option("#c-a", "ETH"); pg.select_option("#c-b", label="ALC"); pg.wait_for_timeout(int(1.5*1000))
    print("5", pg.inner_text("#c-bilgi"))
    pg.fill("#c-yuzde", "50"); pg.dispatch_event("#c-yuzde", "input")
    pg.click("#c-btn"); bekle("Likidite çekildi"); print("  ", st())
    pg.wait_for_timeout(int(1.5*1000)); print("  sonra:", pg.inner_text("#c-bilgi"))
    pg.click("[data-sekme=takas]"); pg.screenshot(path="ekran_temel.png")
    b.close()
print("UI TESTİ BAŞARILI")
