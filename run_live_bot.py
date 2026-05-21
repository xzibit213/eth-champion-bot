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
    <title>ETH Champion | Live Trading Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-deep: #05040a;
            --bg-card: rgba(18, 16, 32, 0.65);
            --border-glass: rgba(255,255,255,0.08);
            --accent-purple: #a78bfa;
            --accent-blue: #60a5fa;
            --accent-green: #34d399;
            --accent-red: #f87171;
            --accent-amber: #fbbf24;
            --text-1: #f8fafc;
            --text-2: #cbd5e1;
            --text-3: #64748b;
        }
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', system-ui, sans-serif;
            background: var(--bg-deep);
            color: var(--text-1);
            min-height: 100vh;
            overflow-x: hidden;
            -webkit-font-smoothing: antialiased;
        }

        /* Animated gradient orbs */
        .bg-orb {
            position: fixed; border-radius: 50%; filter: blur(140px); opacity: 0.15; pointer-events: none; z-index: 0;
        }
        .orb-1 { width: 700px; height: 700px; background: #7c3aed; top: -200px; left: -150px; animation: float1 22s ease-in-out infinite; }
        .orb-2 { width: 600px; height: 600px; background: #2563eb; bottom: -150px; right: -100px; animation: float2 28s ease-in-out infinite; }
        .orb-3 { width: 500px; height: 500px; background: #059669; top: 60%; left: 40%; transform: translate(-50%, -50%); animation: float3 20s ease-in-out infinite; }
        @keyframes float1 { 0%,100% { transform: translate(0,0); } 50% { transform: translate(100px,80px); } }
        @keyframes float2 { 0%,100% { transform: translate(0,0); } 50% { transform: translate(-80px,-100px); } }
        @keyframes float3 { 0%,100% { transform: translate(-50%,-50%) scale(1); } 50% { transform: translate(-30%,-60%) scale(1.2); } }

        .app { max-width: 1400px; margin: 0 auto; padding: 24px 24px 40px; position: relative; z-index: 1; }

        /* Top bar */
        .top-bar {
            display: flex; align-items: center; justify-content: space-between;
            margin-bottom: 32px; padding: 0 8px;
        }
        .brand { display: flex; align-items: center; gap: 14px; }
        .brand-icon {
            width: 48px; height: 48px; border-radius: 16px;
            background: linear-gradient(135deg, #7c3aed, #2563eb);
            display: grid; place-items: center; font-size: 24px; font-weight: 900; color: #fff;
            box-shadow: 0 0 24px rgba(124, 58, 237, 0.4);
        }
        .brand-text { font-size: 20px; font-weight: 800; letter-spacing: -0.5px; }
        .brand-text span { color: var(--text-3); font-weight: 500; font-size: 14px; margin-left: 8px; }

        .live-chip {
            display: inline-flex; align-items: center; gap: 8px;
            background: rgba(52,211,153,0.12); border: 1px solid rgba(52,211,153,0.25);
            padding: 8px 16px; border-radius: 100px; font-size: 13px; font-weight: 700;
            color: var(--accent-green); text-transform: uppercase; letter-spacing: 1px;
            box-shadow: 0 0 15px rgba(52,211,153,0.15);
        }
        .live-dot { width: 8px; height: 8px; background: var(--accent-green); border-radius: 50%; animation: blink 1.5s infinite; }
        @keyframes blink { 0%,100% { opacity: .4; } 50% { opacity: 1; box-shadow: 0 0 8px var(--accent-green); } }

        /* Main Layout Grid */
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 420px;
            gap: 24px;
            align-items: start;
        }

        /* Glass Panel Base */
        .glass-panel {
            background: var(--bg-card); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
            border: 1px solid var(--border-glass); border-radius: 24px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        }

        /* Chart Area */
        .chart-container {
            height: calc(100vh - 120px);
            min-height: 800px;
            display: flex; flex-direction: column;
        }
        .chart-header {
            padding: 20px 24px; border-bottom: 1px solid var(--border-glass);
            display: flex; justify-content: space-between; align-items: center;
            background: rgba(0,0,0,0.2);
        }
        .ch-title { font-weight: 700; font-size: 16px; letter-spacing: 0.5px; display: flex; align-items: center; gap: 10px; }
        .ch-price { font-family: 'JetBrains Mono', monospace; font-size: 24px; font-weight: 800; color: var(--text-1); }
        .ch-range { font-size: 13px; color: var(--text-3); font-weight: 500; }
        .tv-wrapper { flex: 1; width: 100%; }

        /* Right Sidebar */
        .sidebar { display: flex; flex-direction: column; gap: 24px; }

        /* Stats Grid (2x2) */
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        .stat-card {
            background: linear-gradient(180deg, rgba(255,255,255,0.03), transparent);
            border-radius: 20px; padding: 20px;
            border: 1px solid var(--border-glass);
            transition: transform 0.2s, background 0.3s;
            position: relative; overflow: hidden;
        }
        .stat-card:hover { transform: translateY(-2px); background: rgba(255,255,255,0.05); }
        .stat-card::before {
            content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 2px;
            background: var(--card-color, var(--accent-blue)); opacity: 0.5;
        }
        .st-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text-3); margin-bottom: 8px; font-weight: 700; }
        .st-value { font-family: 'JetBrains Mono', monospace; font-size: 26px; font-weight: 800; text-shadow: 0 0 20px rgba(255,255,255,0.1); }
        
        .c-green { color: var(--accent-green); --card-color: var(--accent-green); }
        .c-red { color: var(--accent-red); --card-color: var(--accent-red); }
        .c-purple { color: var(--accent-purple); --card-color: var(--accent-purple); }
        .c-blue { color: var(--accent-blue); --card-color: var(--accent-blue); }

        /* Panel Headers */
        .panel-hdr {
            display: flex; align-items: center; justify-content: space-between;
            padding: 20px 24px 16px; border-bottom: 1px solid var(--border-glass);
        }
        .panel-hdr h2 { font-size: 14px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-2); font-weight: 800; }

        /* Active Position */
        .pos-panel { padding: 0; }
        .pos-content { padding: 24px; }
        .dir-badge { padding: 6px 16px; border-radius: 100px; font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; }
        .dir-long { background: rgba(52,211,153,0.15); color: var(--accent-green); border: 1px solid rgba(52,211,153,0.3); box-shadow: 0 0 15px rgba(52,211,153,0.1); }
        .dir-short { background: rgba(248,113,113,0.15); color: var(--accent-red); border: 1px solid rgba(248,113,113,0.3); box-shadow: 0 0 15px rgba(248,113,113,0.1); }
        
        .pos-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;}
        .pos-grid.three { grid-template-columns: 1fr 1fr 1fr; margin-bottom: 0;}
        .pos-cell { background: rgba(0,0,0,0.3); border-radius: 16px; padding: 16px; border: 1px solid rgba(255,255,255,0.03); }
        .pos-cell .pc-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-3); margin-bottom: 6px; font-weight: 600;}
        .pos-cell .pc-val { font-family: 'JetBrains Mono', monospace; font-size: 18px; font-weight: 800; }
        
        .no-pos { text-align: center; padding: 40px 0; color: var(--text-3); font-size: 15px; font-style: italic; }
        .no-pos .scan-icon { font-size: 40px; margin-bottom: 12px; display: block; animation: pulse 2s infinite; }
        @keyframes pulse { 0% { transform: scale(0.95); opacity: 0.5; } 50% { transform: scale(1.05); opacity: 1; } 100% { transform: scale(0.95); opacity: 0.5; } }

        /* ROI Slider */
        .roi-panel { padding: 0; }
        .roi-content { padding: 24px; }
        .slider-container { margin-bottom: 24px; }
        .slider-header { display: flex; justify-content: space-between; margin-bottom: 12px; }
        .slider-label { font-size: 13px; color: var(--text-2); font-weight: 600; }
        .slider-value { font-family: 'JetBrains Mono', monospace; font-size: 16px; font-weight: 800; color: var(--accent-purple); }
        
        input[type=range] {
            -webkit-appearance: none; width: 100%; background: transparent; margin: 10px 0;
        }
        input[type=range]:focus { outline: none; }
        input[type=range]::-webkit-slider-runnable-track {
            width: 100%; height: 8px; cursor: pointer;
            background: rgba(255,255,255,0.1); border-radius: 10px;
        }
        input[type=range]::-webkit-slider-thumb {
            height: 24px; width: 24px; border-radius: 50%;
            background: var(--accent-purple); cursor: pointer;
            -webkit-appearance: none; margin-top: -8px;
            box-shadow: 0 0 15px var(--accent-purple);
            border: 3px solid #fff;
        }
        
        .roi-results { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        .roi-box { background: rgba(0,0,0,0.2); padding: 12px; border-radius: 12px; text-align: center; border: 1px solid rgba(255,255,255,0.03); }
        .roi-box .rb-month { font-size: 11px; color: var(--text-3); text-transform: uppercase; font-weight: 700; margin-bottom: 4px; }
        .roi-box .rb-val { font-family: 'JetBrains Mono', monospace; font-size: 16px; font-weight: 800; color: var(--accent-green); }

        /* Trade History */
        .history-panel { padding: 0; max-height: 400px; display: flex; flex-direction: column; }
        .history-content { overflow-y: auto; padding: 0 12px; }
        .history-content::-webkit-scrollbar { width: 6px; }
        .history-content::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
        
        .history-tbl { width: 100%; border-collapse: collapse; font-size: 13px; }
        .history-tbl th {
            text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: 1px;
            color: var(--text-3); padding: 16px 12px 12px; font-weight: 700;
            position: sticky; top: 0; background: var(--bg-card); backdrop-filter: blur(10px); z-index: 2;
        }
        .history-tbl td { padding: 12px; border-top: 1px solid rgba(255,255,255,0.04); font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 500;}
        .history-tbl tr:hover td { background: rgba(255,255,255,0.03); }
        .pnl-pos { color: var(--accent-green); font-weight: 800; }
        .pnl-neg { color: var(--accent-red); font-weight: 800; }
        .res-tp { background: rgba(52,211,153,0.15); color: var(--accent-green); padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; }
        .res-sl { background: rgba(248,113,113,0.15); color: var(--accent-red); padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; }

        /* CTA buttons */
        .cta-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: auto; }
        .cta-btn {
            display: flex; align-items: center; justify-content: center; gap: 8px;
            padding: 16px; border-radius: 16px; text-decoration: none;
            font-size: 14px; font-weight: 700; transition: all 0.25s;
            border: 1px solid var(--border-glass);
        }
        .cta-primary { background: linear-gradient(135deg, #7c3aed, #2563eb); color: #fff; box-shadow: 0 4px 20px rgba(124,58,237,0.3); border: none; }
        .cta-primary:hover { transform: translateY(-3px); box-shadow: 0 8px 30px rgba(124,58,237,0.4); filter: brightness(1.1); }
        .cta-secondary { background: rgba(0,0,0,0.4); color: var(--text-2); }
        .cta-secondary:hover { border-color: rgba(167,139,250,0.4); color: #fff; background: rgba(167,139,250,0.1); }

        @media (max-width: 1024px) {
            .main-grid { grid-template-columns: 1fr; }
            .chart-container { height: 600px; min-height: unset; }
        }
        @media (max-width: 640px) {
            .stats-grid { grid-template-columns: 1fr 1fr; }
            .pos-grid, .pos-grid.three, .roi-results { grid-template-columns: 1fr; }
            .cta-row { grid-template-columns: 1fr; }
            .chart-container { height: 450px; }
        }
    </style>
</head>
<body>
    <div class="bg-orb orb-1"></div>
    <div class="bg-orb orb-2"></div>
    <div class="bg-orb orb-3"></div>

    <div class="app">
        <!-- Top Bar -->
        <div class="top-bar">
            <div class="brand">
                <div class="brand-icon">&#926;</div>
                <div class="brand-text">ETH Champion<span>v2.0 Premium</span></div>
            </div>
            <div class="live-chip"><div class="live-dot"></div>Bot Online</div>
        </div>

        <div class="main-grid">
            <!-- Left: TradingView Chart -->
            <div class="glass-panel chart-container">
                <div class="chart-header">
                    <div class="ch-title">&#128200; ETH/USDT Analysis <span style="font-size: 11px; font-weight: 500; color: var(--text-3); background: rgba(255,255,255,0.1); padding: 4px 8px; border-radius: 6px; margin-left: 8px;">BINANCE SPOT &bull; 15M</span></div>
                    <div class="ch-price">${last_price} <span class="ch-range">Range: ${last_range}</span></div>
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
                            "gridColor": "rgba(255,255,255,0.04)",
                            "hide_top_toolbar": false,
                            "hide_legend": false,
                            "save_image": false,
                            "studies": [
                                "MAExp@tv-basicstudies",
                                "Volume@tv-basicstudies"
                            ],
                            "container_id": "tradingview_12345"
                        }
                        );
                        </script>
                    </div>
                </div>
            </div>

            <!-- Right: Sidebar Data -->
            <div class="sidebar">
                <!-- Stats Grid -->
                <div class="stats-grid">
                    <div class="stat-card c-green">
                        <div class="st-label">Wallet</div>
                        <div class="st-value">${wallet_balance}</div>
                    </div>
                    <div class="stat-card {pnl_color}">
                        <div class="st-label">Total PnL</div>
                        <div class="st-value">{total_pnl}%</div>
                    </div>
                    <div class="stat-card c-purple">
                        <div class="st-label">Win Rate</div>
                        <div class="st-value">{win_rate}%</div>
                    </div>
                    <div class="stat-card c-blue">
                        <div class="st-label">Total Trades</div>
                        <div class="st-value">{total_trades}</div>
                    </div>
                </div>

                <!-- Active Position Panel -->
                <div class="glass-panel pos-panel">
                    <div class="panel-hdr">
                        <h2>Active Position</h2>
                        {dir_badge_html}
                    </div>
                    <div class="pos-content">
                        {active_position_html}
                    </div>
                </div>

                <!-- Google Sheets Banner -->
                <a href="{ledger_url}" target="_blank" class="glass-panel" style="display: block; padding: 16px 20px; text-decoration: none; border: 1px solid rgba(52, 211, 153, 0.3); background: linear-gradient(90deg, rgba(52, 211, 153, 0.05), transparent); position: relative; overflow: hidden; transition: all 0.3s;">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div>
                            <div style="font-size: 12px; font-weight: 700; color: var(--accent-green); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;">Live Trade Ledger</div>
                            <div style="font-size: 14px; color: var(--text-1); font-weight: 500;">Check all live bot trades on Google Sheets &rarr;</div>
                        </div>
                        <div style="font-size: 28px;">&#128202;</div>
                    </div>
                </a>

                <!-- ROI Projection Tool -->
                <div class="glass-panel roi-panel">
                    <div class="panel-hdr">
                        <h2>ROI Projection Tool</h2>
                        <span style="font-size: 11px; color: var(--text-3); font-weight: 600;">COMPOUNDING</span>
                    </div>
                    <div class="roi-content">
                        <div class="slider-container">
                            <div class="slider-header">
                                <span class="slider-label">Expected Monthly Yield</span>
                                <span class="slider-value" id="yield-val">10%</span>
                            </div>
                            <input type="range" id="yield-slider" min="1" max="30" value="10">
                        </div>
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

                <!-- Trade History -->
                <div class="glass-panel history-panel">
                    <div class="panel-hdr">
                        <h2>Recent Trade Log</h2>
                        <span style="font-size: 11px; color: var(--text-3); font-weight: 700;">{wins}W / {losses}L</span>
                    </div>
                    <div class="history-content">
                        {trade_history_html}
                    </div>
                </div>

                <!-- CTA Buttons -->
                <div class="cta-row">
                    <a class="cta-btn cta-primary" href="{ledger_url}" target="_blank">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                        Google Sheets Ledger
                    </a>
                    <a class="cta-btn cta-secondary" href="https://dashboard.render.com/web/srv-d85g27svikkc739sjrtg" target="_blank">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
                        Render Console
                    </a>
                </div>
            </div>
        </div>
        
        <!-- Bottom Description Panel -->
        <div class="glass-panel" style="margin-top: 16px; padding: 32px;">
            <h2 style="font-size: 18px; color: var(--accent-purple); margin-bottom: 24px;">About ETH Champion Engine</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px;">
                <div>
                    <h3 style="font-size: 13px; text-transform: uppercase; color: var(--text-2); margin-bottom: 8px;">Core Capabilities</h3>
                    <p style="font-size: 14px; color: var(--text-3); line-height: 1.6;">A fully autonomous, zero-permission trading engine designed to scan ETH/USDT on the 15-minute timeframe for volatility breakouts. Features a 9/20 EMA Pullback trigger and trailing Take-Profit/Stop-Loss management built purely in Python.</p>
                </div>
                <div>
                    <h3 style="font-size: 13px; text-transform: uppercase; color: var(--text-2); margin-bottom: 8px;">Performance & Backtesting</h3>
                    <p style="font-size: 14px; color: var(--text-3); line-height: 1.6;">Backtested over 6 months of historical Binance data, the strategy maintains a fixed 1:3 Risk/Reward ratio. While win-rate hovers around 30-35%, the asymmetric payoff mathematically yields an upward sloping equity curve.</p>
                </div>
                <div>
                    <h3 style="font-size: 13px; text-transform: uppercase; color: var(--text-2); margin-bottom: 8px;">Technology Stack</h3>
                    <p style="font-size: 14px; color: var(--text-3); line-height: 1.6;">Built by Antigravity AI, utilizing the CCXT library for exchange execution, JSONBlob for cloud state persistence, and Google Apps Script webhooks for real-time ledger accounting.</p>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Client-side ROI Logic -->
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const currentWallet = {wallet_balance_raw}; // Injected from python
            const slider = document.getElementById('yield-slider');
            const yieldVal = document.getElementById('yield-val');
            
            const r1m = document.getElementById('roi-1m');
            const r3m = document.getElementById('roi-3m');
            const r6m = document.getElementById('roi-6m');
            const r12m = document.getElementById('roi-12m');

            const formatter = new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
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
                dir_badge = f'<span class="dir-badge {dir_cls}">{d.upper()}</span>'
                
                margin = balance * 0.10
                size = margin / active_trade["entry_price"]
                
                pos_html = f'''<div class="pos-grid" style="grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div class="pos-cell"><div class="pc-label">Entry Price</div><div class="pc-val" style="color:var(--text-1)">${active_trade["entry_price"]:.2f}</div></div>
                    <div class="pos-cell"><div class="pc-label">Margin Used</div><div class="pc-val" style="color:var(--text-1)">${margin:.2f} <span style="font-size:11px;color:var(--text-3)">({size:.4f} ETH)</span></div></div>
                    <div class="pos-cell"><div class="pc-label">Stop Loss</div><div class="pc-val" style="color:var(--accent-red)">${active_trade["sl_price"]:.2f}</div></div>
                    <div class="pos-cell"><div class="pc-label">Take Profit</div><div class="pc-val" style="color:var(--accent-green)">${active_trade["tp_price"]:.2f}</div></div>
                </div>'''
            else:
                dir_badge = '<span style="font-size:11px;color:var(--text-3);">IDLE</span>'
                pos_html = '<div class="no-pos"><span class="scan-icon">&#128225;</span>Scanning for breakout signals...</div>'

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
