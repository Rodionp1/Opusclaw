import asyncio
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

from src.sessions import load_session, append_message, save_session

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Phase 1: Simple chat with session memory."""
    user_id = str(update.effective_user.id)
    session_key = f"session_{user_id}"
    
    # Load conversation history
    messages = load_session(session_key)
    
    # Add user message
    user_msg = {"role": "user", "content": update.message.text}
    messages.append(user_msg)
    append_message(session_key, user_msg)
    
    # Call Claude (simple API, no tools yet)
    from anthropic import AsyncAnthropic
    client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_KEY"))
    
    # Load SOUL
    soul_path = "agents/main/SOUL.md"
    if os.path.exists(soul_path):
        with open(soul_path, "r") as f:
            system_prompt = f.read()
    else:
        system_prompt = "You are a helpful AI assistant."
    
    response = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        system=system_prompt,
        messages=messages
    )
    
    assistant_text = response.content[0].text
    
    # Save assistant response
    assistant_msg = {"role": "assistant", "content": assistant_text}
    append_message(session_key, assistant_msg)
    
    await update.message.reply_text(assistant_text)


def main():
    if not TELEGRAM_TOKEN:
        print("Error: Set TELEGRAM_TOKEN in .env")
        return
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("OpusClaw Phase 1 running...")
    print("Features: Sessions + SOUL.md personality")
    app.run_polling()


if __name__ == "__main__":
    main()