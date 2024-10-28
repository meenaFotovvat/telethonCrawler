import json
from fastapi import FastAPI, HTTPException
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import GetHistoryRequest
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

# Initialize the FastAPI app
app = FastAPI()

# Access environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
phone_number = os.getenv("PHONE_NUMBER")  # Store phone number in .env for security

# Initialize the Telethon client
client = TelegramClient('bookNook', API_ID, API_HASH)

# Define the Telegram scraping function
async def scrape_telegram_channels(channels):
    all_data = {}

    for channel in channels:
        try:
            # Fetch channel entity
            channel_entity = await client.get_entity(channel)

            # Get message history from the channel
            messages = await client(GetHistoryRequest(
                peer=channel_entity,
                offset_id=0,
                offset_date=None,
                add_offset=0,
                limit=100,         # Number of messages to retrieve
                max_id=0,
                min_id=0,
                hash=0
            ))

            # Process each message
            data = []
            for message in messages.messages:
                data.append({
                    'message_id': message.id,
                    'text': message.message,
                    'date': str(message.date),
                    'sender_id': message.from_id.user_id if message.from_id else None
                })

            # Save data for the current channel
            all_data[channel] = data

        except Exception as e:
            print(f"Failed to scrape channel {channel}: {e}")

    # Return JSON-formatted data
    return all_data

# Define the FastAPI route that Metis will call
@app.get("/fetch_telegram_data")
async def fetch_telegram_data():
    # Channels to scrape
    channels = ['@chiro_chanel', '@Tajrobeh_home', '@Khaneh_Agahi1']
    
    # Start the Telegram client and scrape channels
    await client.start(phone_number)
    if await client.is_user_authorized():
        data = await scrape_telegram_channels(channels)
        await client.disconnect()
        return data
    else:
        await client.disconnect()
        raise HTTPException(status_code=401, detail="Unauthorized access to Telegram API.")
