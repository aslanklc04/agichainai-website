import json, sys, http.server, functools, threading
from playwright.sync_api import sync_playwright
FRONT = sys.argv[1]
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=FRONT); H.log_message=lambda *a: None
threading.Thread(target=http.server.ThreadingHTTPServer(("127.0.0.1", 8094), H).serve_forever, daemon=True).start()
ok=[]
def k(ad,c,d=""): ok.append(bool(c)); print(("  ✔ " if c else "  ✘ ")+ad+("" if c else f"  [{d}]"))
istekler=[]
SHIM = """window.ethereum = { request: async ({method, params}) => { window.__istekler = (window.__istekler||[]).concat([{method, params}]);
  if (method === 'wallet_switchEthereumChain') { const e = new Error('Unrecognized chain ID'); e.code = 4902; throw e; }
  if (method === 'wallet_addEthereumChain' || method === 'wallet_watchAsset') return method === 'wallet_watchAsset' ? true : null;
  if (method === 'eth_chainId') return '0x14a34';
  return null; }, on: () => {} };"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME_YOLU") or None, args=["--no-sandbox"])
    # Cüzdansız ziyaretçi (ör. telefonda normal tarayıcı)
    pg = b.new_page(viewport={"width":390,"height":860}); hatalar=[]; pg.on("pageerror", lambda e: hatalar.append(str(e)))
    pg.goto("http://127.0.0.1:8094/index.html"); pg.wait_for_timeout(600)
    k("Test ağı uyarı bandı görünür", "TEST AĞI" in pg.inner_text(".bant"))
    k("Yeni ziyaretçiye rehber görünür", pg.is_visible("#rehber"))
    href = pg.get_attribute("#mm-ac", "href")
    k("Cüzdansız ziyaretçiye 'MetaMask'ta aç' linki verilir", pg.is_visible("#mm-ac") and href.startswith("https://metamask.app.link/dapp/127.0.0.1:8094/"), href)
    pg.click("#agi-ekle"); pg.wait_for_timeout(300)
    k("Cüzdan yokken AGI ekle anlaşılır uyarı verir", "MetaMask gerekli" in pg.inner_text("#durum"))
    k("AGI listede (cüzdansız)", "AGI" in pg.eval_on_selector_all("#t-to option","e=>e.map(x=>x.textContent)"))
    k("Sayfada JS hatası yok", not hatalar, str(hatalar))
    genislik = pg.evaluate("document.documentElement.scrollWidth"); k("390px ekranda yatay taşma yok", genislik <= 390, str(genislik))
    pg.screenshot(path="ekran_rehber.png", full_page=True); pg.close()
    # Cüzdanlı ziyaretçi
    pg = b.new_page(viewport={"width":390,"height":860}); pg.add_init_script(SHIM)
    pg.goto("http://127.0.0.1:8094/index.html"); pg.wait_for_timeout(600)
    k("Cüzdan varken 'MetaMask'ta aç' linki gizli", not pg.is_visible("#mm-ac"))
    pg.click("#ag-ekle"); pg.wait_for_timeout(400)
    ist = pg.evaluate("window.__istekler || []")
    ekle = [x for x in ist if x["method"] == "wallet_addEthereumChain"]
    k("'Ağı ekle' Base Sepolia'yı doğru bilgilerle ekler", ekle and ekle[0]["params"][0]["chainId"] == "0x14a34" and "hazır" in pg.inner_text("#durum"), str(ist)[:200])
    pg.click("#agi-ekle"); pg.wait_for_timeout(400)
    ist = pg.evaluate("window.__istekler || []")
    izle = [x for x in ist if x["method"] == "wallet_watchAsset"]
    o = izle[0]["params"]["options"] if izle else {}
    k("'AGI ekle' doğru token adresiyle cüzdana ekler", o.get("address") == "0xC5b4f8E62dBe505F60446Abe4539aaBc8259b47C" and o.get("symbol") == "AGI" and o.get("decimals") == 18, str(o))
    b.close()
print(f"{sum(ok)}/{len(ok)} rehber testi başarılı")
