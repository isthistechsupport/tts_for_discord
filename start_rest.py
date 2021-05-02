from typing import Text
import requests
import discord
from xml.sax.saxutils import quoteattr, escape
from discord.ext import commands
import demoji
import datetime
import json
import toml
import time
import uuid
import os
import re


def save_setup(setup):
    """
    Writes the setup to settings.toml
    """
    f = open("settings.toml", "w")
    f.write(toml.dumps(setup))
    f.close()


# Tries to load the settings, otherwise creates a new settings.toml and prompts the user to fill it
try:
    setup = toml.load("settings.toml")
    assert setup['discord']['token'] != "", "A Discord Token is required"
    assert setup['azure']['key'] != "", "An Azure Speech Key is required"
    assert setup['azure']['region'] != "", "An Azure Speech Region is required"
except:
    setup = toml.load("settings.toml.template")
    save_setup(setup)
    print("Fill settings.toml and try again")
    quit(1)


if demoji.last_downloaded_timestamp() == None:
    demoji.download_codes()


azure_token = {'token': '', 'expiration_date': datetime.datetime(1970,1,1)}


def get_token():
    """
    Gets the Bearer token to connect to Azure
    """
    if datetime.datetime.now() > azure_token['expiration_date']:
        fetch_token_url = f"https://{setup['azure']['region']}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
        headers = {
            'Ocp-Apim-Subscription-Key': setup['azure']['key'],
            'User-Agent': 'tts_for_discord_bot'
        }
        response = requests.post(fetch_token_url, headers=headers)
        azure_token['token'] = str(response.text)
        azure_token['expiration_date'] = datetime.datetime.now() + datetime.timedelta(minutes=9)
    return azure_token['token']


def speak_text(text: str, filename: str):
    """
    Downloads a recording of the given text with the given filename
    """
    url = f"https://{setup['azure']['region']}.tts.speech.microsoft.com/cognitiveservices/v1"
    payload = f"<speak version=\"1.0\" xmlns=\"http://www.w3.org/2001/10/synthesis\" xml:lang=\"en-US\"><voice name=\"{setup['azure']['voice']}\">{text}</voice></speak>"
    headers = {
        'Content-Type': 'application/ssml+xml',
        'X-Microsoft-OutputFormat': 'audio-16khz-32kbitrate-mono-mp3',
        'Authorization': f'Bearer {get_token()}'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    with open(filename, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                file.write(chunk)


def get_voices(language):
    """
    Downloads a recording of the given text with the given filename
    """
    fetch_voices_url = f"https://{setup['azure']['region']}.tts.speech.microsoft.com/cognitiveservices/voices/list"
    headers = {
        'Authorization': f"Bearer {get_token()}",
        'User-Agent': 'tts_for_discord_bot'
    }
    response = requests.get(fetch_voices_url, headers=headers)
    voices = json.loads(str(response.text))
    voices_filtered = filter(lambda voice: voice['Locale'].startswith(language), voices)
    voice_names = map(lambda voice: voice['ShortName'], voices_filtered)
    return voice_names


bot = commands.Bot(command_prefix=setup['discord']['prefix'])
bot.case_insensitive = setup['discord']['ignore_case']


@bot.command(name="getprefix", help="Gets the bot prefix")
async def getprefix(ctx):
    await ctx.send(f"Current prefix is {setup['discord']['prefix']}")


@bot.command(name="setprefix", help="Sets the bot prefix, default is $")
async def setprefix(ctx, new_prefix):
    if new_prefix != '':
        ctx.prefix = new_prefix
        setup['discord']['prefix'] = new_prefix
        save_setup(setup)
        await ctx.send(f"New prefix set to {new_prefix}")
    else:
        await ctx.send(f"New prefix can't be blank")


@bot.command(name="getcase", help="Gets the case insensitiveness")
async def setprefix(ctx):
    await ctx.send(f"case insensitiveness is set to {setup['discord']['ignore_case']}")


@bot.command(name="setcase", help="Sets the case insensitiveness, default is true")
async def setprefix(ctx, new_case :bool):
    ctx.bot.case_insensitive = new_case
    setup['discord']['ignore_case'] = new_case
    save_setup(setup)


async def speak(ctx, text, filename, delete):
    """
    Reads the given text out loud
    """
    try:
        vc = await connect_vc(ctx)
        if text != None:
            speak_text(text, filename)
        if vc == None and (not setup['discord']['ignore_dc']):
            audio = discord.File(filename)
            await ctx.send(content="Here's the audio", file=audio)
        else:
            vc.play(discord.FFmpegPCMAudio(source=filename))
            while vc.is_playing():
                time.sleep(0.5)
    except RuntimeError as ex:
        await ctx.send(f"{ctx.author.mention} is not connected to voice")
    finally:
        if delete:
            try:
                os.remove(filename)
            except:
                pass


@bot.command(name="listvoices", help=f"Gets the possible voices for the given language")
async def listvoices(ctx, language: str):
    locale = language
    if language.lower() == "español" or language.lower() == "spanish":
        locale = 'es'
        await ctx.send(f"Converting language \"{language}\" to locale {locale}")
    if language.lower() == "english" or language.lower() == "ingles" or language.lower() == "inglés":
        locale = 'en'
        await ctx.send(f"Converting language \"{language}\" to locale {locale}")
    if language.lower() == "portuguese" or language.lower() == "portugués" or language.lower() == "portugues" or language.lower() == "português":
        locale = 'pt'
        await ctx.send(f"Converting language \"{language}\" to locale {locale}")
    voice_names = get_voices(locale)
    await ctx.send(f"The available voices for locale {locale} are {', '.join(voice_names)}. Type $setvoice <voice name> to use them")


@bot.command(name="getvoice", help=f"Gets the current bot voice")
async def getvoice(ctx):
    await ctx.send(f"Current voice is {setup['azure']['voice']}")


@bot.command(name="setvoice", help=f"Sets the bot voice, the list of possible voices can be found at https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support#text-to-speech (leave blank or 'default' to autodetect language)")
async def setvoice(ctx, new_voice):
    setup['azure']['voice'] = new_voice
    save_setup(setup)
    await ctx.send(f"New voice set to {new_voice}")


@bot.command(name="join", help="Connects to the current voice channel")
async def connect_vc(ctx):
    voice_enabled = ctx.author.voice
    vc = None
    if voice_enabled != None:
        voice_channel=ctx.author.voice.channel
        if ctx.me.voice == None:
            vc = await voice_channel.connect()
        elif voice_channel != ctx.me.voice.channel:
            await ctx.voice_client.disconnect()
            vc = await voice_channel.connect()
        else:
            vc = ctx.voice_client
    else:
        if (not setup['discord']['ignore_dc']) and ctx.me.voice != None:
            vc = ctx.voice_client
        elif (not setup['discord']['ignore_dc']):
            pass
        else:
            raise RuntimeError("Member is not connected to voice")
    return vc


@bot.command(name="leave", help="Disconnects from the current voice channel")
async def disconnect_vc(ctx):
    vc = ctx.voice_client
    if vc != None:
        await vc.disconnect()
    else:
        await ctx.send(f"Already disconnected.")


@bot.command(name="say", aliases=['make'], help="Reads whatever text is passed out loud")
async def say(ctx, *, arg: str):
    filename = f"{uuid.uuid4().hex}.wav"
    pruned = re.sub('(<:.*:\d*>)', '', arg).strip()
    cleaned = demoji.replace(pruned, "")
    if setup['azure']['max_chars'] == 0 or len(cleaned) <= setup['azure']['max_chars']:
        await speak(ctx, cleaned, filename, True)
    else:
        await ctx.send(f"The message is longer than {setup['azure']['max_chars']} characters")

    
@bot.command(name="horoscope", help="Gives my horoscope")
async def horoscope(ctx):
    await ctx.send(f"I'm a Taurus, moon in Virgo, ascendant in Scorpio. Basically this means I'm a very dramatic bot. However, I cry less than Piscis, and I'm less toxic than Scorpios")
    await speak(ctx, None, './horoscope.wav', False)


@bot.command(name="ping", help="Shows the bot latency")
async def ping(ctx):
    ping_ = bot.latency
    ping =  round(ping_ * 1000)
    await ctx.send(f"My ping is {ping}ms")


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


@bot.event
async def on_message(message):
    if str(message.author) == "Chismander#8766" and ((str(message.content)).count(":(") > 0 or (str(message.content)).count(":c") > 0):
        await message.channel.send("Típico de Piscis")
    await bot.process_commands(message)


bot.run(setup['discord']['token'])