from time import sleep
from telegram import InlineKeyboardMarkup
from telegram.message import Message
from telegram.error import RetryAfter
from pyrogram.errors import FloodWait
from pyrogram import enums

from bot import AUTO_DELETE_MESSAGE_DURATION, LOGGER, status_reply_dict, status_reply_dict_lock, Interval, DOWNLOAD_STATUS_UPDATE_INTERVAL, bot

from bot.modules.helper_funcs.mirror_helpers.bot_utils import get_readable_message, setInterval


def sendMessage(text: str, bot, message: Message):
    try:
        return bot.sendMessage(
            message.chat_id,
            reply_to_message_id=message.message_id,
            text=text,
            allow_sending_without_reply=True,
            parse_mode="HTMl",
            disable_web_page_preview=True)
    except RetryAfter as r:
        LOGGER.warning(str(r))
        sleep(r.retry_after * 1.5)
        return sendMessage(text, bot, message)
    except Exception as e:
        LOGGER.error(str(e))
        return


def sendMarkup(text: str, bot, message: Message, reply_markup: InlineKeyboardMarkup):
    try:
        return bot.sendMessage(
            message.chat_id,
            reply_to_message_id=message.message_id,
            text=text,
            reply_markup=reply_markup,
            allow_sending_without_reply=True,
            parse_mode="HTMl",
            disable_web_page_preview=True)
    except RetryAfter as r:
        LOGGER.warning(str(r))
        sleep(r.retry_after * 1.5)
        return sendMarkup(text, bot, message, reply_markup)
    except Exception as e:
        LOGGER.error(str(e))
        return


def editMessage(text: str, message: Message, reply_markup=None):
    try:
        bot.editMessageText(
            text=text,
            message_id=message.message_id,
            chat_id=message.chat.id,
            reply_markup=reply_markup,
            parse_mode="HTMl",
            disable_web_page_preview=True)
    except RetryAfter as r:
        LOGGER.warning(str(r))
        sleep(r.retry_after * 1.5)
        return editMessage(text, message, reply_markup)
    except Exception as e:
        LOGGER.error(str(e))
        return

def sendSpeedTestMessage(text: str, bot, message: Message, link):
    try:
        return bot.sendPhoto(
            chat_id=message.chat.id,
            photo = link,
            caption = text,
            reply_to_message_id = message.message_id,
            parse_mode="HTML",
            filename = "speedrun.png")
    except RetryAfter as r:
        LOGGER.warning(str(r))
        sleep(r.retry_after * 1.5)
        return sendSpeedTestMessage(text, bot, message, link)
    except Exception as e:
        LOGGER.error(str(e))
        return

def deleteMessage(bot, message: Message):
    try:
        bot.deleteMessage(chat_id=message.chat.id, message_id=message.message_id)
    except Exception as e:
        LOGGER.error(str(e))


def sendLogFile(bot, message: Message):
    with open("log.txt", "rb") as f:
        bot.sendDocument(
            document=f,
            filename=f.name,
            reply_to_message_id=message.message_id,
            chat_id=message.chat_id)


def auto_delete_message(bot, cmd_message: Message, bot_message: Message):
    if AUTO_DELETE_MESSAGE_DURATION != -1:
        sleep(AUTO_DELETE_MESSAGE_DURATION)
        try:
            # Skip if None is passed meaning we don't want to delete bot xor cmd message
            deleteMessage(bot, cmd_message)
            deleteMessage(bot, bot_message)
        except AttributeError:
            pass


def delete_all_messages():
    with status_reply_dict_lock:
        for message in list(status_reply_dict.values()):
            try:
                deleteMessage(bot, message)
                del status_reply_dict[message.chat.id]
            except Exception as e:
                LOGGER.error(str(e))


def update_all_messages():
    msg, buttons = get_readable_message()
    with status_reply_dict_lock:
        for chat_id in list(status_reply_dict.keys()):
            if status_reply_dict[chat_id] and msg != status_reply_dict[chat_id].text:
                if buttons == "":
                    editMessage(msg, status_reply_dict[chat_id])
                else:
                    editMessage(msg, status_reply_dict[chat_id], buttons)
                status_reply_dict[chat_id].text = msg


def sendStatusMessage(msg, bot):
    if len(Interval) == 0:
        Interval.append(
            setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages))
    progress, buttons = get_readable_message()
    with status_reply_dict_lock:
        if msg.chat.id in list(status_reply_dict.keys()):
            try:
                message = status_reply_dict[msg.chat.id]
                deleteMessage(bot, message)
                del status_reply_dict[msg.chat.id]
            except Exception as e:
                LOGGER.error(str(e))
                del status_reply_dict[msg.chat.id]
        if buttons == "":
            message = sendMessage(progress, bot, msg)
        else:
            message = sendMarkup(progress, bot, msg, buttons)
        status_reply_dict[msg.chat.id] = message