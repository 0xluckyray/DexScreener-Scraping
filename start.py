# Import necessary functions from other modules
from save import save_track_wallets
from track import track_wallets
from saveTime import save_Time

import time

while True:  # Infinite loop to repeatedly execute the following actions
  save_Time()   # Call function to save the current time
  # save_track_wallets()   # Call function to save tracked wallets to mongodb Atlas
  track_wallets()   # Call function to start tracking wallets from their transactions
  time.sleep(259200)  # Pause execution for 259200 seconds (3 days) before repeating