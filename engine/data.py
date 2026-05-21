import pandas as pd
import ccxt
import time

class BinanceData:
    def __init__(self):
        self.binance = ccxt.binance()

    def fetch_ohlcv(self, symbol: str, timeframe: str, since_ms: int, until_ms: int) -> pd.DataFrame:
        candles = []
        current_since = since_ms
        print(f"Fetching {symbol} {timeframe} data from {pd.to_datetime(since_ms, unit='ms')} to {pd.to_datetime(until_ms, unit='ms')}...")
        
        while current_since < until_ms:
            try:
                ohlcv = self.binance.fetch_ohlcv(symbol, timeframe, since=current_since, limit=1000)
                if not ohlcv:
                    break
                
                # Filter out candles that go beyond until_ms
                ohlcv = [c for c in ohlcv if c[0] <= until_ms]
                if not ohlcv:
                    break
                    
                candles.extend(ohlcv)
                
                if len(ohlcv) < 1000:
                    break
                    
                current_since = ohlcv[-1][0] + 1
                time.sleep(0.1) # Respect rate limits
            except Exception as e:
                print(f"Error fetching data: {e}")
                time.sleep(5) # Wait before retry
                
        df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        # Drop duplicates just in case pagination overlaps
        df = df[~df.index.duplicated(keep='first')]
        print(f"Successfully fetched {len(df)} candles.")
        return df