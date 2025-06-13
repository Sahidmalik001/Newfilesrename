import asyncio
from pyrogram import Client, filters, enums
from pyrogram.enums import MessageMediaType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply

from helper.utils import progress_for_pyrogram, convert, humanbytes
from helper.database import db
import time
import os


@Client.on_callback_query(filters.regex('rename'))
async def rename(bot, update):
    user_id = update.data.split('-')[1]

    if int(user_id) not in [update.from_user.id, 0]:
        return await update.answer(f"⚠️ Hᴇʏ {update.from_user.first_name}\nTʜɪs ɪs ɴᴏᴛ ʏᴏᴜʀ ғɪʟᴇ ʏᴏᴜ ᴄᴀɴ'ᴛ ᴅᴏ ᴀɴʏ ᴏᴘᴇʀᴀᴛɪᴏɴ", show_alert=True)

    await update.message.delete()
    await update.message.reply_text(
        "__𝙿𝚕𝚎𝚊𝚜𝚎 𝙴𝚗𝚝𝚎𝚛 𝙽𝚎𝚠 𝙵𝚒𝚕𝚎𝙽𝚊𝚖𝚎...__",
        reply_to_message_id=update.message.reply_to_message.id,
        reply_markup=ForceReply(True)
    )


@Client.on_message((filters.private | filters.group) & filters.reply)
async def refunc(client, message):
    reply_message = message.reply_to_message
    if (reply_message.reply_markup) and isinstance(reply_message.reply_markup, ForceReply):
        new_name = message.text
        await message.delete()
        msg = await client.get_messages(message.chat.id, reply_message.id)
        file = msg.reply_to_message
        media = getattr(file, file.media.value)

        if not "." in new_name:
            if "." in media.file_name:
                extn = media.file_name.rsplit('.', 1)[-1]
            else:
                extn = "mkv"
            new_name = new_name + "." + extn

        await reply_message.delete()

        button = [[InlineKeyboardButton("📁 Dᴏᴄᴜᴍᴇɴᴛ", callback_data="upload_document")]]
        if file.media in [MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]:
            button.append([InlineKeyboardButton("🎥 Vɪᴅᴇᴏ", callback_data="upload_video")])
        elif file.media == MessageMediaType.AUDIO:
            button.append([InlineKeyboardButton("🎵 Aᴜᴅɪᴏ", callback_data="upload_audio")])

        await message.reply_text(
            text=f"<b>Sᴇʟᴇᴄᴛ Tʜᴇ Oᴜᴛᴩᴜᴛ Fɪʟᴇ Tyᴩᴇ</b>\n<b>• Fɪʟᴇ Nᴀᴍᴇ :-</b><code>{new_name}</code>",
            reply_to_message_id=file.id,
            reply_markup=InlineKeyboardMarkup(button)
        )


@Client.on_callback_query(filters.regex("upload"))
async def doc(bot, update):
    new_name = update.message.text.split(":-")[1].strip()
    file_path = f"Renames/{new_name}"
    file = update.message.reply_to_message

    ms = await update.message.edit("⚠️ __**Please wait...**__\n**Tʀyɪɴɢ Tᴏ Dᴏᴡɴʟᴏᴀᴅ....**")
    try:
        dl = await bot.download_media(
            message=file,
            file_name=file_path,
            progress=progress_for_pyrogram,
            progress_args=(
                "\n⚠️ __**Please wait...**__\n\n☃️ **Dᴏᴡɴʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ....**", ms, time.time()
            )
        )
    except Exception as e:
        return await ms.edit(str(e))

    user_id = update.from_user.id
    media = getattr(file, file.media.value)
    duration = getattr(media, "duration", 0)
    c_caption = await db.get_caption(user_id)
    c_thumb = await db.get_thumbnail(user_id)

    if c_caption:
        try:
            caption = c_caption.format(
                filename=new_name,
                filesize=humanbytes(media.file_size),
                duration=convert(duration)
            )
        except Exception as e:
            return await ms.edit(text=f"Yᴏᴜʀ Cᴀᴩᴛɪᴏɴ Eʀʀᴏʀ ●> ({e})")
    else:
        caption = f"**{new_name}**"

    ph_path = None
    if media.thumbs or c_thumb:
        try:
            if c_thumb:
                ph_path = await bot.download_media(c_thumb)
            else:
                ph_path = await bot.download_media(media.thumbs[0].file_id)
        except:
            ph_path = None

    await ms.edit("⚠️ __**Please wait...**__\n🌨️ **Uᴘʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ....**")
    type = update.data.split("_")[1]
    try:
        if type == "document":
            await bot.send_document(
                update.from_user.id,
                document=file_path,
                thumb=ph_path,
                caption=caption,
                progress=progress_for_pyrogram,
                progress_args=("⚠️ __**Please wait...**__\n🌨️ **Uᴘʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ....**", ms, time.time())
            )
        elif type == "video":
            await bot.send_video(
                update.from_user.id,
                video=file_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("⚠️ __**Please wait...**__\n🌨️ **Uᴘʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ....**", ms, time.time())
            )
        elif type == "audio":
            await bot.send_audio(
                update.from_user.id,
                audio=file_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("⚠️ __**Please wait...**__\n🌨️ **Uᴘʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ....**", ms, time.time())
            )
    except Exception as e:
        try:
            os.remove(file_path)
            if ph_path:
                os.remove(ph_path)
        except:
            pass
        return await ms.edit(f"❌ Eʀʀᴏʀ: {e}")

    try:
        os.remove(file_path)
        if ph_path:
            os.remove(ph_path)
    except:
        pass

    if update.message.chat.type == enums.ChatType.SUPERGROUP:
        botusername = await bot.get_me()
        await ms.edit(
            f"Hey {update.from_user.mention},\n\nI Have Sent The Renamed File To Your PM.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text="🤖 Open PM", url=f'https://t.me/{botusername.username}')]
            ])
        )
    else:
        await ms.delete()
