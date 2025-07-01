import os
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, error
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from credentials import telegram_api_token
import asyncio
import hashlib


# Directory paths
INPUT_DIR = "telegram_audios/input"
OUTPUT_DIR = "telegram_audios/output"
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

WELCOME_MESSAGE = (
    "Welcome to the Voice Transformation Bot! 🎙️\n\n"
    "Send me an audio file, and I'll transform the voice for you. "
    "After sending the audio, you'll be able to select which model to use for the transformation."
)

# List of available voices with speaker embeddings and model checkpoints
AVAILABLE_VOICES = {
    "Messi": {
        "embedding": "speaker_embeddings/messi_emb.pt",
        "checkpoint": "checkpoints/messi/G_1000.pth"
    }
}
# Start command
async def start(update: Update, context):
    await update.message.reply_text(WELCOME_MESSAGE)

# Handle text messages
async def handle_text(update: Update, context):
    try:
        await update.message.reply_text("Send me an audio file, and I'll transform the voice for you!")
    except error.Forbidden:
        # Handle the case where the bot is blocked by the user
        print(f"Bot was blocked by the user: {update.message.from_user.id}")


# Handle audio files
CALLBACK_DATA_MAP = {}  # To store callback data and its corresponding file paths
async def handle_audio(update: Update, context):
    file = update.message.voice or update.message.audio
    if not file:
        await update.message.reply_text("Please send a valid audio file.")
        return

    # Get user-specific directory
    user_id = update.message.from_user.username or str(update.message.from_user.id)
    user_input_dir = os.path.join(INPUT_DIR, user_id)
    user_output_dir = os.path.join(OUTPUT_DIR, user_id)
    os.makedirs(user_input_dir, exist_ok=True)
    os.makedirs(user_output_dir, exist_ok=True)

    print(f'Recieved audio from {user_id}')

    # Save the audio file
    file_path = os.path.join(user_input_dir, f"{update.message.from_user.id}.wav")
    file_obj = await file.get_file()
    await file_obj.download_to_drive(file_path)

    # Generate a unique identifier for the callback data
    def generate_callback_data(file_path, embedding, checkpoint):
        data_string = f"{file_path}|{embedding}|{checkpoint}"
        callback_hash = hashlib.md5(data_string.encode()).hexdigest()
        CALLBACK_DATA_MAP[callback_hash] = (file_path, embedding, checkpoint)  # Store the mapping
        return callback_hash

    # Show available voices
    keyboard = [
        [InlineKeyboardButton(
            name,
            callback_data=generate_callback_data(file_path, data['embedding'], data['checkpoint'])
        )]
        for name, data in AVAILABLE_VOICES.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose a voice to transform to:", reply_markup=reply_markup)


# Handle voice selection
async def handle_voice_selection(update: Update, context):
    query = update.callback_query
    try:
        # Respond to the callback query immediately with a cache time
        await query.answer(cache_time=10)  # Cache the response for 10 seconds to avoid repeated errors
    except error.BadRequest as e:
        print(f"Failed to answer callback query: {e}")
        return

    # Retrieve the original data using the hash
    callback_hash = query.data
    if callback_hash not in CALLBACK_DATA_MAP:
        await query.edit_message_text("Invalid selection.")
        return

    input_path, embedding_path, checkpoint_path = CALLBACK_DATA_MAP[callback_hash]
    user_id = os.path.basename(os.path.dirname(input_path))  # Extract user ID from input path
    user_output_dir = os.path.join(OUTPUT_DIR, user_id)
    output_path = os.path.join(user_output_dir, f"{os.path.basename(input_path).split('.')[0]}_transformed.wav")

    # Inform the user that processing has started
    await query.edit_message_text("Processing audio...")

    # Run the conversion script in the background
    async def run_conversion():
        try:
            subprocess.run(
                [
                    "python", "convert.py",
                    "--ptfile", checkpoint_path,
                    "--outdir", user_output_dir,
                    "--input_audio", input_path,
                    "--saved_embedding", embedding_path
                ],
                check=True
            )
            print('Voice transformation completed successfully.')

            # Check if the message content is different before editing
            current_message = query.message.text
            new_message = "Voice transformation complete! Sending the transformed audio..."
            if current_message != new_message:
                await query.edit_message_text(new_message)

            # Send transformed audio
            with open(output_path, "rb") as audio_file:
                # await query.message.reply_audio(audio_file)
                await query.message.reply_voice(audio_file)
        except subprocess.CalledProcessError:
            await query.edit_message_text("An error occurred during voice transformation.")
        except FileNotFoundError:
            await query.edit_message_text("Output file not found. Please check the conversion script.")

    asyncio.create_task(run_conversion())


# Main function
def main():

    print('Voice Clone bot is up!')

    # Create the application
    application = Application.builder().token(telegram_api_token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT, handle_text))  # Respond to text messages
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_audio))
    application.add_handler(CallbackQueryHandler(handle_voice_selection))

    # Run the bot with proper event loop handling
    try:
        asyncio.run(application.run_polling())
    except RuntimeError as e:
        if str(e) == "Event loop is closed":
            # Recreate the event loop if it is closed
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(application.run_polling())

if __name__ == "__main__":
    main()