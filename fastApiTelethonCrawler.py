import base64
import os
import logging
from fastapi import FastAPI, HTTPException
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import GetHistoryRequest
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from io import BytesIO

logging.basicConfig(level=logging.INFO)
load_dotenv()  # Load environment variables from .env file

app = FastAPI()

# Access environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
phone_number = os.getenv("PHONE_NUMBER")
encryption_key_b64 = os.getenv("ENCRYPTION_KEY")  # Base64-encoded encryption key

# Decode Base64 encryption key
encryption_key = base64.b64decode(encryption_key_b64)

# Define path to the session file on the mounted disk
disk_mount_path = "/var/lib/data/booknook"  # Change this if your Disk is mounted elsewhere
encrypted_session_file_path = os.path.join(disk_mount_path, "bookNook_session.session.enc")

# Decrypt session file from the mounted Disk
def decrypt_session_file(file_path, key):
    fernet = Fernet(key)
    with open(file_path, "rb") as encrypted_file:
        encrypted_data = encrypted_file.read()
    decrypted_data = fernet.decrypt(encrypted_data)
    return BytesIO(decrypted_data)  # Return a file-like object for Telethon to use

# Initialize the decrypted session file content as a BytesIO stream
session_file_stream = decrypt_session_file(encrypted_session_file_path, encryption_key)

# Initialize the Telethon client using the decrypted session content
client = TelegramClient(session_file_stream, API_ID, API_HASH)

# Define the Telegram scraping function (same as before)
async def scrape_telegram_channels(channels):
    all_data = {}
    for channel in channels:
        try:
            logging.info(f"Fetching entity for channel: {channel}")
            channel_entity = await client.get_entity(channel)

            logging.info(f"Fetching message history for channel: {channel}")
            messages = await client(GetHistoryRequest(
                peer=channel_entity,
                offset_id=0,
                offset_date=None,
                add_offset=0,
                limit=50,
                max_id=0,
                min_id=0,
                hash=0
            ))

            data = []
            for message in messages.messages:
                data.append({
                    'message_id': message.id,
                    'text': message.message,
                    'date': str(message.date),
                    'sender_id': message.from_id.user_id if message.from_id else None
                })

            all_data[channel] = data
            logging.info(f"Scraping completed for channel: {channel}")

        except Exception as e:
            logging.error(f"Failed to scrape channel {channel}: {e}")
            raise HTTPException(status_code=500, detail=f"Error scraping channel {channel}: {e}")

    return all_data

@app.get("/fetch_telegram_data")
async def fetch_telegram_data():
    channels = ['@chiro_chanel', '@Tajrobeh_home', '@Khaneh_Agahi1']
    
    try:
        await client.start(phone_number)
        
        if await client.is_user_authorized():
            data = await scrape_telegram_channels(channels)
            await client.disconnect()
            return data
        else:
            await client.disconnect()
            raise HTTPException(status_code=401, detail="Unauthorized access to Telegram API.")
    
    except SessionPasswordNeededError:
        await client.disconnect()
        raise HTTPException(status_code=403, detail="Two-factor authentication is required for this account.")
    except Exception as e:
        logging.error(f"Error in fetch_telegram_data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch telegram data.")
