from asyncio import sleep
import pandas as pd
import requests
from dotenv import load_dotenv
import os
load_dotenv()

# Load the Excel file
file_path = "tq-part.xlsx"
excel_data = pd.ExcelFile(file_path)

# Define the Discord webhook URL
webhook_url = os.getenv("WEBHOOK_URL") or "https://discord.com/api/webhooks/1234567890/ABCDEFGHIJKL"

# Function to send data via Discord webhook
def send_to_discord(name, email, team_id):
    message = f"!register {name} {email} {team_id}"
    data = {"content": message}
    response = requests.post(webhook_url, json=data)
    if response.status_code == 204:
        print(f"Successfully sent: {message}")
    else:
        print(f"Failed to send: {message} - Status code: {response.status_code}")

# Iterate over each sheet and send data to Discord
for sheet_name in excel_data.sheet_names:
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # Drop rows with missing values in any of the required columns
    df = df.dropna(subset=['Name', 'Email ID', 'Team name'])
    
    for _, row in df.iterrows():
        name = row['Name']
        email = row['Email ID']
        team_id = row['Team name']
        send_to_discord(name, email, team_id)
        sleep(1)  # Sleep for 1 second to avoid rate limiting
