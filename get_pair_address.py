import requests
import dotenv
import os

dotenv.load_dotenv()
BITQUERY_API_KEY=os.getenv("BITQUERY_API_KEY")

def run_query(query, variables):
    # Set the API endpoint and headers
    url = "https://graphql.bitquery.io/"  # GraphQL API endpoint for Bitquery
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": BITQUERY_API_KEY  
    }

    # Create the payload for the request
    payload = {
        "query": query,  # The GraphQL query to be executed
        "variables": variables  # Variables to be used in the query
    }

    # Make the request to Bitquery API
    response = requests.post(url, json=payload, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        return response.json()   # Return the JSON response from the API
    else:
        raise Exception(f"Query failed with code {response.status_code}: {response.text}")  # Raise an error if the request fails

# Define your GraphQL query
query = """
query ($address: String!, $other: String!) {
  ethereum(network: ethereum) {
    dexTrades(
      options: {limit: 1, desc: "block.height"}
      baseCurrency: {is: $address}
      quoteCurrency: {is: $other}
    ) {
      smartContract {
        address {
          address
        }
      }
      block {
        height
      }
    }
  }
}
"""
def get_pair_address(token1, token2):
  # Define your variables for the GraphQL query
  variables = {
    "address": token1,  # Basic token address
    "other": token2  # Quote token address
  }
  result = run_query(query, variables)  # Execute the GraphQL query with defined variables
  trades = result.get('data', {}).get('ethereum', {}).get('dexTrades', [])  # Extract trades from the result
  if trades:
    smart_contract_address = trades[0]['smartContract']['address']['address']  # Get smart contract address from first trade
    return smart_contract_address # Return the smart contract address (pair address)
  else:
    print("No trades found for the given token addresses.")  # Log message if no trades were found