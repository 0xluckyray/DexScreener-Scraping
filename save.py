import requests
from pymongo import MongoClient
from bs4 import BeautifulSoup
import os
import dotenv
from datetime import datetime 
import time

dotenv.load_dotenv()
CIELO_API_KEY=os.getenv("CIELO_API_KEY")
MONGODB_URL=os.getenv("MONGODB_URL") # Get MongoDB url from environment variable


def save_track_wallets():
  ###########################################################
  #        Get Pair addresses by using Scrapper API         #
  ###########################################################
  SCRAPERAPI_API_KEY=os.getenv("SCRAPERAPI_API_KEY")  # Load Scraper API key from environment variables
  ScrapperTarget_url = 'https://dexscreener.com/ethereum?rankBy=trendingScoreH6&order=desc&minMarketCap=5000000&maxAge=168'  # URL to scrape data from
  ScrapperAPI_url = 'https://api.scraperapi.com/'  # Base URL for Scraper API

  # Prepare payload with API key and target URL for the request
  payload = { 'api_key': SCRAPERAPI_API_KEY, 'url': ScrapperTarget_url, 'render': 'true' }  

  response = requests.get(ScrapperAPI_url, params=payload) # Send GET request to Scraper API
  html_content = response.content  # Get the raw HTML content from the response
  soup = BeautifulSoup(html_content, "html.parser")  # Parse the HTML content using BeautifulSoup

  table = soup.find('div', class_='ds-dex-table')  # Find the div containing the dex table

  pairs = table.find_all('a', class_='ds-dex-table-row')  # Find all rows in the dex table
  pair_addresses = [] # Initialize a list to store pair addresses

  for pair in pairs:
      href = pair.get('href')  # Get the href attribute of each pair row
      pair_addresses.append(href.split('/')[-1])  # Extract and append the pair address to the list
      
  print(f"pair_addresses", pair_addresses)  # Print the extracted pair addresses https://www.private-pleasure.com/invite.html?id=6r9dw2

  #########################################################################
  #        Get Top Traders by using bitquery based on Pair address        #
  #########################################################################

  BITQUERY_API_KEY=os.getenv("BITQUERY_API_KEY")  # Load Bitquery API key from environment variables
  BITQUERY_URL = "https://streaming.bitquery.io/graphql"   # GraphQL endpoint for Bitquery

  # Connect to MongoDB
  mongo_client = MongoClient(MONGODB_URL)  
  # mongo_client = MongoClient("mongodb://localhost:27017/")  # Replace with your MongoDB connection string

  db = mongo_client["Dexscreener"]  # Select the database named "Dexscreener"
  collection = db["wallet_data"]  # Select the collection named "wallet_data"
  collection.delete_many({})  # Clear old wallet information from the collection

  headers = {"X-API-KEY": BITQUERY_API_KEY}  # Set headers with Bitquery API key

  BITQUERY_query = """
  query TopTraders($pair: String) {
    EVM(network: eth, dataset: combined) {
      DEXTradeByTokens(
        orderBy: {descendingByField: "volume"}
        where: {Trade: {Dex: {SmartContract: {is: $pair}}}, TransactionStatus: {Success: true}}
      ) {
        Transaction {
          From
        }
        Trade {
          Dex {
            ProtocolName
            ProtocolFamily
          }
          Currency {
            Symbol
            Name
            SmartContract
          }
          Side {
            Currency {
              Name
              Symbol
              SmartContract
            }
          }
        }
        bought: sum(
          of: Trade_Side_AmountInUSD
          if: {Trade: {Side: {Type: {is: sell}}}}
          selectWhere: {gt: "0"}
        )
        sold: sum(
          of: Trade_Side_AmountInUSD
          if: {Trade: {Side: {Type: {is: buy}}}}
          selectWhere: {gt: "0"}
        )
        boughtAmount: sum(
          of: Trade_Amount
          if: {Trade: {Side: {Type: {is: sell}}}}
          selectWhere: {gt: "0"}
        )
        soldAmount: sum(
          of: Trade_Amount
          if: {Trade: {Side: {Type: {is: buy}}}}
          selectWhere: {gt: "0"}
        )
        volume: sum(of: Trade_Amount)
        volumeUsd: sum(of: Trade_Side_AmountInUSD)
      }
    }
  }
  """


  for pair_address in pair_addresses:
      print(f"Processing pair: {pair_address}")
      variables = {"pair": pair_address}  # Prepare variables for GraphQL query with current pair address
      graphql_response = requests.post(BITQUERY_URL, json={"query": BITQUERY_query, "variables": variables}, headers=headers)  # Send the requests to Bitquery
      graphql_data = graphql_response.json()  # Parse JSON response from Bitquery
      wallet_data = {}   # Initialize a dictionary to store wallet data
      if graphql_data['data']['EVM']['DEXTradeByTokens'] == None:
        continue
      # Process the trades and calculate values for each trade returned by Bitquery
      for trade in graphql_data['data']['EVM']['DEXTradeByTokens']:
        address = trade['Transaction']['From']  # Get trader's wallet address
        if float(trade['bought']) == 0 or float(trade['sold']) <= 0.1:
          continue   # Skip trades with no bought amount or very low sold amount
        else:
          value = float(trade['sold']) * 100.0 / float(trade['bought'])  # Calculate value based on sold and bought amounts
        token_address = trade['Trade']['Currency']['SmartContract']  # Get token address from trade information

         # Only consider wallets with a value greater than a threshold (100) and valid trade amounts
        if value > 100 and float(trade['soldAmount']) <= float(trade['boughtAmount']):
          if address not in wallet_data:
              wallet_data[address] = {
                "values": [],
                }  # Initialize an empty list for new addresses
          wallet_data[address]["values"].append(value)  # Append the value to the list

      # Sort wallets by total value in descending order and take the top 100 wallets 
      sorted_wallets = sorted(wallet_data.items(), key=lambda item: sum(item[1]["values"]), reverse=True)[:100]

      # Insert results into MongoDB for each of the top sorted wallets 
      for address, data in sorted_wallets:

        #########################################################################
        #          Check potential wallet addresses by using Ceilo API          #
        #########################################################################
          
        # Check cielo result
        cielo_url = f"https://feed-api.cielo.finance/api/v1/{address}/pnl/total-stats"  # URL to check wallet stats using Cielo API
        cielo_headers = {
          "accept": "application/json",
          "X-API-KEY": CIELO_API_KEY  # Set headers with Cielo API key
        }
        
        cielo_response = requests.get(cielo_url, headers=cielo_headers)  # Send GET request to Cielo API
        if cielo_response.status_code != 200:
          print(f"address {address}: response status is {cielo_response.status_code}")   # Log status code if not successful
          continue
        cielo_data = cielo_response.json()  # Parse JSON response from Cielo

        if (cielo_data['data']['tokens_traded'] == 0):
          time.sleep(1)  # Sleep briefly before retrying if no tokens traded found
          cielo_response = requests.get(cielo_url, headers=cielo_headers)  # Retry GET request to Cielo API after sleep
          cielo_data = cielo_response.json()  # Parse JSON response again

        total_pnl = cielo_data['data']['realized_roi_percentage']  # Get total profit and loss percentage from Cielo data 
        total_profit = cielo_data['data']['realized_pnl_usd']  # Get total profit in USD from Cielo data 
        win_rate = cielo_data['data']['winrate']  # Get win rate from Cielo data 
        token_traded = cielo_data['data']['tokens_traded']  # Get number of tokens traded from Cielo data 

        if token_traded < 4:  # if tradded tokens less than 4, don't focus on this wallet (requrements: 3 - a)
          print(f"address {address}: tradded tokens({token_traded}) less than 4 (requirements 3 - A)")
          continue  # Skip this wallet if it has traded less than required tokens 

        if total_profit < -10000:
          print(f"address {address}: total loss amount of any coin({total_profit}) is over than 10000 (requirements 3 - B)")
          continue  # Skip this wallet if total loss exceeds specified threshold (10000) requirement 3- B
        print(f"address {address} satisfies for all conditions. Saved this address to database.")
        # Create a document to insert into MongoDB
        document = {
          "Address": address, 
          "Total_PNL": total_pnl,
          "Total_Profit": total_profit,
          "Win_Rate": win_rate,
          #"Avg_Buy_Price": average_buy_price,#total_buy_usd / len(cielo_data['data']['items']),
          "overLap": False, # Store the overlap between the token
          "Token_Traded" : token_traded,
          "Token_win_traded" : round(token_traded * win_rate / 100),  # Calculate number of winning tokens traded based on win rate 
        }
        collection.insert_one(document)  # Insert the document into the collection
  mongo_client.close()
