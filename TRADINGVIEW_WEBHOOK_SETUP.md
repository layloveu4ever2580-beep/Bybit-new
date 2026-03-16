# TradingView Webhook Setup

This guide will help you configure TradingView alerts to send webhook signals to the bot.

## 1. Webhook URL

In the TradingView alert settings, enable **Webhook URL** under the Notifications tab and paste your deployed render URL + `/webhook`:

`https://your-app-name.onrender.com/webhook`

## 2. Message Payload Format

Select **Order fills and alert() function calls** as the alert condition. In the message box, enter exactly:

`{{message}}`

## 3. Pine Script Setup

Your Pine Script should use the `alert()` function to send the signal as a JSON string when a trade signal is generated. The JSON must match the following schema:

```json
{
  "ticker": "ETCUSDT.P",
  "action": "buy",
  "limit": 8.80,
  "tp": 8.92,
  "sl": 8.68,
  "entry_filled": true
}
```

The bot takes the `action` ("buy" or "sell"). `limit` is ignored, and it executes a market order instantly. `tp` and `sl` are placed as conditional limit orders immediately following the entry order.

Ensure your script only sends tickets configured in `leverage_config.py`.
