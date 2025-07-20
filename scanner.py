import os, sys, time, threading, json, requests
from http.server import SimpleHTTPRequestHandler, HTTPServer
from concurrent.futures import ThreadPoolExecutor
from mnemonic import Mnemonic
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins
from colorama import Fore, Style, init

init(autoreset=True)

# 🔑 Set your Ethers V2 API key here:
ETHERSCAN_KEY = "YOUR_ETHERSCAN_V2_API_KEY"

THREADS = 100
FOUND_FILE = "found_wallets.txt"
mnemo = Mnemonic("english")
lock = threading.Lock()

SUPPORTED_CHAINS = {
    "ETH": {"api": "https://api.etherscan.io/api", "color": Fore.WHITE},
    "BNB": {"api": "https://api.bscscan.com/api", "color": Fore.YELLOW},
    "MATIC": {"api": "https://api.polygonscan.com/api", "color": Fore.CYAN},
    "AVAX": {"api": "https://api.snowtrace.io/api", "color": Fore.RED},
}
FULL_CHAINS = {**SUPPORTED_CHAINS,
               "SOL": {"rpc": "https://api.mainnet-beta.solana.com", "color": Fore.MAGENTA},
               "BTC": {"color": Fore.GREEN}}

DERIVATION_PATHS = ["m/44'/60'/0'/0/0","m/44'/60'/0'/0/1","m/44'/60'/1'/0/0"]

# 📊 Stats
wallets_checked = 0
found_wallets = []
start_time = time.time()

def clear_line():
    sys.stdout.write("\r" + " " * 80 + "\r")

def print_banner():
    os.system("cls" if os.name=="nt" else "clear")
    print(f"{Fore.LIGHTMAGENTA_EX}"
          "📡 Multi‑chain mnemonic scanner w/ terminal + web dashboard\n"
          f"Threads: {THREADS}\n{Style.RESET_ALL}")

def fetch_balance(api_url, addr):
    try:
        r = requests.get(api_url, params={"module":"account","action":"balance","address":addr,"tag":"latest","apikey":ETHERSCAN_KEY}, timeout=8).json()
        return int(r.get("result","0")) / 1e18 if r.get("status")=="1" else 0
    except:
        return 0

def fetch_nft_count(api_url, addr):
    try:
        r = requests.get(api_url, params={"module":"account","action":"tokennfttx","address":addr,"apikey":ETHERSCAN_KEY}, timeout=8).json()
        return len({tx["tokenID"] for tx in r.get("result",[])}) if r.get("status")=="1" else 0
    except:
        return 0

def fetch_solana(addr):
    try:
        r = requests.post(FULL_CHAINS["SOL"]["rpc"], json={"jsonrpc":"2.0","id":1,"method":"getBalance","params":[addr]}, timeout=8).json()
        return r["result"]["value"] / 1e9 if isinstance(r.get("result"), dict) else 0
    except:
        return 0

def fetch_btc(addr):
    try:
        r = requests.get(f"https://blockchain.info/q/addressbalance/{addr}", timeout=8)
        return int(r.text) / 1e8 if r.ok else 0
    except:
        return 0

def check_wallet():
    global wallets_checked
    phrase = mnemo.generate(strength=128)
    seed = Bip39SeedGenerator(phrase).Generate()
    balances, nft_counts = {}, {}

    for p in DERIVATION_PATHS:
        try:
            bip = Bip44.FromSeedAndPath(seed, p)
            addr = bip.PublicKey().ToAddress()

            for ch, info in FULL_CHAINS.items():
                if ch in SUPPORTED_CHAINS:
                    bal = fetch_balance(info["api"], addr)
                    nfts = fetch_nft_count(info["api"], addr)
                    if bal > 0 or nfts:
                        balances[ch] = balances.get(ch, 0) + bal
                        nft_counts[ch] = nft_counts.get(ch, 0) + nfts
                elif ch == "SOL":
                    bal = fetch_solana(addr)
                    if bal > 0: balances["SOL"] = balances.get("SOL",0)+bal
                elif ch == "BTC":
                    bal = fetch_btc(addr)
                    if bal > 0: balances["BTC"] = balances.get("BTC",0)+bal
        except:
            continue

    total = sum(balances.values())
    wallets_checked += 1

    q = ""
    if balances:
        with lock, open(FOUND_FILE,"a") as f:
            for ch, bal in balances.items():
                f.write(f"{bal:.6f} {ch} | NFTs: {nft_counts.get(ch,0)} : {phrase}\n")
        for ch, bal in balances.items():
            clr = FULL_CHAINS[ch]["color"]
            n = nft_counts.get(ch,0)
            q += f"{clr}Balance:{bal:.6f}|TOTAL:{total:.6f}|NFTs:{n}|{ch}:{phrase}{Style.RESET_ALL}\n"
    print_status_line()
    if q: print("\n"+q.strip())

def print_status_line():
    elapsed = time.time()-start_time
    speed = wallets_checked/elapsed if elapsed else 0
    clear_line()
    sys.stdout.write(f"{Fore.BLUE}[Status] Checked: {wallets_checked:,} | Speed: {speed:.2f} addr/sec{Style.RESET_ALL}")
    sys.stdout.flush()

class DashHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        elapsed = time.time()-start_time
        speed = wallets_checked/elapsed if elapsed else 0
        data = {"checked":wallets_checked,"speed":round(speed,2),"found":found_wallets[-20:]}
        html = "<html><head><meta http‑equiv='refresh' content='3'/>" \
               "<title>Scanner Dashboard</title></head><body>" \
               f"<h2>Status</h2><p>Checked: {wallets_checked:,}</p><p>Speed: {speed:.2f} addr/sec</p><h3>Found</h3><pre>{json.dumps(data['found'],indent=2)}</pre></body></html>"
        self.send_response(200); self.send_header("Content-type","text/html"); self.end_headers()
        self.wfile.write(html.encode())

def run_dashboard():
    srv = HTTPServer(("0.0.0.0",8000), DashHandler)
    srv.serve_forever()

if __name__=="__main__":
    try:
        print_banner()
        threading.Thread(target=run_dashboard,daemon=True).start()
        with ThreadPoolExecutor(max_workers=THREADS) as ex:
            while True: ex.submit(check_wallet)
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[!] Scanner stopped cleanly.{Style.RESET_ALL}")