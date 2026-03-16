import os
import time
import math
from dotenv import load_dotenv
from pybit.unified_trading import HTTP
from leverage_config import LEVERAGE_SETTINGS
from database import get_settings, insert_trade, update_trade, get_open_trades

load_dotenv()

BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")
BYBIT_TESTNET = os.getenv("BYBIT_TESTNET", "false").lower() == "true"

session = HTTP(
    testnet=BYBIT_TESTNET,
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_API_SECRET,
)

def get_market_price(ticker):
    try:
        res = session.get_tickers(category="linear", symbol=ticker)
        if "result" in res and "list" in res["result"] and len(res["result"]["list"]) > 0:
            return float(res["result"]["list"][0]["lastPrice"])
        return None
    except Exception as e:
        print(f"Error getting market price for {ticker}: {e}")
        return None

def calculate_quantity(target_profit, entry_price, tp_price, ticker):
    # Quantity = Target_Profit / abs(Entry_Price - Take_Profit_Price)
    diff = abs(entry_price - tp_price)
    if diff == 0:
        return 0
    qty = target_profit / diff
    
    # Needs to format to Bybit precision for ticker.
    try:
        res = session.get_instruments_info(category="linear", symbol=ticker)
        if "result" in res and "list" in res["result"]:
            info = res["result"]["list"][0]
            qty_step = float(info["lotSizeFilter"]["qtyStep"])
            decimals = int(-math.log10(qty_step)) if qty_step < 1 else 0
            
            if decimals > 0:
                qty = round(qty, decimals)
            else:
                qty = int(qty)
            
            min_qty = float(info["lotSizeFilter"]["minOrderQty"])
            if qty < min_qty:
                qty = min_qty
            return qty
    except Exception as e:
        print(f"Error fetching qty precision: {e}")
    return round(qty, 3)

def set_leverage(ticker):
    leverage = LEVERAGE_SETTINGS.get(ticker, 10)
    try:
        session.set_leverage(
            category="linear",
            symbol=ticker,
            buyLeverage=str(leverage),
            sellLeverage=str(leverage)
        )
    except Exception as e:
        if "leverage not modified" not in str(e).lower() and "not modified" not in str(e).lower():
            print(f"Error setting leverage for {ticker}: {e}")

def enter_trade(payload):
    ticker = payload.get("ticker")
    action = payload.get("action", "").lower()
    tp_price = float(payload.get("tp", 0))
    sl_price = float(payload.get("sl", 0))
    
    if ticker not in LEVERAGE_SETTINGS:
        return {"success": False, "error": f"Unsupported ticker: {ticker}"}
        
    market_price = get_market_price(ticker)
    if not market_price:
        return {"success": False, "error": f"Could not fetch market price for {ticker}"}
        
    if action == "buy":
        if market_price >= tp_price or market_price <= sl_price:
            return {"success": False, "error": f"Market price {market_price} is outside valid bounds for buy: sl={sl_price}, tp={tp_price}"}
        side = "Buy"
        sl_limit = sl_price * 0.999
    elif action == "sell":
        if market_price <= tp_price or market_price >= sl_price:
            return {"success": False, "error": f"Market price {market_price} is outside valid bounds for sell: sl={sl_price}, tp={tp_price}"}
        side = "Sell"
        sl_limit = sl_price * 1.001
    else:
        return {"success": False, "error": f"Invalid action: {action}"}
        
    settings = get_settings()
    target_profit = settings.get("target_profit", 60.0)
    
    quantity = calculate_quantity(target_profit, market_price, tp_price, ticker)
    if quantity == 0:
        return {"success": False, "error": "Calculated quantity is 0"}
        
    set_leverage(ticker)
    
    try:
        # Place market order with conditional TP/SL limit orders
        order = session.place_order(
            category="linear",
            symbol=ticker,
            side=side,
            orderType="Market",
            qty=str(quantity),
            takeProfit=str(tp_price),
            stopLoss=str(sl_price),
            tpslMode="Full",
            tpLimitPrice=str(tp_price),
            slLimitPrice=str(sl_limit),
            tpOrderType="Limit",
            slOrderType="Limit"
        )
        
        order_id = order["result"]["orderId"]
        trade_id = insert_trade(ticker, action, market_price, tp_price, sl_price, quantity, "open", target_profit, order_id)
        
        return {"success": True, "trade_id": trade_id, "order_id": order_id, "entry": market_price, "qty": quantity}
    except Exception as e:
        error_msg = str(e)
        insert_trade(ticker, action, market_price, tp_price, sl_price, quantity, "failed", target_profit, None, error_msg)
        return {"success": False, "error": error_msg}

def sync_trades():
    open_trades = get_open_trades()
    if not open_trades:
        return {"success": True, "message": "No open trades to sync"}
        
    synced = 0
    errors = 0
    
    for trade in open_trades:
        try:
            # Check positions
            pos_res = session.get_positions(category="linear", symbol=trade["ticker"])
            positions = pos_res.get("result", {}).get("list", [])
            
            position_open = False
            for pos in positions:
                if float(pos.get("size", 0)) > 0:
                    position_open = True
                    break
                    
            if not position_open:
                # Need to find closed PnL
                hist_res = session.get_closed_pnl(category="linear", symbol=trade["ticker"], limit=10)
                closed_pnl_list = hist_res.get("result", {}).get("list", [])
                
                # Simple heuristic: find latest closed pnl for this ticker (robust logic requires order ID matching)
                # In Bybit, we can match by checking closed PnL related to the order. For simplicity here:
                pnl = 0.0
                if closed_pnl_list:
                    pnl = float(closed_pnl_list[0].get("closedPnl", 0.0))
                
                update_trade(trade["id"], status="closed", pnl=pnl)
                synced += 1
            else:
                # Update current PnL for open trade
                pnl = 0.0
                for pos in positions:
                    if float(pos.get("size", 0)) > 0:
                        pnl = float(pos.get("unrealisedPnl", 0.0))
                        break
                update_trade(trade["id"], pnl=pnl)
                synced += 1
                
        except Exception as e:
            print(f"Error syncing trade {trade['id']}: {e}")
            errors += 1
            
    return {"success": True, "synced": synced, "errors": errors}
