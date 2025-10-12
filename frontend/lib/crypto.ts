// Server-side utility to fetch BTC/ETH prices with 24h change, cached for 60s
// Uses CoinGecko simple price endpoint. Supports demo/pro API key via header.

type PriceItem = { usd: number; usd_24h_change?: number };
export type CryptoSnapshot = {
  ts: number;
  btc: { price: number; change24h: number };
  eth: { price: number; change24h: number };
};

let cache: CryptoSnapshot | null = null;
const TTL_MS = 60_000;

export async function getCryptoSnapshot(): Promise<CryptoSnapshot> {
  const now = Date.now();
  if (cache && now - cache.ts < TTL_MS) return cache;

  const key = process.env.COINGECKO_PRO_API_KEY || process.env.COINGECKO_API_KEY || process.env.COINGECKO_DEMO_API_KEY;
  const headers: Record<string, string> = {};
  if (key) {
    // CoinGecko supports demo and pro headers
    headers["x-cg-pro-api-key"] = key;
    headers["x-cg-demo-api-key"] = key;
  }

  const url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true";
  const res = await fetch(url, { headers, next: { revalidate: 60 } });
  if (!res.ok) {
    // Fallback to last cache if available
    if (cache) return cache;
    throw new Error(`CoinGecko error: ${res.status}`);
  }
  const data = (await res.json()) as { bitcoin: PriceItem; ethereum: PriceItem };
  const snap: CryptoSnapshot = {
    ts: now,
    btc: { price: data.bitcoin.usd, change24h: Number(data.bitcoin.usd_24h_change || 0) },
    eth: { price: data.ethereum.usd, change24h: Number(data.ethereum.usd_24h_change || 0) },
  };
  cache = snap;
  return snap;
}



