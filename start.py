from azure.cognitiveservices.speech.languageconfig import AutoDetectSourceLanguageConfig
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer
from azure.cognitiveservices.speech.audio import AudioOutputConfig
import discord
from discord import file
from discord.ext import commands
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


@bot.command(name="listvoices", help=f"Gets the possible voices")
async def setvoice(ctx, language):
    await ctx.send(f"Current voice is {setup['azure']['voice']}")


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


async def setup_azure(filename):
    """
    Returns an Azure Speech Synthesizer pointing to the given filename
    """
    auto_detect_source_language_config = None
    speech_config = SpeechConfig(subscription=setup['azure']['key'], region=setup['azure']['region'])
    if setup['azure']['voice'] == '' or setup['azure']['voice'] == 'default':
        auto_detect_source_language_config = AutoDetectSourceLanguageConfig(None, None)
    else:
        speech_config.speech_synthesis_voice_name = setup['azure']['voice']
    audio_config = AudioOutputConfig(filename=filename)
    synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config, auto_detect_source_language_config=auto_detect_source_language_config)
    return synthesizer


async def speak(ctx, text, filename, delete):
    """
    Reads the given text out loud
    """
    try:
        vc = await connect_vc(ctx)
        if text != None:
            synthesizer = await setup_azure(filename)
            synthesizer.speak_text_async(text).get()
        if vc == None and (not setup['discord']['ignore_dc']):
            audio = discord.File(filename)
            await ctx.send(content="Here's the audio", file=audio)
        else:
            await vc.play(discord.FFmpegPCMAudio(source=filename))
    except RuntimeError as ex:
        await ctx.send(f"{ctx.author.mention} is not connected to voice")
    finally:
        if delete:
            try:
                os.remove(filename)
            except:
                pass


@bot.command(name="say", help="Reads whatever text is passed out loud")
async def say(ctx, *, arg: str):
    filename = f"{uuid.uuid4().hex}.wav"
    cleaned = re.sub('(<:.*:\d*>)', '', arg).strip()
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
    if str(message.author) == "Chismander#8766" and (str(message.content)).count(":(") > 0:
        await message.channel.send("Típico de Piscis")
    await bot.process_commands(message)


bot.run(setup['discord']['token'])