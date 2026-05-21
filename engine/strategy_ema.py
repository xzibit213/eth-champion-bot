import pandas as pd
import pandas_ta as ta

class EmaPullbackStrategy:
    def populate_indicators(self, df):
        df['ema_9'] = ta.ema(df['close'], length=9)
        df['ema_20'] = ta.ema(df['close'], length=20)
        df['range'] = df['high'] - df['low']
        return df

    def populate_signals(self, df, min_range=6.0):
        """
        Populates Entry Signals for the Champion ETH/USDT 15M EMA Pullback Strategy.
        - Long Trigger: EMA(9) > EMA(20) && Close > Open && Range >= $6.0 && (Low <= EMA(9) or Open <= EMA(9) or Low <= EMA(20) or Open <= EMA(20))
        - Short Trigger: EMA(9) < EMA(20) && Close < Open && Range >= $6.0 && (High >= EMA(9) or Open >= EMA(9) or High >= EMA(20) or Open >= EMA(20))
        - Stop Loss: Signal candle Low (for Longs) or High (for Shorts)
        - Take Profit: 1:3 Risk-to-Reward Ratio from entry
        """
        df['enter_long'] = 0
        df['enter_short'] = 0
        df['sl_price'] = 0.0

        # Long Signal population
        df.loc[(df['ema_9'] > df['ema_20']) & (df['close'] > df['open']) & (df['range'] >= min_range) & ((df['low'] <= df['ema_9']) | (df['open'] <= df['ema_9']) | (df['low'] <= df['ema_20']) | (df['open'] <= df['ema_20'])), 'enter_long'] = 1
        df.loc[df['enter_long'] == 1, 'sl_price'] = df['low']

        # Short Signal population
        df.loc[(df['ema_9'] < df['ema_20']) & (df['close'] < df['open']) & (df['range'] >= min_range) & ((df['high'] >= df['ema_9']) | (df['open'] >= df['ema_9']) | (df['high'] >= df['ema_20']) | (df['open'] >= df['ema_20'])), 'enter_short'] = 1
        df.loc[df['enter_short'] == 1, 'sl_price'] = df['high']

        return df