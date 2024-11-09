import json
import logging
from fastapi import FastAPI, HTTPException
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import GetHistoryRequest
from dotenv import load_dotenv
import os
from cryptography.fernet import Fernet

logging.basicConfig(level=logging.INFO)

load_dotenv()  # Load environment variables from .env file

app = FastAPI()

# Access environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
phone_number = os.getenv("PHONE_NUMBER")

# Generate encryption key if it doesn't exist
if not os.path.exists("encryption_key.key"):
    key = Fernet.generate_key()
    with open("encryption_key.key", "wb") as key_file:
        key_file.write(key)
else:
    # Load the existing encryption key
    with open("encryption_key.key", "rb") as key_file:
        key = key_file.read()

# Initialize encryption key
def load_key():
    return key  # Use the key already loaded or generated

# Encryption functions
def decrypt_session_file(file_path, key):
    fernet = Fernet(key)
    with open(file_path, "rb") as encrypted_file:
        encrypted_data = encrypted_file.read()
    decrypted_data = fernet.decrypt(encrypted_data)
    
    decrypted_file_path = file_path.replace(".enc", "")
    with open(decrypted_file_path, "wb") as decrypted_file:
        decrypted_file.write(decrypted_data)
    
    return decrypted_file_path

def encrypt_session_file(file_path, key):
    fernet = Fernet(key)
    with open(file_path, "rb") as decrypted_file:
        original_data = decrypted_file.read()
    
    encrypted_data = fernet.encrypt(original_data)
    encrypted_file_path = file_path + ".enc"
    with open(encrypted_file_path, "wb") as encrypted_file:
        encrypted_file.write(encrypted_data)
    
    return encrypted_file_path

# Decrypt session file before using it in TelegramClient
session_file_path = "bookNook_session.session.enc"
if os.path.exists(session_file_path):
    decrypted_session_file_path = decrypt_session_file(session_file_path, load_key())
else:
    decrypted_session_file_path = "bookNook_session.session"  # Start a new session if the file doesn't exist

# Initialize the Telethon client with the decrypted session file
client = TelegramClient(decrypted_session_file_path, API_ID, API_HASH)

# Define the Telegram scraping function
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

            # Encrypt the session file again after disconnecting
            encrypt_session_file(decrypted_session_file_path, load_key())
            os.remove(decrypted_session_file_path)  # Clean up the decrypted session file
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
