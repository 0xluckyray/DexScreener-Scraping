import requests
import dotenv
import os

dotenv.load_dotenv()
BITQUERY_API_KEY=os.getenv("BITQUERY_API_KEY")

# Define the GraphQL endpoint
url = "https://streaming.bitquery.io/graphql"

def get_liquidity(pair, token1, token2, other):
    # Define your GraphQL query
    query = """
    {
      EVM(dataset: archive, network: eth) {
        token1Balance: BalanceUpdates(
          where: {
            BalanceUpdate: {
              Address: {
                is: "%s"
              }
            }
            Currency: { SmartContract: { is: "%s" } }
          }
          orderBy: { descendingByField: "balance" }
        ) {
          Currency {
            Name
          }
          balance: sum(of: BalanceUpdate_Amount)
          BalanceUpdate {
            Address
          }
        }

        token2Balance: BalanceUpdates(
          where: {
            BalanceUpdate: {
              Address: {
                is: "%s"
              }
            }
            Currency: { SmartContract: { is: "%s" } }
          }
          orderBy: { descendingByField: "balance" }
        ) {
          Currency {
            Name
          }
          balance: sum(of: BalanceUpdate_Amount)
          BalanceUpdate {
            Address
          }
        }

        TokenHolders(
          date: "2025-10-21"
          tokenSmartContract: "%s"
          where: {Balance: {Amount: {gt: "0"}}}
        ) {
          uniq(of: Holder_Address)
        }
      }
    }
    """

    # Set headers if needed (e.g., for authentication)
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": BITQUERY_API_KEY  # Your API key
    }

    # Format the query with the current pair and token
    formatted_query = query % (pair, token1, pair, token2, other)

    # Make the request
    response = requests.post(url, json={'query': formatted_query}, headers=headers)

    # Check for a successful response
    if response.status_code == 200:
        data = response.json()
        print(f"Liquidity and Holder Count Data for Pair {pair} and Token {other}:")
        print(data)
        return data
    else:
        print(f"Query failed with status code {response.status_code}: {response.text}")
