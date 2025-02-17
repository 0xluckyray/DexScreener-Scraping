import requests

def get_total_supply(contract_address, etherscan_api_key):
    url = 'https://api.etherscan.io/api'  # Base URL for Etherscan API

    # Set parameters including the contract address and your API key
    params = {
        'module': 'stats',  # Specify the module to access token statistics
        'action': 'tokensupply',  # Specify the action to get token supply
        'contractaddress': contract_address,  # The contract address of the token
        'apikey': etherscan_api_key
    }

    # Make the request to the Etherscan API
    response = requests.get(url, params=params)  # Send GET request with parameters

    # Check if request was successful
    if response.status_code == 200:
        data = response.json()
        if data['status'] == '1':  # Check if the status indicates success
            return int(data['result'])  # Return the total supply as an integer (adjust for token decimals if needed)
        else:
            raise Exception(f"Error: {data['message']}")  # Raise an error with message from API response
    else:
        raise Exception(f"Error: Unable to connect to Etherscan. Status code: {response.status_code}")  # Raise an error if connection fails
