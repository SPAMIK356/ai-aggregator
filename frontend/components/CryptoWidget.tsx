import { getCryptoSnapshot } from "../lib/crypto";

function formatUSD(n: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 }).format(n);
}

export default async function CryptoWidget() {
  try {
    const snap = await getCryptoSnapshot();
    return (
      <div className="crypto-widget" aria-label="Crypto prices">
        {[{ key: "BTC", v: snap.btc }, { key: "ETH", v: snap.eth }].map(({ key, v }) => {
          const pos = v.change24h >= 0;
          return (
            <div key={key} className="crypto-chip">
              <div className="crypto-symbol">{key}</div>
              <div className="crypto-price">{formatUSD(v.price)}</div>
              <div className={pos ? "crypto-change up" : "crypto-change down"}>{v.change24h.toFixed(2)}%</div>
            </div>
          );
        })}
      </div>
    );
  } catch {
    return null;
  }
}



