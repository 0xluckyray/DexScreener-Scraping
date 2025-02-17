import websocket
import json
import requests
import dotenv
import os
import time
from pymongo import MongoClient
from get_supply import get_total_supply
from get_liquidity import get_liquidity
from get_pair_address import get_pair_address

# Load environment variables from .env file
dotenv.load_dotenv()
ETHERSCAN_API_KEY=os.getenv("ETHERSCAN_API_KEY")  # Get Etherscan API key from environment variable
CIELO_API_KEY=os.getenv("CIELO_API_KEY")  # Get Cielo API key from environment variable
MONGODB_URL=os.getenv("MONGODB_URL") # Get MongoDB url from environment variable
TELEGRAM_BOT_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN") # Get telegram bot token
def track_wallets():
    # Connect to MongoDB database
    mongo_client = MongoClient(MONGODB_URL)  # Replace with your MongoDB connection string
    db = mongo_client["Dexscreener"]  # Replace with your database name
    collection = db["wallet_data"]  # Replace with your collection name

    ###########################################################
    #           Realtime Tracking by using Ceilo API          #
    ###########################################################

    cielo_url = "https://feed-api.cielo.finance/api/v1/tracked-wallets"  # URL for Cielo API
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-API-KEY": CIELO_API_KEY   # Set API key in headers for authentication
    }
    # Function to add tracked wallets to Cielo API
    def add_tracked_wallets(wallet, label):
        payload = {
            "wallet": wallet,  # Wallet address to be tracked
            "label": label  # Label associated with the wallet
        }
        response = requests.post(cielo_url, json=payload, headers=headers)  # Send POST request to add wallet
        print(f"{wallet} is added to track wallet list {label}") # Log addition of wallet

    # Function to retrieve currently tracked wallets from Cielo API
    def get_tracked_wallets():
        response = requests.get(cielo_url, headers=headers) # Send GET request to retrieve tracked wallets
        return response.json() # Return JSON response

    # Function to delete tracked wallets
    def delete_tracked_wallets(id):
        payload = { "wallet_ids": id }  # Prepare payload with wallet IDs to delete
        response = requests.delete(cielo_url, json=payload, headers=headers)  # Send DELETE request

    # WebSocket event handlers

    # Function to send a message to a Telegram channel when a swap occurs
    def send_message_to_telegram(message):
      if message['token0_symbol'] == "WETH":
        total_supply = get_total_supply(message['token1_address'], ETHERSCAN_API_KEY)  # Get total supply of token1
        market_cap = total_supply * message['token1_price_usd']  # Calculate market cap based on token1 price
        other_token = message['token1_address']  # Set other token as token1 address
      else :
        total_supply = get_total_supply(message['token0_address'], ETHERSCAN_API_KEY)  # Get total supply of token0
        market_cap = total_supply * message['token0_price_usd']  # Calculate market cap based on token0 price
        other_token = message['token0_address']  # Set other token as token0 address
      if total_supply > 1e23:
        market_cap = market_cap / 1e9  # Convert market cap to billions if over threshold
      market_cap = market_cap / 1e9  # Ensure market cap is in billions
      pair_address = get_pair_address(message['token1_address'], message['token0_address'])  # Get pair address from given two tokens
      liquidity_response = get_liquidity(pair_address, message['token0_address'], message['token1_address'], other_token) # Get balance and holder count from bitquery
      if pair_address == None or liquidity_response['data']['EVM']['token1Balance'] == []:
        liquidity = 0
        holder_count = 0
      else:
        liquidity = float(liquidity_response['data']['EVM']['token1Balance'][0]['balance'])*float(message['token0_price_usd']) + float(liquidity_response['data']['EVM']['token2Balance'][0]['balance'])*float(message['token1_price_usd'])
        holder_count = int(liquidity_response['data']['EVM']['TokenHolders'][0]['uniq'])  # Get unique holder count
      print("total_supply:", total_supply, "market_cap:", market_cap, "liquidity:", liquidity, "holder:", holder_count)
      bot_token = TELEGRAM_BOT_TOKEN # Telegram bot(Bitcoin Lottery) token (replace with your own)
      chat_id = '@blackbox_alert_ch'  # Use the channel name with "@" prefix
    #   chat_id1 = '@+186S3MLPRUNmNGUx'
      # Set the content of bot's message
    #   print(message)
      message_content = (
        "🆔 #{label} most profitable wallet\n"
        "⭐️ Swapped {token0_amount} #{token0_symbol} (${token0_usd}) for {token1_amount} #{token1_symbol} @ ${token1_usd}.\n"
        "📊 Market Cap: ${market_cap}\n"
        "💰 Liquidity: ${liquidity}\n"
        "🤘 Holder Counts: {holder_count}\n"
        "Token: <code>{other}</code>\n"
        "#ethereum | <a href='https://app.cielo.finance/profile/{wallet_address}'>Cielo</a> | <a href='https://etherscan.io/tx/{hash}'>ViewTx</a> | <a href='https://www.defined.fi/eth/{other}'>Chart</a>\n"
        ).format(
          label = "{:03}".format(int(message['from_label'])),
          market_cap = round(market_cap, 2), 
          liquidity = round(liquidity, 2),
          holder_count = holder_count,
          wallet_address = message['wallet'],
          hash = message['tx_hash'],
          token0_amount = round(message['token0_amount'], 2), token0_symbol = message['token0_symbol'],
          token0_usd = round(float(message['token0_amount']) * float(message['token0_price_usd']), 2), 
          token1_amount = round(message['token1_amount'], 2), token1_symbol = message['token1_symbol'],
          token1_usd = float(message['token1_price_usd']), 
          other = other_token,
         
          )

      # URL for sending messages
      url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

      # Parameters for the request
      params = {
          'chat_id': chat_id,
          'text': message_content,
          'parse_mode': 'HTML',
          'disable_web_page_preview': True  # Disable link previews
      }
      response = requests.get(url, params=params)
      
    def on_open(ws):
        print("Real time tracking started..")  # Log when tracking starts
        subscribe_message = {
            "type": "subscribe_feed",  # Message type for subscription
            "filter": {
                "tx_types": ["swap"],   # Filter for transaction types (swaps)
                "chains": ["ethereum"]  # Filter for Ethereum chain only
            }
        }
        ws.send(json.dumps(subscribe_message))  # Send subscription message

    def on_message(ws, message):
        print("Received:", message)   # Log received WebSocket message
        parsed_message = json.loads(message)  # Parse JSON message from WebSocket
        if parsed_message['type']=="tx" and parsed_message['data']['token0_address'] !=parsed_message['data']['token1_address']:
          send_message_to_telegram(parsed_message['data'])  # Call function to send message if it's a swap transaction

    def on_error(ws, error):
        print("WebSocket error:", error)  # Log any errors that occur with the WebSocket
        on_open(ws)

    def on_close(ws, close_status_code, close_msg):
        print("WebSocket connection closed")  # Log when WebSocket connection is closed
        print(f"Status code: {close_status_code}, Message: {close_msg}")
        print("Attempting to reconnect...")
        while True:
            time.sleep(2)  # Wait for 2 seconds before reconnecting
            ws.run_forever()  # Attempt to reconnect

    WS_URL = 'wss://feed-api.cielo.finance/api/v1/ws'

    # Delete old tracked wallets
    data = get_tracked_wallets()
    tracked_wallet_id = []

    for tracked_wallet in data['data']['tracked_wallets']:
        tracked_wallet_id.append(tracked_wallet['id'])
    delete_tracked_wallets(tracked_wallet_id)

    # Load target wallet addresses from MongoDB, sorted by average profit
    track_wallets = list(collection.find({}).sort([("Total_PNL", -1)]).limit(200))  # Convert cursor to list
    if len(track_wallets) > 0:
        index = 1
        for wallet in track_wallets:
            add_tracked_wallets(wallet['Address'], str(index))
            index = index + 1

    # Create a WebSocket application
    ws = websocket.WebSocketApp(
        WS_URL,
        header=["X-API-KEY: {}".format(CIELO_API_KEY)],
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # Run the WebSocket app
    ws.run_forever()