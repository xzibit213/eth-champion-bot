import pandas as pd
import numpy as np
import pandas_ta as ta

class BaseStrategy:
    def populate_indicators(self, df):
        pass

    def populate_signals(self, df):
        pass

class MACDStrategy(BaseStrategy):
    def populate_indicators(self, df):
        # Calculate MACD using pandas-ta
        # This appends MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9 to df
        df.ta.macd(close='close', fast=12, slow=26, signal=9, append=True)
        # Rename columns to standard names for easier access
        df.rename(columns={'MACD_12_26_9': 'macd', 'MACDh_12_26_9': 'macdhist', 'MACDs_12_26_9': 'macdsignal'}, inplace=True)
        return df

    def populate_signals(self, df):
        df['enter_long'] = 0
        df['exit_long'] = 0
        
        # Long Entry: MACD crosses above Signal
        df['enter_long'] = np.where(
            (df['macd'] > df['macdsignal']) & 
            (df['macd'].shift(1) <= df['macdsignal'].shift(1)), 1, 0)
        
        # Long Exit: MACD crosses below Signal
        df['exit_long'] = np.where(
            (df['macd'] < df['macdsignal']) & 
            (df['macd'].shift(1) >= df['macdsignal'].shift(1)), 1, 0)
        
        return df