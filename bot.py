import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
BOT_TOKEN = 'BOT_TOKEN'

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Dictionary to store group activity timestamps and information
group_activity = {}

# Notify in terminal when the bot starts
async def start_notification(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Bot is now running and logged in!")

# Send a welcome message when the bot is added to a group
async def welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        await update.message.reply_text("Thank you for adding me to the group!")
        logger.info(f"Bot added to group: {chat.title} (ID: {chat.id})")
        # Initialize group activity timestamp and store group info
        group_activity[chat.id] = {
            "title": chat.title,
            "username": chat.username,  # Store group username (if available)
            "last_active": datetime.now(),
        }

# Check group inactivity
async def check_inactivity(context: ContextTypes.DEFAULT_TYPE):
    current_time = datetime.now()
    inactive_groups = []

    for chat_id, data in list(group_activity.items()):
        last_active = data["last_active"]
        if current_time - last_active > timedelta(minutes=1):  # 1 minute of inactivity (for testing)
            inactive_groups.append((chat_id, data["title"], data.get("username")))

    if inactive_groups:
        # Create a message listing inactive groups
        message = "The following groups have been inactive for a while:\n\n"
        for chat_id, title, username in inactive_groups:
            message += f"- {title}\n"

        # Add buttons for each inactive group
        keyboard = [
            [InlineKeyboardButton(f"Keep {title}", callback_data=f"keep_{chat_id}"),
             InlineKeyboardButton(f"Delete {title}", callback_data=f"delete_{chat_id}")]
            for chat_id, title, _ in inactive_groups
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the message to the user
        await context.bot.send_message(
            chat_id=context.job.chat_id,  # Send to the user who started the bot
            text=message,
            reply_markup=reply_markup,
        )
        logger.info(f"Listed inactive groups to user.")

# Handle button clicks
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_response = query.data
    chat_id = int(user_response.split("_")[1])  # Extract group ID from callback data
    action = user_response.split("_")[0]  # Extract action (keep or delete)

    if action == "keep":
        # Reset the activity timer for the group
        group_activity[chat_id]["last_active"] = datetime.now()
        await query.answer(f"Okay, I'll keep the group: {group_activity[chat_id]['title']}.")
        logger.info(f"User chose to keep group {chat_id}.")
    elif action == "delete":
        # Generate the correct group link
        group_info = group_activity[chat_id]
        print(chat_id)
        print(group_info)
        group_link = (
            f"https://web.telegram.org/a/#{chat_id}"  # Use username if available
            if group_info.get("title")
            else f"tg://resolve?domain={chat_id}"  # Fallback to group ID
        )
        await query.answer(f"Click the link below to leave the group: {group_info['title']}")
        await query.edit_message_text(
            f"To leave the group '{group_info['title']}', please click this link and manually leave:\n{group_link}\n\n"
            "Steps to delete the group:\n"
            "1. Open the group info.\n"
            "2. Tap on 'Delete Group'.\n"
            "3. Confirm the deletion."
        )
        logger.info(f"User chose to delete group {chat_id}.")

# Command handler for /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(f"Hello {user.first_name}! I'm happy you selected me. I'll help you manage your groups.")
    logger.info(f"User {user.id} started the bot.")

    # Schedule the inactivity checker to run every minute (for testing)
    context.job_queue.run_repeating(check_inactivity, interval=60, first=0, chat_id=user.id)

# Main function to start the bot
def main():
    # Create the Application and pass it your bot's token
    application = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_message))
    application.add_handler(CallbackQueryHandler(button_click))  # Handle button clicks

    # Notify when the bot starts
    application.run_polling()
    logger.info("Bot started and polling for updates...")

if __name__ == '__main__':
    main()