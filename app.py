from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import aiohttp
import ccxt.async_support as ccxt
import pandas as pd
import pandas_ta as ta
import uvicorn
import os

app = FastAPI()

# Initialize CEX Client
exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

# Mobile-Optimized Telegram Mini App Frontend Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Alpha TMA</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen p-4 font-sans pb-10">
    <div class="max-w-md mx-auto space-y-5">
        <!-- Header -->
        <div class="text-center space-y-1 pt-2">
            <h1 class="text-xl font-black tracking-tight text-emerald-400">⚡ AlphaFlow Mini App</h1>
            <p class="text-xs text-slate-400">Institutional TA, FA & Portfolio Risk Engine</p>
        </div>

        <!-- Input Card -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-3.5 shadow-xl">
            <div>
                <label class="block text-xs font-semibold text-slate-300 mb-1">Token Symbol / Contract</label>
                <input type="text" id="query" placeholder="e.g. BTC or SOL" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 uppercase">
            </div>
            <div class="grid grid-cols-2 gap-3">
                <div>
                    <label class="block text-xs font-semibold text-slate-300 mb-1">Portfolio Size ($)</label>
                    <input type="number" id="portfolio" value="5000" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-300 mb-1">Leverage (Perps)</label>
                    <input type="number" id="leverage" value="5" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500">
                </div>
            </div>
            <button onclick="runAnalysis()" class="w-full bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold py-3 rounded-xl transition text-sm shadow-lg shadow-emerald-500/20 active:scale-95">
                Analyze Setup 🚀
            </button>
        </div>

        <!-- Loading State -->
        <div id="loading" class="hidden text-center py-8">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-emerald-500 border-t-transparent"></div>
            <p class="text-xs text-slate-400 mt-2">Scanning order books & liquidity pools...</p>
        </div>

        <!-- Results Display -->
        <div id="results" class="hidden space-y-4">
            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-3.5 shadow-xl">
                <div class="flex justify-between items-center border-b border-slate-800 pb-3">
                    <div>
                        <h2 id="res-symbol" class="font-bold text-base text-emerald-400">---</h2>
                        <span id="res-venue" class="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-slate-300">---</span>
                    </div>
                    <div class="text-right">
                        <div id="res-price" class="font-mono font-bold text-sm">---</div>
                        <div id="res-change" class="text-xs">---</div>
                    </div>
                </div>

                <!-- Market Data -->
                <div class="grid grid-cols-2 gap-2 text-xs text-slate-300 bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/50">
                    <div>Volume (24h): <span id="res-vol" class="font-mono font-bold text-white">---</span></div>
                    <div id="res-metric-container">Metric: <span id="res-metric-val" class="font-mono font-bold text-white">---</span></div>
                </div>

                <!-- Trade Setup -->
                <div class="space-y-1.5">
                    <div class="text-[11px] font-bold text-slate-400 uppercase tracking-wider">🎯 Optimized Execution Setup</div>
                    <div class="bg-slate-950 border border-slate-800/50 rounded-xl p-3 space-y-2 text-xs font-mono">
                        <div class="flex justify-between"><span>Entry Price:</span> <span id="setup-entry" class="text-white font-bold">---</span></div>
                        <div class="flex justify-between"><span>Stop Loss:</span> <span id="setup-sl" class="text-rose-400 font-bold">---</span></div>
                        <div class="flex justify-between"><span>Take Profit 1:</span> <span id="setup-tp1" class="text-emerald-400 font-bold">---</span></div>
                        <div class="flex justify-between"><span>Take Profit 2:</span> <span id="setup-tp2" class="text-emerald-300 font-bold">---</span></div>
                    </div>
                </div>

                <!-- Risk Sizing -->
                <div class="space-y-1.5">
                    <div class="text-[11px] font-bold text-slate-400 uppercase tracking-wider">⚖️ Portfolio Risk Sizing</div>
                    <div class="bg-slate-950 border border-slate-800/50 rounded-xl p-3 space-y-2 text-xs font-mono">
                        <div class="flex justify-between"><span>Max Risk (1.5%):</span> <span id="risk-usd" class="text-amber-400 font-bold">---</span></div>
                        <div class="flex justify-between"><span>Position Size:</span> <span id="risk-tokens" class="text-white font-bold">---</span></div>
                        <div class="flex justify-between"><span>Notional Value:</span> <span id="risk-notional" class="text-white font-bold">---</span></div>
                        <div class="flex justify-between"><span>Required Margin:</span> <span id="risk-margin" class="text-cyan-400 font-bold">---</span></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.expand(); // Expands Mini App to full screen view

        async function runAnalysis() {
            const query = document.getElementById('query').value.trim();
            const portfolio = document.getElementById('portfolio').value;
            const leverage = document.getElementById('leverage').value;

            if (!query) {
                alert('Please enter a valid token symbol or contract address.');
                return;
            }

            document.getElementById('loading').classList.remove('hidden');
            document.getElementById('results').classList.add('hidden');

            try {
                const response = await fetch(`/api/analyze?query=${encodeURIComponent(query)}&portfolio=${portfolio}&leverage=${leverage}`);
                const data = await response.json();

                if (data.error) {
                    alert(data.error);
                    return;
                }

                document.getElementById('res-symbol').innerText = `${data.symbol} (${data.name || ''})`;
                document.getElementById('res-venue').innerText = data.venue;
                document.getElementById('res-price').innerText = `$${Number(data.price).toLocaleString()}`;
                
                const changeEl = document.getElementById('res-change');
                changeEl.innerText = `${data.change_24h > 0 ? '+' : ''}${data.change_24h}%`;
                changeEl.className = `text-xs font-semibold ${data.change_24h >= 0 ? 'text-emerald-400' : 'text-rose-400'}`;

                document.getElementById('res-vol').innerText = `$${Number(data.volume_24h).toLocaleString()}`;
                
                if (data.type === 'CEX_PERP') {
                    document.getElementById('res-metric-container').innerHTML = `1H RSI: <span id="res-metric-val" class="font-mono font-bold text-white">${data.rsi_1h}</span>`;
                } else {
                    document.getElementById('res-metric-container').innerHTML = `Liquidity: <span id="res-metric-val" class="font-mono font-bold text-white">$${Number(data.liquidity).toLocaleString()}</span>`;
                }

                document.getElementById('setup-entry').innerText = `$${Number(data.entry).toLocaleString()}`;
                document.getElementById('setup-sl').innerText = `$${Number(data.stop_loss).toLocaleString()}`;
                document.getElementById('setup-tp1').innerText = `$${Number(data.tp1).toLocaleString()}`;
                document.getElementById('setup-tp2').innerText = `$${Number(data.tp2).toLocaleString()}`;

                document.getElementById('risk-usd').innerText = `$${data.risk.risk_usd.toLocaleString()}`;
                document.getElementById('risk-tokens').innerText = `${data.risk.tokens} ${data.symbol}`;
                document.getElementById('risk-notional').innerText = `$${data.risk.notional.toLocaleString()}`;
                document.getElementById('risk-margin').innerText = `$${data.risk.margin.toLocaleString()} (${data.risk.leverage}x)`;

                document.getElementById('results').classList.remove('hidden');
            } catch (err) {
                alert('Connection error or analytics timeout.');
                console.error(err);
            } finally {
                document.getElementById('loading').classList.add('hidden');
            }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_mini_app():
    return HTML_TEMPLATE

@app.get("/api/analyze")
async def analyze_api(query: str, portfolio: float = 5000.0, leverage: int = 1):
    data = None
    is_perp = True
    try:
        await exchange.load_markets()
        formatted_symbol = f"{query.upper()}/USDT:USDT"
        if formatted_symbol in exchange.markets:
            ticker = await exchange.fetch_ticker(formatted_symbol)
            ohlcv = await exchange.fetch_ohlcv(formatted_symbol, timeframe='1h', limit=50)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['rsi'] = ta.rsi(df['close'], length=14)
            current_rsi = round(float(df['rsi'].iloc[-1]), 2)
            
            data = {
                "type": "CEX_PERP",
                "name": query.upper(),
                "symbol": query.upper(),
                "price": float(ticker['last']),
                "volume_24h": float(ticker['quoteVolume']),
                "change_24h": float(ticker['percentage']),
                "rsi_1h": current_rsi,
                "venue": "CEX Futures"
            }
    except Exception as e:
        print(f"CEX error: {e}")

    if not data:
        is_perp = False
        leverage = 1
        url = f"https://api.dexscreener.com/latest/dex/search?q={query}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    res_json = await response.json()
                    pairs = res_json.get("pairs", [])
                    if pairs:
                        best = max(pairs, key=lambda x: float(x.get("liquidity", {}).get("usd", 0)))
                        data = {
                            "type": "DEX",
                            "name": best.get("baseToken", {}).get("name"),
                            "symbol": best.get("baseToken", {}).get("symbol"),
                            "price": float(best.get("priceUsd", 0)),
                            "liquidity": float(best.get("liquidity", {}).get("usd", 0)),
                            "volume_24h": float(best.get("volume", {}).get("h24", 0)),
                            "change_24h": float(best.get("priceChange", {}).get("h24", 0)),
                            "venue": f"DEX ({best.get('dexId', 'DEX').upper()})"
                        }

    if not data:
        return {"error": f"Could not find token data for '{query}'."}

    price = data["price"]
    buffer = 0.02 if is_perp else 0.04
    entry = price
    stop_loss = round(entry * (1 - buffer), 6)
    tp1 = round(entry * (1 + (buffer * 1.5)), 6)
    tp2 = round(entry * (1 + (buffer * 3.0)), 6)

    risk_pct = 1.5
    risk_amount = portfolio * (risk_pct / 100.0)
    price_risk = abs(entry - stop_loss)
    position_tokens = risk_amount / price_risk if price_risk > 0 else 0
    notional_value = position_tokens * entry
    required_margin = notional_value / leverage if is_perp else notional_value

    risk_data = {
        "risk_usd": round(risk_amount, 2),
        "tokens": round(position_tokens, 4),
        "notional": round(notional_value, 2),
        "margin": round(required_margin, 2),
        "leverage": leverage
    }

    return {
        **data,
        "entry": entry,
        "stop_loss": stop_loss,
        "tp1": tp1,
        "tp2": tp2,
        "risk": risk_data
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
