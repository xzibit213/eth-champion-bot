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
    <meta http-equiv="refresh" content="60">
    <title>ETH Champion Bot — Live Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-deep: #07060e;
            --bg-card: rgba(15, 13, 28, 0.7);
            --border-glass: rgba(255,255,255,0.06);
            --accent-purple: #a78bfa;
            --accent-blue: #60a5fa;
            --accent-green: #34d399;
            --accent-red: #f87171;
            --accent-pink: #f472b6;
            --accent-amber: #fbbf24;
            --text-1: #f1f5f9;
            --text-2: #94a3b8;
            --text-3: #64748b;
        }
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', system-ui, sans-serif;
            background: var(--bg-deep);
            color: var(--text-1);
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* Animated gradient orbs */
        .bg-orb {
            position: fixed; border-radius: 50%; filter: blur(120px); opacity: 0.12; pointer-events: none; z-index: 0;
        }
        .orb-1 { width: 600px; height: 600px; background: #7c3aed; top: -150px; left: -100px; animation: float1 20s ease-in-out infinite; }
        .orb-2 { width: 500px; height: 500px; background: #2563eb; bottom: -100px; right: -80px; animation: float2 25s ease-in-out infinite; }
        .orb-3 { width: 400px; height: 400px; background: #ec4899; top: 50%; left: 50%; transform: translate(-50%, -50%); animation: float3 18s ease-in-out infinite; }
        @keyframes float1 { 0%,100% { transform: translate(0,0); } 50% { transform: translate(80px,60px); } }
        @keyframes float2 { 0%,100% { transform: translate(0,0); } 50% { transform: translate(-60px,-80px); } }
        @keyframes float3 { 0%,100% { transform: translate(-50%,-50%) scale(1); } 50% { transform: translate(-40%,-40%) scale(1.15); } }

        .app { max-width: 880px; margin: 0 auto; padding: 24px 16px 40px; position: relative; z-index: 1; }

        /* Top bar */
        .top-bar {
            display: flex; align-items: center; justify-content: space-between;
            margin-bottom: 28px; padding: 0 4px;
        }
        .brand { display: flex; align-items: center; gap: 12px; }
        .brand-icon {
            width: 44px; height: 44px; border-radius: 14px;
            background: linear-gradient(135deg, #7c3aed, #2563eb);
            display: grid; place-items: center; font-size: 22px; font-weight: 800; color: #fff;
            box-shadow: 0 0 20px rgba(124, 58, 237, 0.3);
        }
        .brand-text { font-size: 18px; font-weight: 700; letter-spacing: -0.3px; }
        .brand-text span { color: var(--text-3); font-weight: 400; font-size: 13px; margin-left: 6px; }

        .live-chip {
            display: inline-flex; align-items: center; gap: 6px;
            background: rgba(52,211,153,0.1); border: 1px solid rgba(52,211,153,0.2);
            padding: 6px 14px; border-radius: 100px; font-size: 12px; font-weight: 600;
            color: var(--accent-green); text-transform: uppercase; letter-spacing: 0.8px;
        }
        .live-dot { width: 7px; height: 7px; background: var(--accent-green); border-radius: 50%; animation: blink 1.4s infinite; }
        @keyframes blink { 0%,100% { opacity: .5; } 50% { opacity: 1; } }

        /* Price hero */
        .price-hero {
            background: var(--bg-card); backdrop-filter: blur(20px);
            border: 1px solid var(--border-glass); border-radius: 20px;
            padding: 28px 32px; margin-bottom: 20px;
            display: flex; align-items: center; justify-content: space-between;
            position: relative; overflow: hidden;
        }
        .price-hero::after {
            content: ''; position: absolute; top: 0; right: 0; width: 200px; height: 100%;
            background: linear-gradient(135deg, rgba(124,58,237,0.08), rgba(37,99,235,0.06));
            border-radius: 0 20px 20px 0;
        }
        .price-left .price-label { font-size: 13px; color: var(--text-3); margin-bottom: 4px; font-weight: 500; }
        .price-left .price-value {
            font-family: 'JetBrains Mono', monospace; font-size: 38px; font-weight: 800;
            background: linear-gradient(135deg, #fff 40%, var(--accent-purple));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .price-left .price-pair { font-size: 13px; color: var(--text-2); margin-top: 4px; }
        .price-right { text-align: right; z-index: 1; }
        .price-right .range-label { font-size: 11px; color: var(--text-3); text-transform: uppercase; letter-spacing: 1px; }
        .price-right .range-val { font-family: 'JetBrains Mono', monospace; font-size: 22px; font-weight: 700; color: var(--accent-amber); }
        .price-right .range-note { font-size: 11px; color: var(--text-3); margin-top: 2px; }

        /* Stats grid */
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 20px; }
        .stat-tile {
            background: var(--bg-card); backdrop-filter: blur(16px);
            border: 1px solid var(--border-glass); border-radius: 16px;
            padding: 18px 16px; text-align: center; transition: transform 0.2s, border-color 0.2s;
        }
        .stat-tile:hover { transform: translateY(-2px); border-color: rgba(167,139,250,0.2); }
        .stat-tile .st-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1.2px; color: var(--text-3); margin-bottom: 6px; font-weight: 600; }
        .stat-tile .st-value { font-family: 'JetBrains Mono', monospace; font-size: 20px; font-weight: 800; }
        .c-green { color: var(--accent-green); }
        .c-red { color: var(--accent-red); }
        .c-purple { color: var(--accent-purple); }
        .c-blue { color: var(--accent-blue); }
        .c-amber { color: var(--accent-amber); }

        /* Position panel */
        .panel {
            background: var(--bg-card); backdrop-filter: blur(16px);
            border: 1px solid var(--border-glass); border-radius: 20px;
            padding: 24px 28px; margin-bottom: 20px;
        }
        .panel-hdr {
            display: flex; align-items: center; justify-content: space-between;
            margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid var(--border-glass);
        }
        .panel-hdr h2 { font-size: 14px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-2); font-weight: 700; }
        .dir-badge {
            padding: 4px 14px; border-radius: 100px; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
        }
        .dir-long { background: rgba(52,211,153,0.12); color: var(--accent-green); border: 1px solid rgba(52,211,153,0.2); }
        .dir-short { background: rgba(248,113,113,0.12); color: var(--accent-red); border: 1px solid rgba(248,113,113,0.2); }

        .pos-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
        .pos-cell { background: rgba(0,0,0,0.25); border-radius: 12px; padding: 14px; }
        .pos-cell .pc-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-3); margin-bottom: 4px; }
        .pos-cell .pc-val { font-family: 'JetBrains Mono', monospace; font-size: 16px; font-weight: 700; }

        .no-pos { text-align: center; padding: 28px 0; color: var(--text-3); font-size: 14px; font-style: italic; }
        .no-pos .scan-icon { font-size: 32px; margin-bottom: 8px; display: block; animation: spin 3s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

        /* Trade history */
        .history-tbl { width: 100%; border-collapse: collapse; font-size: 13px; }
        .history-tbl th {
            text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: 1px;
            color: var(--text-3); padding: 0 8px 10px; font-weight: 600;
        }
        .history-tbl td { padding: 10px 8px; border-top: 1px solid rgba(255,255,255,0.04); font-family: 'JetBrains Mono', monospace; font-size: 12px; }
        .history-tbl tr:hover td { background: rgba(255,255,255,0.02); }
        .pnl-pos { color: var(--accent-green); font-weight: 700; }
        .pnl-neg { color: var(--accent-red); font-weight: 700; }
        .res-tp { background: rgba(52,211,153,0.1); color: var(--accent-green); padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 600; }
        .res-sl { background: rgba(248,113,113,0.1); color: var(--accent-red); padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 600; }

        /* CTA buttons */
        .cta-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 20px; }
        .cta-btn {
            display: flex; align-items: center; justify-content: center; gap: 8px;
            padding: 14px 16px; border-radius: 14px; text-decoration: none;
            font-size: 13px; font-weight: 600; transition: all 0.25s;
            border: 1px solid var(--border-glass);
        }
        .cta-primary { background: linear-gradient(135deg, #7c3aed, #2563eb); color: #fff; box-shadow: 0 4px 20px rgba(124,58,237,0.25); }
        .cta-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(124,58,237,0.35); }
        .cta-secondary { background: var(--bg-card); color: var(--text-2); }
        .cta-secondary:hover { border-color: rgba(167,139,250,0.3); color: var(--text-1); }

        /* Footer */
        .footer { text-align: center; padding: 8px 0; }
        .footer p { font-size: 11px; color: var(--text-3); letter-spacing: 0.3px; }
        .footer .heartbeat { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--text-3); margin-top: 4px; }

        @media (max-width: 640px) {
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .pos-grid { grid-template-columns: 1fr; }
            .cta-row { grid-template-columns: 1fr; }
            .price-hero { flex-direction: column; align-items: flex-start; gap: 16px; }
            .price-right { text-align: left; }
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
                <div class="brand-text">ETH Champion<span>v1.0</span></div>
            </div>
            <div class="live-chip"><div class="live-dot"></div>Bot Online</div>
        </div>

        <!-- Price Hero -->
        <div class="price-hero">
            <div class="price-left">
                <div class="price-label">ETH/USDT — Live Price</div>
                <div class="price-value">${last_price}</div>
                <div class="price-pair">Binance Spot • 15M Timeframe</div>
            </div>
            <div class="price-right">
                <div class="range-label">Last Candle Range</div>
                <div class="range-val">${last_range}</div>
                <div class="range-note">Trigger: &ge; $6.00</div>
            </div>
        </div>

        <!-- Stats Grid -->
        <div class="stats-grid">
            <div class="stat-tile">
                <div class="st-label">Wallet</div>
                <div class="st-value c-green">${wallet_balance}</div>
            </div>
            <div class="stat-tile">
                <div class="st-label">Total PnL</div>
                <div class="st-value {pnl_color}">{total_pnl}%</div>
            </div>
            <div class="stat-tile">
                <div class="st-label">Win Rate</div>
                <div class="st-value c-purple">{win_rate}%</div>
            </div>
            <div class="stat-tile">
                <div class="st-label">Trades</div>
                <div class="st-value c-blue">{total_trades}</div>
            </div>
        </div>

        <!-- Active Position Panel -->
        <div class="panel">
            <div class="panel-hdr">
                <h2>Active Position</h2>
                {dir_badge_html}
            </div>
            {active_position_html}
        </div>

        <!-- Trade History -->
        <div class="panel">
            <div class="panel-hdr">
                <h2>Recent Trade Log</h2>
                <span style="font-size: 11px; color: var(--text-3);">{wins}W / {losses}L</span>
            </div>
            {trade_history_html}
        </div>

        <!-- CTA Buttons -->
        <div class="cta-row">
            <a class="cta-btn cta-primary" href="{ledger_url}" target="_blank">&#128202; Google Sheets Ledger</a>
            <a class="cta-btn cta-secondary" href="https://dashboard.render.com/web/srv-d85g27svikkc739sjrtg" target="_blank">&#9881; Render Console</a>
        </div>

        <!-- Footer -->
        <div class="footer">
            <p>15M Timeframe &bull; $6.0 Breakout Range &bull; High/Low SL &bull; 1:3 Risk-Reward &bull; {trade_mode}</p>
            <div class="heartbeat">Last heartbeat: {last_heartbeat}</div>
        </div>
    </div>
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
            
            if os.path.exists('state.json'):
                try:
                    with open('state.json', 'r') as f:
                        loaded = json.load(f)
                        state.update(loaded)
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
                pos_html = f'''<div class="pos-grid">
                    <div class="pos-cell"><div class="pc-label">Entry Price</div><div class="pc-val" style="color:var(--text-1)">${active_trade["entry_price"]:.2f}</div></div>
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
