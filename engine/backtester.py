import pandas as pd
import math
from datetime import datetime

class RiskManagedBacktester:
    def __init__(self, initial_balance=10000.0, use_break_even=False, reward_risk_ratio=3.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.use_break_even = use_break_even
        self.reward_risk_ratio = reward_risk_ratio
        
        self.max_balance = initial_balance
        self.max_drawdown = 0.0
        
        self.active_trade = None
        self.trade_log = []

    def run_backtest(self, df: pd.DataFrame) -> pd.DataFrame:
        self.balance = self.initial_balance
        self.max_balance = self.initial_balance
        self.max_drawdown = 0.0
        self.active_trade = None
        self.trade_log = []
        
        # High performance optimization: convert DataFrame to records dict list
        records = df.to_dict('records')
        timestamps = df.index.tolist()
        
        for idx in range(len(records)):
            row = records[idx]
            index = timestamps[idx]
            
            # 1. Check open trade for exits
            if self.active_trade is not None:
                trade = self.active_trade
                
                # Check for Break-Even Trigger (1:1 R:R)
                if self.use_break_even and not trade['be_triggered']:
                    if trade['direction'] == 'Long':
                        if row['high'] >= trade['entry_price'] + trade['risk_per_unit']:
                            trade['sl_price'] = trade['entry_price']
                            trade['be_triggered'] = True
                    elif trade['direction'] == 'Short':
                        if row['low'] <= trade['entry_price'] - trade['risk_per_unit']:
                            trade['sl_price'] = trade['entry_price']
                            trade['be_triggered'] = True
                
                exit_price = None
                exit_reason = None
                
                # Check exit conditions (assume SL hit first if both hit, to be conservative)
                if trade['direction'] == 'Long':
                    if row['low'] <= trade['sl_price']:
                        exit_price = trade['sl_price']
                        exit_reason = 'SL'
                    elif row['high'] >= trade['tp_price']:
                        exit_price = trade['tp_price']
                        exit_reason = 'TP'
                elif trade['direction'] == 'Short':
                    if row['high'] >= trade['sl_price']:
                        exit_price = trade['sl_price']
                        exit_reason = 'SL'
                    elif row['low'] <= trade['tp_price']:
                        exit_price = trade['tp_price']
                        exit_reason = 'TP'
                
                if exit_price is not None:
                    trade_amount = trade['margin'] * trade['leverage']
                    if trade['direction'] == 'Long':
                        profit = ((exit_price - trade['entry_price']) / trade['entry_price']) * trade_amount
                    else:
                        profit = ((trade['entry_price'] - exit_price) / trade['entry_price']) * trade_amount
                    
                    self.balance += profit
                    trade['exit_date'] = index
                    trade['exit_price'] = exit_price
                    trade['profit'] = profit
                    trade['exit_reason'] = exit_reason
                    trade['final_balance'] = self.balance
                    
                    # Drawdown Tracking
                    self.max_balance = max(self.max_balance, self.balance)
                    current_dd = ((self.max_balance - self.balance) / self.max_balance) * 100
                    self.max_drawdown = max(self.max_drawdown, current_dd)
                    
                    self.trade_log.append(trade)
                    self.active_trade = None

            # 2. Check for new entries if no trade is active
            if self.active_trade is None:
                if row['enter_long'] == 1 or row['enter_short'] == 1:
                    direction = 'Long' if row['enter_long'] == 1 else 'Short'
                    entry_price = row['close']
                    sl_price = row['sl_price']
                    
                    if sl_price == entry_price:
                        continue # Avoid division by zero
                    
                    risk_dollar_per_unit = abs(entry_price - sl_price)
                    sl_distance_pct = (risk_dollar_per_unit / entry_price) * 100
                    
                    tp_price = entry_price + (risk_dollar_per_unit * self.reward_risk_ratio) if direction == 'Long' else entry_price - (risk_dollar_per_unit * self.reward_risk_ratio)
                    
                    margin = 10.0
                    max_loss = self.balance * 0.03
                    
                    # Required Leverage = (Account Balance × 0.03) / (10 × Stop Loss Distance% / 100)
                    required_leverage = max_loss / (margin * (sl_distance_pct / 100))
                    leverage = math.floor(required_leverage)
                    
                    if leverage > 100:
                        continue # Skip trade if required leverage > exchange cap (100x)
                    if leverage < 1:
                        leverage = 1
                        
                    self.active_trade = {
                        'entry_date': index,
                        'direction': direction,
                        'entry_price': entry_price,
                        'sl_price': sl_price,
                        'tp_price': tp_price,
                        'risk_per_unit': risk_dollar_per_unit,
                        'sl_distance_pct': sl_distance_pct,
                        'margin': margin,
                        'leverage': leverage,
                        'balance_at_entry': self.balance,
                        'signal_range': row.get('range', 0),
                        'be_triggered': False
                    }

        return pd.DataFrame(self.trade_log)

    def generate_mom_report(self):
        if not self.trade_log:
            return pd.DataFrame()
            
        df_log = pd.DataFrame(self.trade_log)
        df_log['month'] = df_log['exit_date'].dt.to_period('M')
        mom_report = df_log.groupby('month').agg(
            total_trades=('profit', 'count'),
            win_count=('profit', lambda x: (x > 0).sum()),
            loss_count=('profit', lambda x: (x <= 0).sum()),
            net_profit=('profit', 'sum')
        )
        mom_report['win_rate'] = mom_report['win_count'] / mom_report['total_trades'] * 100
        return mom_report