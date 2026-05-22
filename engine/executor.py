import ccxt
import time
import json
import os
import logging
import requests
import threading
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from engine.strategy_ema import EmaPullbackStrategy

# Set up logging to both console and bot.log file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

class SingleStrategyExecutor:
    def __init__(self, symbol: str, timeframe: str = '15m', dry_run: bool = True, api_key: str = '', secret: str = ''):
        self.symbol = symbol
        self.timeframe = timeframe
        self.dry_run = dry_run
        self.strategy = EmaPullbackStrategy()
        self.state_file = 'state.json'
        
        # Initialize CCXT Binance Client (Supports both live and dry fetch)
        exchange_config = {
            'enableRateLimit': True,
            'options': {'defaultType': 'future'} # Default to futures for Stop/Limit order support
        }
        if api_key and secret:
            exchange_config['apiKey'] = api_key
            exchange_config['secret'] = secret
            
        self.exchange = ccxt.binance(exchange_config)
        
        # Load or initialize trade state
        self.state = self.load_state()

    def _default_state(self) -> dict:
        return {
            'active_trade': None,
            'balance': 1000.0,
            'initial_balance': 1000.0,
            'dry_run': self.dry_run,
            'google_webhook_url': '',
            'google_doc_url': 'https://docs.google.com',
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'trade_history': [],
            'last_price': 0.0,
            'last_range': 0.0,
            'last_heartbeat': '',
            'bot_start_time': datetime.now().isoformat()
        }

    REMOTE_STATE_URL = "https://jsonblob.com/api/jsonBlob/019e50f6-1b7c-7536-a4be-1d87d8f3d668"

    def _remote_get(self) -> dict | None:
        """Fetch state from JSONBlob. Returns dict or None on failure."""
        try:
            res = requests.get(self.REMOTE_STATE_URL, timeout=8)
            if res.status_code == 200 and res.text.strip():
                state = res.json()
                logging.info("Successfully loaded persistent state from remote store.")
                return state
        except Exception as e:
            logging.error(f"Remote state GET failed: {e}")
        return None

    def _remote_put(self, state: dict):
        """Write state to JSONBlob via PUT."""
        try:
            requests.put(
                self.REMOTE_STATE_URL,
                json=state,
                headers={"Content-Type": "application/json"},
                timeout=8
            )
        except Exception as e:
            logging.error(f"Remote state PUT failed: {e}")

    def load_state(self) -> dict:
        # 1. Try remote store first (survives Render deploys & sleep)
        remote = self._remote_get()
        if remote:
            defaults = self._default_state()
            for k, v in defaults.items():
                if k not in remote:
                    remote[k] = v
            # Sync to local disk
            with open(self.state_file, 'w') as f:
                json.dump(remote, f, indent=4)
            return remote

        # 2. Fallback to local disk
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    logging.info(f"Loaded existing bot state from {self.state_file}")
                    defaults = self._default_state()
                    for k, v in defaults.items():
                        if k not in state:
                            state[k] = v
                    return state
            except Exception as e:
                logging.error(f"Error loading state file: {e}. Reinitializing state.")

        default_state = self._default_state()
        self.save_state(default_state)
        logging.info("Initialized fresh state.json")
        return default_state

    def save_state(self, state: dict):
        # Save to local disk
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to write state to disk: {e}")

        # Sync to remote store (fire-and-forget in background thread)
        threading.Thread(target=self._remote_put, args=(state.copy(),), daemon=True).start()

    def log_trade_to_google(self, event_type: str, trade_info: dict):
        """Sends trade data to Google Apps Script webhook for single-row-per-trade logging."""
        webhook_url = os.environ.get('GOOGLE_WEBHOOK_URL') or self.state.get('google_webhook_url', '')
        if not webhook_url:
            logging.info("Google Doc/Sheet Webhook URL not set. Skipping remote logging.")
            return
        
        now = datetime.utcnow()
        
        payload = {
            "event": event_type,
            "symbol": self.symbol,
            "direction": trade_info.get('direction', ''),
            "entry_price": trade_info.get('entry_price', 0.0),
            "sl_price": trade_info.get('sl_price', 0.0),
            "tp_price": trade_info.get('tp_price', 0.0),
            "current_balance": self.state['balance']
        }
        
        if event_type == 'OPENED':
            payload["open_timestamp"] = now.strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
        
        elif event_type == 'CLOSED':
            payload["close_timestamp"] = now.strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
            payload["exit_price"] = trade_info.get('exit_price', 0.0)
            payload["return_pct"] = trade_info.get('return_pct', 0.0)
            payload["exit_reason"] = trade_info.get('exit_reason', '')
            
            # Calculate trade duration and candle count
            entry_time_str = trade_info.get('entry_time', '')
            if entry_time_str:
                try:
                    entry_time = datetime.fromisoformat(entry_time_str)
                    duration_seconds = (now - entry_time).total_seconds()
                    duration_minutes = int(duration_seconds // 60)
                    hours = duration_minutes // 60
                    mins = duration_minutes % 60
                    payload["duration"] = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
                    payload["candle_count"] = max(1, int(duration_minutes // 15))
                except Exception:
                    payload["duration"] = "N/A"
                    payload["candle_count"] = 0
            else:
                payload["duration"] = "N/A"
                payload["candle_count"] = 0
        
        def send_request():
            try:
                res = requests.post(webhook_url, json=payload, timeout=10)
                logging.info(f"Successfully logged {event_type} trade to Google. Status: {res.status_code}")
            except Exception as e:
                logging.error(f"Failed to log trade to Google Docs/Sheets: {e}")
                
        # OPENED must be synchronous to survive Render redeploys.
        # CLOSED can be fire-and-forget since the bot sleeps for 15min after.
        if event_type == 'OPENED':
            send_request()
        else:
            threading.Thread(target=send_request, daemon=True).start()

    def sleep_until_next_candle(self):
        """Calculates precise remaining time until next 15M boundary and sleeps."""
        now = datetime.now()
        
        # Next 15M boundary calculation
        minutes_to_add = 15 - (now.minute % 15)
        next_candle_time = now.replace(second=0, microsecond=0) + timedelta(minutes=minutes_to_add)
        
        # Extra 0.3 second safety delay to ensure CCXT/Binance has closed the candle on server
        next_candle_time += timedelta(seconds=0.3)
        
        sleep_seconds = (next_candle_time - now).total_seconds()
        
        if sleep_seconds > 0:
            logging.info(f"Precise sleep: Waking up at {next_candle_time.strftime('%Y-%m-%d %H:%M:%S')} (sleeping for {sleep_seconds:.1f}s)")
            time.sleep(sleep_seconds)

    def fetch_live_data(self) -> pd.DataFrame:
        """Fetches the last 50 candles to compute indicators safely with Bybit/OKX fallbacks."""
        # 1. Try Primary Exchange (Binance)
        try:
            candles = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=50)
            df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            logging.warning(f"Error fetching candles from primary exchange {self.exchange.id}: {e}. Trying Bybit fallback...")
            
        # 2. Try Bybit Fallback (often unbanned on Render hosting)
        try:
            # Create a stateless Bybit client
            fallback_exchange = ccxt.bybit({'enableRateLimit': True})
            bybit_symbol = self.symbol.replace('/', '') if '/' in self.symbol else self.symbol
            candles = fallback_exchange.fetch_ohlcv(bybit_symbol, self.timeframe, limit=50)
            df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            logging.info("Successfully fetched data from Bybit fallback.")
            return df
        except Exception as e2:
            logging.warning(f"Error fetching candles from Bybit fallback: {e2}. Trying OKX fallback...")
            
        # 3. Try OKX Fallback
        try:
            fallback_exchange = ccxt.okx({'enableRateLimit': True})
            okx_symbol = self.symbol.replace('/', '-') if '/' in self.symbol else self.symbol
            if '-' not in okx_symbol:
                okx_symbol = okx_symbol.replace('USDT', '-USDT')
            candles = fallback_exchange.fetch_ohlcv(okx_symbol, self.timeframe, limit=50)
            df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            logging.info("Successfully fetched data from OKX fallback.")
            return df
        except Exception as e3:
            logging.error(f"Failed to fetch data from all exchanges: {e3}")
            return pd.DataFrame()

    def process_signals(self):
        df = self.fetch_live_data()
        if df.empty:
            logging.warning("Dataframe empty, skipping processing round.")
            return
            
        df = self.strategy.populate_indicators(df)
        df = self.strategy.populate_signals(df, min_range=6.0)
        
        last_closed_candle = df.iloc[-2]
        current_price = df.iloc[-1]['close']
        
        # Persist live market data for the dashboard
        self.state['last_price'] = round(current_price, 2)
        self.state['last_range'] = round(last_closed_candle['range'], 2)
        self.state['last_heartbeat'] = datetime.now().isoformat()
        self.save_state(self.state)
        
        logging.info(f"Heartbeat Checked. Current Price: ${current_price:.2f} | Last Closed Candle Range: ${last_closed_candle['range']:.2f}")
        
        # 1. Manage Active Trade Exit Checks
        if self.state['active_trade'] is not None:
            trade = self.state['active_trade']
            exit_triggered = False
            exit_price = 0.0
            exit_reason = ""
            
            if self.dry_run:
                high_val = last_closed_candle['high']
                low_val = last_closed_candle['low']
                
                if trade['direction'] == 'Long':
                    if low_val <= trade['sl_price']:
                        exit_price = trade['sl_price']
                        exit_reason = 'SL'
                        exit_triggered = True
                    elif high_val >= trade['tp_price']:
                        exit_price = trade['tp_price']
                        exit_reason = 'TP'
                        exit_triggered = True
                else: # Short
                    if high_val >= trade['sl_price']:
                        exit_price = trade['sl_price']
                        exit_reason = 'SL'
                        exit_triggered = True
                    elif low_val <= trade['tp_price']:
                        exit_price = trade['tp_price']
                        exit_reason = 'TP'
                        exit_triggered = True
            else:
                try:
                    sl_order = self.exchange.fetch_order(trade['sl_order_id'], self.symbol)
                    tp_order = self.exchange.fetch_order(trade['tp_order_id'], self.symbol)
                    
                    if sl_order['status'] == 'closed':
                        exit_price = trade['sl_price']
                        exit_reason = 'SL'
                        exit_triggered = True
                        self.exchange.cancel_order(trade['tp_order_id'], self.symbol)
                    elif tp_order['status'] == 'closed':
                        exit_price = trade['tp_price']
                        exit_reason = 'TP'
                        exit_triggered = True
                        self.exchange.cancel_order(trade['sl_order_id'], self.symbol)
                except Exception as e:
                    logging.error(f"Failed to fetch order status from exchange: {e}")
            
            if exit_triggered:
                if trade['direction'] == 'Long':
                    trade_return = ((exit_price - trade['entry_price']) / trade['entry_price']) * 100
                else:
                    trade_return = ((trade['entry_price'] - exit_price) / trade['entry_price']) * 100
                    
                old_balance = self.state['balance']
                self.state['balance'] = old_balance * (1 + trade_return / 100)
                
                logging.info(f"🏆 Active Position Closed! Reason: {exit_reason} | Return: {trade_return:+.2f}% | Balance: ${self.state['balance']:.2f}")
                
                # Remote log closing details
                trade['exit_price'] = exit_price
                trade['return_pct'] = round(trade_return, 2)
                trade['exit_reason'] = exit_reason
                self.log_trade_to_google('CLOSED', trade)
                
                # Track stats for dashboard
                self.state['total_trades'] = self.state.get('total_trades', 0) + 1
                if trade_return > 0:
                    self.state['wins'] = self.state.get('wins', 0) + 1
                else:
                    self.state['losses'] = self.state.get('losses', 0) + 1
                
                # Append to trade history (keep last 20)
                history_entry = {
                    'time': datetime.now().strftime('%m/%d %H:%M'),
                    'dir': trade['direction'][0],
                    'entry': round(trade['entry_price'], 2),
                    'exit': round(exit_price, 2),
                    'pnl': round(trade_return, 2),
                    'result': exit_reason
                }
                history = self.state.get('trade_history', [])
                history.append(history_entry)
                self.state['trade_history'] = history[-20:]  # Keep last 20 trades
                
                self.state['active_trade'] = None
                self.save_state(self.state)
                
        # 2. Check for New Entries if no trade is active
        if self.state['active_trade'] is None:
            enter_long = last_closed_candle['enter_long'] == 1
            enter_short = last_closed_candle['enter_short'] == 1
            
            if enter_long or enter_short:
                # STALENESS CHECK: Prevent late entry if server woke up late
                candle_open_time = last_closed_candle.name
                candle_close_time = candle_open_time + timedelta(minutes=15)
                current_time = datetime.utcnow()
                
                # If current time is more than 15 seconds past the candle close, it's a stale signal
                if (current_time - candle_close_time).total_seconds() > 15:
                    logging.warning(f"Skipping stale signal! Candle closed at {candle_close_time} UTC, current time is {current_time.strftime('%Y-%m-%d %H:%M:%S')} UTC.")
                    return

                direction = 'Long' if enter_long else 'Short'
                entry_price = current_price
                sl_price = last_closed_candle['low'] if enter_long else last_closed_candle['high']
                
                if sl_price == entry_price:
                    logging.warning("SL price matches entry price, skipping trade trigger.")
                    return
                    
                risk = abs(entry_price - sl_price)
                tp_price = entry_price + (risk * 3.0) if enter_long else entry_price - (risk * 3.0)
                
                logging.info(f"🚀 Signal Confirmed! Direction: {direction} | Entry: ${entry_price:.2f} | SL: ${sl_price:.2f} | TP: ${tp_price:.2f}")
                
                active_trade = {
                    'entry_time': datetime.now().isoformat(),
                    'direction': direction,
                    'entry_price': entry_price,
                    'sl_price': sl_price,
                    'tp_price': tp_price
                }
                
                if not self.dry_run:
                    try:
                        margin_allocated = self.state['balance'] * 0.1
                        position_size = margin_allocated / entry_price
                        
                        logging.info(f"Placing live market {direction} order for {position_size:.4f} {self.symbol}...")
                        
                        side = 'buy' if direction == 'Long' else 'sell'
                        entry_order = self.exchange.create_market_order(self.symbol, side, position_size)
                        
                        opp_side = 'sell' if direction == 'Long' else 'buy'
                        sl_order = self.exchange.create_order(
                            symbol=self.symbol,
                            type='STOP_MARKET',
                            side=opp_side,
                            amount=position_size,
                            params={'stopPrice': sl_price}
                        )
                        
                        tp_order = self.exchange.create_order(
                            symbol=self.symbol,
                            type='LIMIT',
                            side=opp_side,
                            amount=position_size,
                            price=tp_price
                        )
                        
                        active_trade['entry_order_id'] = entry_order['id']
                        active_trade['sl_order_id'] = sl_order['id']
                        active_trade['tp_order_id'] = tp_order['id']
                        
                    except Exception as e:
                        logging.error(f"Fatal error placing live orders: {e}.")
                        return
                
                self.state['active_trade'] = active_trade
                self.save_state(self.state)
                
                # Remote log opening details
                self.log_trade_to_google('OPENED', active_trade)

    def start_loop(self):
        logging.info(f"Bot execution engine started. Target: {self.symbol} ({self.timeframe}) | Dry-Run: {self.dry_run}")
        while True:
            try:
                self.process_signals()
                self.sleep_until_next_candle()
            except KeyboardInterrupt:
                logging.info("Bot execution gracefully terminated by user.")
                break
            except Exception as e:
                logging.error(f"Unexpected loop exception: {e}. Restarting in 10s...")
                time.sleep(10)