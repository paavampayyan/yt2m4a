from pyrogram import Client, filters
from pytube.extract import video_id
import youtube_dl
from youtube_search import YoutubeSearch
import requests
from googleapiclient.discovery import build
from pprint import pprint
import time
from pytube import YouTube, exceptions
import os
from config import Config
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

api_key = 'AIzaSyBxBsDDW4xdLP0C86Q4XTUXSntARkdTZYw'
ytregex = r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"

youtube = build('youtube', 'v3', developerKey=api_key)
psycho = 1445436774

ydl_opts = {'format': 'bestaudio[ext=m4a]',
    'external_downloader':"aria2c",
    'verbose':True,}

bot = Client(
    'yt2m4a',
    bot_token = Config.BOT_TOKEN,
    api_id = Config.API_ID,
    api_hash = Config.API_HASH
)

## Extra Fns -------------------------------

# Convert hh:mm:ss to seconds
def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(':'))))


## Commands --------------------------------
@bot.on_message(filters.command(['start']))
def start(client, message):
    message.reply_text('👋 Hi, this is our new bot that we built to download non-copyrighted songs. So you can only download songs from some of the channels we mentioned, and you can also download the song that the publisher added "Copyright Free" to their video description.'
                       '\n\n『 Channels Available 』'
                       '\n 1. [NoCopyrightSongs Hindi](https://www.youtube.com/channel/UCg-vlcyvOyNVPV6Neogmubg)'
                       '\n 2. [NoCopyrightSounds](https://www.youtube.com/user/NoCopyrightSounds)'
                       '\n 3. [No Copyright Music -MALAYALAM ARENA](https://www.youtube.com/channel/UCYJgoH4eHQ6kzKbRWsJJfGQ)'
                       '\n 4. [NO COPYRIGHT BGM TAMIL](https://www.youtube.com/channel/UCWUlb09YbWMm5rFvS9rGg2g)'
                       '\n\n『 How To Request Song? 』'
                       '\n Just type `/song` - song name or copy paste video link.')

@bot.on_message(filters.command(['song']))
def a(client, message):
    query = ''
    for i in message.command[1:]:
        query += ' ' + str(i)
    print(query)
    m = message.reply('🔎 Fetching the song...')
    ydl_opts = {"format": "bestaudio[ext=m4a]"}
    try:
        results = []
        count = 0
        while len(results) == 0 and count < 6:
            if count>0:
                time.sleep(1)
            results = YoutubeSearch(query, max_results=1).to_dict()
            count += 1
        try:
            pprint(results[0]['id'])
            duration = results[0]["duration"]
            ## UNCOMMENT THIS IF YOU WANT A LIMIT ON DURATION. CHANGE 1800 TO YOUR OWN PREFFERED DURATION AND EDIT THE MESSAGE (30 minutes cap) LIMIT IN SECONDS
            # if time_to_seconds(duration) >= 1800:  # duration limit
            #     m.edit("Exceeded 30mins cap")
            #     return
            link = f"https://youtube.com{results[0]['url_suffix']}"
            # print(results)
            title = results[0]["title"]
            thumbnail = results[0]["thumbnails"][0]
            views = results[0]["views"]
            request = youtube.videos().list(
                        part='snippet',
                        id=f"{results[0]['id']}"
                    )
            response = request.execute()
            g = (response['items'][0]['snippet']['description']).split()
            C = (response['items'][0]['snippet']['channelTitle'])
            print(C)
            if not C in ("NoCopyrightSongs Hindi", "NoCopyrightSounds", "No Copyright Music -MALAYALAM ARENA", "NO COPYRIGHT BGM TAMIL", "No Copyright Background Music"):
                if "FREE" in g or "Free" in g or "free" in g or "Copyrightfree" in g:
                    print("ok")
                else:
                    m.edit("Sorry, the song you requested does not seem to be available for download. Watch it on Youtube",
                           reply_markup=InlineKeyboardMarkup(

                            [
                                [  # First row
                                    InlineKeyboardButton(  # Generates a callback query when pressed
                                        "Whatch Now 👀",
                                        url=link
                                    )
                                ]
                            ]
                        ))
                return
            else:
                print("continue")
                
#             thumb_name = f'thumb{message.message_id}.jpg'
#             thumb = requests.get(thumbnail, allow_redirects=True)
#             open(thumb_name, 'wb').write(thumb.content)
            
            

        except Exception as e:
            print(e)
            m.edit('Found nothing. Try changing the spelling a little.')
            return
    except Exception as e:
        m.edit(
            "✖️ Found Nothing. Sorry.\n\nTry another keywork or maybe spell it properly."
        )
        print(str(e))
        return
    m.edit("⏬ Downloading.")
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            audio_file = ydl.prepare_filename(info_dict)
            ydl.process_info(info_dict)
        rep = f'🎧 **Title**: [{title[:35]}]({link})\n⏳ **Duration**: `{duration}`\n👁‍🗨 **Views**: `{views}`'
        secmul, dur, dur_arr = 1, 0, duration.split(':')
        for i in range(len(dur_arr)-1, -1, -1):
            dur += (int(dur_arr[i]) * secmul)
            secmul *= 60
        message.reply_audio(audio_file, caption=rep, parse_mode='md',quote=False, title=title, duration=dur)
        m.delete()
    except Exception as e:
        m.edit('❌ Error')
        print(e)
    try:
        os.remove(audio_file)
#         os.remove(thumb_name)
    except Exception as e:
        print(e)

@bot.on_message(filters.regex(ytregex))
def video_dl(client, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    rpk = "[" + user_name + "](tg://user?id=" + str(user_id) + ")"
    chat_id = message.chat.id
    link = message.text.strip()
    bot.send_chat_action(chat_id, "typing")
    time.sleep(1)
    m = message.reply("Fetching data ⏳")
    try:
        ids = link.split('=')[1]
        print(ids)
        request = youtube.videos().list(
                        part='snippet',
                        id=f"{ids}"
                    )
        response = request.execute()
        g = (response['items'][0]['snippet']['description']).split()
        C = (response['items'][0]['snippet']['channelTitle'])
        if not C in ("NoCopyrightSongs Hindi", "NoCopyrightSounds", "No Copyright Music -MALAYALAM ARENA", "NO COPYRIGHT BGM TAMIL", "No Copyright Background Music"):
            if "FREE" in g or "Free" in g or "free" in g or "Copyrightfree" in g or "NCS" in g:
                print("ok")
            else:
                m.edit("Sorry, the song you requested does not seem to be available for download")
                return
        else:
            print("continue")

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            audio = ydl.prepare_filename(info_dict)
            ydl.process_info(info_dict)
            caption = f"**Requested by : {rpk}**\n\n@blackmusicgroup"


        m.edit("⏫ Uploading ")
        client.send_chat_action(chat_id, "upload_audio")
        message.reply_audio(audio, caption=caption)
        m.delete()
    
        if os.path.exists(audio):
            os.remove(audio)
        if os.path.exists('a.jpg'):
            os.remove('a.jpg')

    except exceptions.RegexMatchError:
        message.reply_text("Invalid URL.")
        m.delete() 
    except exceptions.LiveStreamError:
        message.reply_text("Live Stream links not supported.")
        m.delete()
    except exceptions.VideoUnavailable:
        message.reply_text("Video is unavailable.")
        m.delete()
    except exceptions.HTMLParseError:
        message.reply_text("Given URL couldn't be parsed.")
        m.delete()
                 
bot.run()
