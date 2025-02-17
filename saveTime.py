# Import necessary libraries
from pymongo import MongoClient
from datetime import datetime, timedelta
import dotenv
import os

MONGODB_URL=os.getenv("MONGODB_URL") # Get MongoDB url from environment variable

def save_Time():
  utc_now = datetime.utcnow() - timedelta(hours=7)   # Get the current UTC time and adjust it to a specific timezone (UTC-7)
  seven_days_ago = utc_now - timedelta(days=7)   # Calculate the time for seven days ago from the current adjusted time

  # Connect to MongoDB database
  mongo_client = MongoClient(MONGODB_URL)  # Replace with your MongoDB connection string
  # mongo_client = MongoClient("mongodb://localhost:27017/")  # Replace with your MongoDB connection string
  db = mongo_client["Dexscreener"]  # Select the database named "Dexscreener"
  collection1 = db["trackedTime"]  # Select the collection named "trackedTime"
  collection1.delete_many({})   # Delete all documents in the trackedTime collection to initialize old wallet information

   # Create a document to store the start and end times for tracking
  document1 = {
    "startTime": seven_days_ago,  # Set start time as seven days ago
    "endTime": utc_now,  # Set end time as the current adjusted time
  }
  try:
    result = collection1.insert_one(document1)  # Attempt to insert the document into the collection
    print(f"Saved tracking time.")  # Log success message
  except Exception as e:
    print(f"An error occurred: {e}")  # Log any error that occurs during insertion
  mongo_client.close()   # Close the connection to the MongoDB database