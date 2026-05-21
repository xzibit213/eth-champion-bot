import sys
import os
import json
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from engine.executor import SingleStrategyExecutor

# Premium HTML Template for the Bot Dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="30">
    <title>ETH Champion | Vanguard Terminal</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-deep: #050505;
            --bg-shell: rgba(255, 255, 255, 0.02);
            --bg-core: rgba(12, 12, 12, 0.7);
            --border-shell: rgba(255, 255, 255, 0.03);
            --border-core: rgba(255, 255, 255, 0.06);
            --accent-purple: #9f7aea;
            --accent-blue: #60a5fa;
            --accent-green: #34d399;
            --accent-red: #f87171;
            --text-1: #ffffff;
            --text-2: #a1a1aa;
            --text-3: #52525b;
            --bezier: cubic-bezier(0.32, 0.72, 0, 1);
        }
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
            background: var(--bg-deep);
            color: var(--text-1);
            min-height: 100dvh;
            overflow-x: hidden;
            -webkit-font-smoothing: antialiased;
        }

        /* Ethereal Glass Orbs */
        .bg-orb {
            position: fixed; border-radius: 50%; filter: blur(160px); opacity: 0.12; pointer-events: none; z-index: 0;
            will-change: transform;
        }
        .orb-1 { width: 800px; height: 800px; background: #9f7aea; top: -200px; left: -200px; animation: float1 30s ease-in-out infinite; }
        .orb-2 { width: 700px; height: 700px; background: #10b981; bottom: -200px; right: -200px; animation: float2 40s ease-in-out infinite; }
        @keyframes float1 { 0%,100% { transform: translate(0,0); } 50% { transform: translate(100px,100px); } }
        @keyframes float2 { 0%,100% { transform: translate(0,0); } 50% { transform: translate(-100px,-100px); } }

        .app-container {
            max-width: 1440px; margin: 0 auto; padding: 48px 24px 80px; position: relative; z-index: 1;
        }

        /* Top Bar */
        .top-bar {
            display: flex; align-items: center; justify-content: space-between;
            margin-bottom: 64px; padding: 0 16px;
        }
        .brand { display: flex; align-items: center; gap: 16px; }
        .brand-icon {
            width: 44px; height: 44px; border-radius: 12px;
            background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
            display: grid; place-items: center; font-size: 20px; color: #fff;
            box-shadow: inset 0 1px 1px rgba(255,255,255,0.2);
        }
        .brand-text { font-size: 22px; font-weight: 700; letter-spacing: -0.5px; }
        .brand-text span { color: var(--text-3); font-weight: 500; font-size: 14px; margin-left: 12px; letter-spacing: 0; }

        .live-chip {
            display: inline-flex; align-items: center; gap: 8px;
            padding: 8px 16px; border-radius: 999px; font-size: 11px; font-weight: 700;
            color: var(--text-2); text-transform: uppercase; letter-spacing: 1.5px;
            background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
        }
        .live-dot { width: 6px; height: 6px; background: var(--accent-green); border-radius: 50%; box-shadow: 0 0 10px var(--accent-green); }

        /* DOUBLE-BEZEL COMPONENT (Doppelrand) */
        .double-bezel {
            background: var(--bg-shell);
            border: 1px solid var(--border-shell);
            border-radius: 2rem;
            padding: 6px;
        }
        .db-inner {
            background: var(--bg-core);
            border: 1px solid var(--border-core);
            border-radius: calc(2rem - 6px);
            box-shadow: inset 0 1px 1px rgba(255,255,255,0.05);
            backdrop-filter: blur(40px); -webkit-backdrop-filter: blur(40px);
            height: 100%;
            overflow: hidden;
        }

        /* Layout Archetype: The Asymmetrical Bento */
        .bento-grid {
            display: grid;
            grid-template-columns: repeat(12, 1fr);
            gap: 24px;
            margin-bottom: 48px;
        }
        .col-span-8 { grid-column: span 8; }
        .col-span-4 { grid-column: span 4; }
        .col-span-12 { grid-column: span 12; }

        /* Typography Tags */
        .eyebrow {
            display: inline-block; padding: 4px 12px; border-radius: 999px;
            font-size: 10px; text-transform: uppercase; letter-spacing: 0.2em; font-weight: 600;
            background: rgba(255,255,255,0.05); color: var(--text-2); margin-bottom: 16px;
        }

        /* Chart Header */
        .chart-header { padding: 32px 32px 0; display: flex; justify-content: space-between; align-items: flex-start; }
        .ch-price { font-family: 'JetBrains Mono', monospace; font-size: 36px; font-weight: 700; letter-spacing: -1px; }
        .ch-range { display: block; font-size: 14px; color: var(--text-3); font-weight: 500; font-family: 'Plus Jakarta Sans'; letter-spacing: 0; margin-top: 4px; }
        .tv-wrapper { height: 600px; width: 100%; margin-top: 16px; }

        /* Stats Grid Inside Bento */
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; padding: 24px; height: 100%; align-content: space-between;}
        .stat-card {
            background: rgba(255,255,255,0.02); border-radius: 1.5rem; padding: 24px;
            border: 1px solid rgba(255,255,255,0.03); transition: all 0.5s var(--bezier);
        }
        .stat-card:hover { transform: translateY(-4px); background: rgba(255,255,255,0.04); }
        .st-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text-3); margin-bottom: 12px; font-weight: 700; }
        .st-value { font-family: 'JetBrains Mono', monospace; font-size: 32px; font-weight: 700; letter-spacing: -1px; }
        
        .c-green { color: var(--accent-green); }
        .c-red { color: var(--accent-red); }
        .c-purple { color: var(--accent-purple); }

        /* Active Position */
        .pos-panel { padding: 32px; }
        .pos-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 32px; }
        .dir-badge {
            padding: 6px 12px; border-radius: 999px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px;
        }
        .dir-long { background: rgba(52,211,153,0.1); color: var(--accent-green); }
        .dir-short { background: rgba(248,113,113,0.1); color: var(--accent-red); }
        
        .pos-table { width: 100%; border-collapse: collapse; text-align: left; }
        .pos-table th { font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text-3); font-weight: 600; padding-bottom: 16px; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .pos-table td { padding: 24px 0 0 0; font-family: 'JetBrains Mono', monospace; font-size: 18px; font-weight: 500; }
        .no-pos { text-align: center; padding: 40px 0; color: var(--text-3); font-size: 14px; letter-spacing: 0.5px;}

        /* Nested CTA Button Architecture */
        .cta-container { display: flex; flex-direction: column; gap: 16px; padding: 24px; }
        .cta-btn {
            display: flex; align-items: center; justify-content: space-between;
            background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
            padding: 8px 8px 8px 24px; border-radius: 999px; text-decoration: none; color: var(--text-1);
            font-size: 14px; font-weight: 600; transition: all 0.6s var(--bezier);
            cursor: pointer;
        }
        .cta-icon-wrapper {
            width: 40px; height: 40px; border-radius: 999px;
            background: rgba(255,255,255,0.1); display: grid; place-items: center;
            transition: all 0.6s var(--bezier);
        }
        .cta-btn:active { transform: scale(0.98); }
        .cta-btn:hover { background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.15); }
        .cta-btn:hover .cta-icon-wrapper { background: #fff; color: #000; transform: scale(1.05) translate(2px, -2px); }

        /* Trade History */
        .history-panel { padding: 32px; max-height: 400px; display: flex; flex-direction: column; }
        .history-content { overflow-y: auto; margin-top: 16px; padding-right: 16px;}
        .history-content::-webkit-scrollbar { width: 4px; }
        .history-content::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
        
        .history-tbl { width: 100%; border-collapse: collapse; }
        .history-tbl th { text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text-3); padding-bottom: 16px; font-weight: 600; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .history-tbl td { padding: 16px 0; border-bottom: 1px solid rgba(255,255,255,0.02); font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--text-2); }
        .pnl-pos { color: var(--accent-green); }
        .pnl-neg { color: var(--accent-red); }

        /* ROI Slider (Minimalist) */
        .roi-panel { padding: 32px; }
        .slider-header { display: flex; justify-content: space-between; margin-bottom: 24px; align-items: baseline;}
        .slider-value { font-family: 'JetBrains Mono', monospace; font-size: 24px; font-weight: 700; color: #fff; }
        input[type=range] { -webkit-appearance: none; width: 100%; background: transparent; margin: 24px 0; }
        input[type=range]:focus { outline: none; }
        input[type=range]::-webkit-slider-runnable-track { width: 100%; height: 2px; background: rgba(255,255,255,0.1); }
        input[type=range]::-webkit-slider-thumb {
            height: 16px; width: 16px; border-radius: 50%; background: #fff; cursor: pointer;
            -webkit-appearance: none; margin-top: -7px; transition: transform 0.3s var(--bezier);
        }
        input[type=range]::-webkit-slider-thumb:hover { transform: scale(1.5); }
        .roi-results { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px;}
        .roi-box { padding: 16px 0; border-top: 1px solid rgba(255,255,255,0.05); }
        .roi-box .rb-month { font-size: 11px; color: var(--text-3); text-transform: uppercase; font-weight: 600; letter-spacing: 1px; margin-bottom: 8px; }
        .roi-box .rb-val { font-family: 'JetBrains Mono', monospace; font-size: 20px; font-weight: 500; }

        /* Mobile Collapse */
        @media (max-width: 1024px) {
            .col-span-8, .col-span-4 { grid-column: span 12; }
            .bento-grid { gap: 16px; margin-bottom: 16px; }
            .app-container { padding: 24px 16px 40px; }
            .chart-header { padding: 24px 24px 0; }
            .tv-wrapper { height: 450px; }
            .pos-table th, .pos-table td { padding: 12px 8px; font-size: 14px; }
        }
    </style>
</head>
<body>
    <div class="bg-orb orb-1"></div>
    <div class="bg-orb orb-2"></div>

    <div class="app-container">
        <div class="top-bar">
            <div class="brand">
                <div class="brand-icon">&#8960;</div>
                <div class="brand-text">ETH Champion<span>Vanguard Build</span></div>
            </div>
            <div class="live-chip"><div class="live-dot"></div>Online</div>
        </div>

        <!-- Row 1: Chart & Core Stats -->
        <div class="bento-grid">
            <!-- Main Chart -->
            <div class="col-span-8 double-bezel">
                <div class="db-inner">
                    <div class="chart-header">
                        <div>
                            <span class="eyebrow">Market Data &bull; 15M</span>
                            <div class="ch-price">${last_price}</div>
                        </div>
                        <div style="text-align: right;">
                            <span class="eyebrow" style="background: transparent; margin:0;">24H Range</span>
                            <span class="ch-range">${last_range}</span>
                        </div>
                    </div>
                    <div class="tv-wrapper">
                        <div class="tradingview-widget-container" style="height: 100%; width: 100%">
                            <div id="tradingview_12345" style="height: 100%; width: 100%"></div>
                            <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
                            <script type="text/javascript">
                            new TradingView.widget(
                            {
                                "autosize": true,
                                "symbol": "BINANCE:ETHUSDT",
                                "interval": "15",
                                "timezone": "Etc/UTC",
                                "theme": "dark",
                                "style": "1",
                                "locale": "en",
                                "enable_publishing": false,
                                "backgroundColor": "rgba(0,0,0,0)",
                                "gridColor": "rgba(255,255,255,0.02)",
                                "hide_top_toolbar": true,
                                "hide_legend": true,
                                "save_image": false,
                                "studies": ["MAExp@tv-basicstudies", "Volume@tv-basicstudies"],
                                "container_id": "tradingview_12345"
                            }
                            );
                            </script>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Stats -->
            <div class="col-span-4 double-bezel">
                <div class="db-inner">
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="st-label">Wallet</div>
                            <div class="st-value">${wallet_balance}</div>
                        </div>
                        <div class="stat-card">
                            <div class="st-label">Total PnL</div>
                            <div class="st-value {pnl_color}">{total_pnl}%</div>
                        </div>
                        <div class="stat-card">
                            <div class="st-label">Win Rate</div>
                            <div class="st-value c-purple">{win_rate}%</div>
                        </div>
                        <div class="stat-card">
                            <div class="st-label">Trades</div>
                            <div class="st-value">{total_trades}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Row 2: Active Position Full Width -->
        <div class="bento-grid">
            <div class="col-span-12 double-bezel">
                <div class="db-inner pos-panel">
                    <div class="pos-header">
                        <span class="eyebrow" style="margin:0;">Active Position</span>
                        {dir_badge_html}
                    </div>
                    <div style="overflow-x: auto;">
                        {active_position_html}
                    </div>
                </div>
            </div>
        </div>

        <!-- Row 3: History, ROI, Actions -->
        <div class="bento-grid">
            <!-- History -->
            <div class="col-span-4 double-bezel">
                <div class="db-inner history-panel">
                    <span class="eyebrow">Recent Trade Log</span>
                    <div class="history-content">
                        {trade_history_html}
                    </div>
                </div>
            </div>

            <!-- ROI Tool -->
            <div class="col-span-4 double-bezel">
                <div class="db-inner roi-panel">
                    <span class="eyebrow">ROI Projection Tool</span>
                    <div class="slider-header">
                        <span style="font-size: 13px; color: var(--text-2); font-weight: 500;">Expected Monthly Yield</span>
                        <span class="slider-value" id="yield-val">10%</span>
                    </div>
                    <input type="range" id="yield-slider" min="1" max="30" value="10">
                    <div class="roi-results">
                        <div class="roi-box">
                            <div class="rb-month">1 Month</div>
                            <div class="rb-val" id="roi-1m">--</div>
                        </div>
                        <div class="roi-box">
                            <div class="rb-month">3 Months</div>
                            <div class="rb-val" id="roi-3m">--</div>
                        </div>
                        <div class="roi-box">
                            <div class="rb-month">6 Months</div>
                            <div class="rb-val" id="roi-6m">--</div>
                        </div>
                        <div class="roi-box">
                            <div class="rb-month">1 Year</div>
                            <div class="rb-val" id="roi-12m">--</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- CTAs -->
            <div class="col-span-4 double-bezel">
                <div class="db-inner cta-container" style="justify-content: center;">
                    <span class="eyebrow" style="margin-bottom: 24px;">External Links</span>
                    <a href="{ledger_url}" target="_blank" class="cta-btn">
                        <span>Google Sheets Ledger</span>
                        <div class="cta-icon-wrapper">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>
                        </div>
                    </a>
                    <a href="https://dashboard.render.com/web/srv-d85g27svikkc739sjrtg" target="_blank" class="cta-btn">
                        <span>Render Console</span>
                        <div class="cta-icon-wrapper">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>
                        </div>
                    </a>
                </div>
            </div>
        </div>

    </div>
    
    <!-- Client-side ROI Logic -->
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const currentWallet = {wallet_balance_raw};
            const slider = document.getElementById('yield-slider');
            const yieldVal = document.getElementById('yield-val');
            
            const r1m = document.getElementById('roi-1m');
            const r3m = document.getElementById('roi-3m');
            const r6m = document.getElementById('roi-6m');
            const r12m = document.getElementById('roi-12m');

            const formatter = new Intl.NumberFormat('en-US', {
                style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0
            });

            function updateProjections() {
                const rate = parseFloat(slider.value) / 100;
                yieldVal.textContent = slider.value + '%';
                r1m.textContent = formatter.format(currentWallet * Math.pow(1 + rate, 1));
                r3m.textContent = formatter.format(currentWallet * Math.pow(1 + rate, 3));
                r6m.textContent = formatter.format(currentWallet * Math.pow(1 + rate, 6));
                r12m.textContent = formatter.format(currentWallet * Math.pow(1 + rate, 12));
            }

            slider.addEventListener('input', updateProjections);
            updateProjections(); // Init
            
            // Subtle scroll reveal
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity = 1;
                        entry.target.style.transform = 'translateY(0)';
                    }
                });
            }, { threshold: 0.1 });
            
            document.querySelectorAll('.double-bezel').forEach((el, i) => {
                el.style.opacity = 0;
                el.style.transform = 'translateY(20px)';
                el.style.transition = `all 0.8s cubic-bezier(0.32, 0.72, 0, 1) ${i * 0.1}s`;
                observer.observe(el);
            });
        });
    </script>
</body>
</html>
"""

# Extremely lightweight healthcheck server to satisfy Render's free web_service requirements
class HealthCheckHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            
            # Read state.json on the fly to render completely live statistics
            state = {
                'balance': 1000.0, 'initial_balance': 1000.0,
                'active_trade': None, 'dry_run': True,
                'total_trades': 0, 'wins': 0, 'losses': 0,
                'trade_history': [], 'last_price': 0.0, 'last_range': 0.0,
                'last_heartbeat': 'N/A'
            }
            ledger_url = os.environ.get('GOOGLE_DOC_URL') or "https://docs.google.com"
            
            loaded_from_disk = False
            if os.path.exists('state.json'):
                try:
                    with open('state.json', 'r') as f:
                        loaded = json.load(f)
                        state.update(loaded)
                        ledger_url = os.environ.get('GOOGLE_DOC_URL') or state.get('google_doc_url', ledger_url)
                        loaded_from_disk = True
                except:
                    pass

            # If local state looks like a fresh default, try remote store as backup
            if not loaded_from_disk or state.get('total_trades', 0) == 0:
                try:
                    import requests as req
                    remote_r = req.get("https://jsonblob.com/api/jsonBlob/019e4ab4-ae75-7654-997d-b83abbee7f26", timeout=5)
                    if remote_r.status_code == 200 and remote_r.text.strip():
                        remote = remote_r.json()
                        # Only use remote if it has more data than local
                        if remote.get('total_trades', 0) >= state.get('total_trades', 0):
                            state.update(remote)
                            ledger_url = os.environ.get('GOOGLE_DOC_URL') or state.get('google_doc_url', ledger_url)
                except:
                    pass

            balance = state['balance']
            initial = state.get('initial_balance', 1000.0)
            total_pnl = ((balance - initial) / initial) * 100
            total_trades = state.get('total_trades', 0)
            wins = state.get('wins', 0)
            losses = state.get('losses', 0)
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
            pnl_color = "c-green" if total_pnl >= 0 else "c-red"
            trade_mode = "DRY RUN" if state.get('dry_run', True) else "LIVE"
            
            last_price = state.get('last_price', 0.0)
            last_range = state.get('last_range', 0.0)
            
            # Format heartbeat
            raw_hb = state.get('last_heartbeat', '')
            if raw_hb:
                try:
                    from datetime import datetime as dt
                    hb_dt = dt.fromisoformat(raw_hb)
                    last_hb_str = hb_dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                except:
                    last_hb_str = raw_hb
            else:
                last_hb_str = 'Awaiting first candle...'

            # Active position HTML
            active_trade = state.get('active_trade')
            if active_trade:
                d = active_trade['direction']
                dir_cls = "dir-long" if d == 'Long' else "dir-short"
                dir_badge = f'<span class="dir-badge {dir_cls}" style="margin:0; font-size:10px;">{d.upper()}</span>'
                
                margin = balance * 0.10
                size = margin / active_trade["entry_price"]
                
                if d == 'Long':
                    unrealized_pnl = ((last_price - active_trade["entry_price"]) / active_trade["entry_price"]) * 100
                else:
                    unrealized_pnl = ((active_trade["entry_price"] - last_price) / active_trade["entry_price"]) * 100
                    
                upnl_cls = "pnl-pos" if unrealized_pnl >= 0 else "pnl-neg"
                upnl_sign = "+" if unrealized_pnl >= 0 else ""
                
                pos_html = f'''<table class="history-tbl" style="margin: 0; min-width: 800px;">
                    <thead><tr><th>Symbol</th><th>Size</th><th>Entry Price</th><th>Mark Price</th><th>Margin</th><th>Stop Loss</th><th>Take Profit</th><th>Unrealized PnL</th></tr></thead>
                    <tbody>
                        <tr>
                            <td><strong>ETH/USDT</strong></td>
                            <td>{size:.4f} ETH</td>
                            <td>${active_trade["entry_price"]:.2f}</td>
                            <td>${last_price:.2f}</td>
                            <td>${margin:.2f}</td>
                            <td style="color:var(--accent-red)">${active_trade["sl_price"]:.2f}</td>
                            <td style="color:var(--accent-green)">${active_trade["tp_price"]:.2f}</td>
                            <td class="{upnl_cls}">{upnl_sign}{unrealized_pnl:.2f}%</td>
                        </tr>
                    </tbody>
                </table>'''
            else:
                dir_badge = '<span style="font-size:11px;color:var(--text-3);">IDLE</span>'
                pos_html = '<div class="no-pos" style="padding: 32px; text-align: center;"><span class="scan-icon" style="margin-right:8px;">&#128225;</span>Scanning for breakout signals...</div>'

            # Trade history table
            history = state.get('trade_history', [])
            if history:
                rows = ""
                for t in reversed(history):
                    pnl_cls = "pnl-pos" if t['pnl'] > 0 else "pnl-neg"
                    res_cls = "res-tp" if t['result'] == 'TP' else "res-sl"
                    pnl_sign = "+" if t['pnl'] > 0 else ""
                    rows += f'<tr><td>{t["time"]}</td><td>{t["dir"]}</td><td>${t["entry"]:.2f}</td><td>${t["exit"]:.2f}</td><td class="{pnl_cls}">{pnl_sign}{t["pnl"]:.2f}%</td><td><span class="{res_cls}">{t["result"]}</span></td></tr>'
                trade_history_html = f'''<table class="history-tbl">
                    <thead><tr><th>Time</th><th>Dir</th><th>Entry</th><th>Exit</th><th>PnL</th><th>Result</th></tr></thead>
                    <tbody>{rows}</tbody></table>'''
            else:
                trade_history_html = '<div class="no-pos" style="padding:16px 0;">No closed trades yet. History will appear here.</div>'

            # Render the page with safe .replace
            html = DASHBOARD_HTML
            replacements = {
                "{last_price}": f"{last_price:.2f}",
                "{last_range}": f"{last_range:.2f}",
                "{wallet_balance}": f"{balance:.2f}",
                "{wallet_balance_raw}": f"{balance}",
                "{total_pnl}": f"{total_pnl:+.2f}",
                "{pnl_color}": pnl_color,
                "{win_rate}": f"{win_rate:.0f}",
                "{total_trades}": str(total_trades),
                "{wins}": str(wins),
                "{losses}": str(losses),
                "{dir_badge_html}": dir_badge,
                "{active_position_html}": pos_html,
                "{trade_history_html}": trade_history_html,
                "{ledger_url}": ledger_url,
                "{trade_mode}": trade_mode,
                "{last_heartbeat}": last_hb_str,
            }
            for key, val in replacements.items():
                html = html.replace(key, val)
            
            self.wfile.write(html.encode('utf-8'))
        elif self.path == '/api/state':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            state = {}
            if os.path.exists('state.json'):
                try:
                    with open('state.json', 'r') as f:
                        state = json.load(f)
                except:
                    pass
            self.wfile.write(json.dumps(state, indent=2).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            
    def log_message(self, format, *args):
        return

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"Healthcheck HTTP server running on port {port}...")
    server.serve_forever()

def main():
    print("==========================================================================")
    print("                 ETH/USDT 15M CHAMPION LIVE TRADING BOT                   ")
    print("==========================================================================")
    
    executor = SingleStrategyExecutor(
        symbol='ETH/USDT',
        timeframe='15m',
        dry_run=True
    )
    
    print("Starting trading execution engine thread...")
    bot_thread = threading.Thread(target=executor.start_loop, daemon=True)
    bot_thread.start()
    
    try:
        run_health_server()
    except KeyboardInterrupt:
        print("\nExecution stopped safely. Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
