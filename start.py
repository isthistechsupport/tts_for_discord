from azure.cognitiveservices.speech.languageconfig import AutoDetectSourceLanguageConfig
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer
from azure.cognitiveservices.speech.audio import AudioOutputConfig
import discord
from discord.ext import commands
import toml
import time
import os
import re

def save_setup(setup):
    f = open("settings.toml", "w")
    f.write(toml.dumps(setup))
    f.close()

try:
    setup = toml.load("settings.toml")
except:
    setup = {'discord': {'token': '', 'prefix': '$'}, 'azure': {'key': '', 'region': '', 'voice': '', 'max_chars': 280}}
    save_setup(setup)
    print("Fill settings.toml and try again")
    quit(1)

bot = commands.Bot(command_prefix=setup["discord"]["prefix"])

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
        return vc
    else:
        await ctx.send(f"{ctx.author.display_name} is not in a voice channel.")
        return vc

async def disconnect_vc(ctx):
    vc = ctx.voice_client
    if vc != None:
        await vc.disconnect()
    else:
        await ctx.send(f"Already disconnected.")

async def setup_azure():
    auto_detect_source_language_config = None
    speech_config = SpeechConfig(subscription=setup["azure"]["key"], region=setup["azure"]["region"])
    if setup["azure"]["voice"] == '' or setup["azure"]["voice"] == 'default':
        auto_detect_source_language_config = AutoDetectSourceLanguageConfig(None, None)
    else:
        speech_config.speech_synthesis_voice_name = setup["azure"]["voice"]
    audio_config = AudioOutputConfig(filename=f"./latest.wav")
    synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config, auto_detect_source_language_config=auto_detect_source_language_config)
    return synthesizer

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command(name="join", help="Connects to the current voice channel")
async def join(ctx):
    await connect_vc(ctx)

@bot.command(name="leave", help="Disconnects from the current voice channel")
async def leave(ctx):
    await disconnect_vc(ctx)

@bot.command(name="setprefix", help="Sets the bot prefix, default is $")
async def setprefix(ctx, new_prefix):
    ctx.prefix = new_prefix
    setup["discord"]["prefix"] = new_prefix
    save_setup(setup)
    await ctx.send(f"New prefix set to {new_prefix}")

@bot.command(name="setvoice", help=f"Sets the bot voice, the list of possible voices can be found at https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support#text-to-speech (leave blank or 'default' to autodetect language)")
async def setvoice(ctx, new_voice):
    setup["azure"]["voice"] = new_voice
    save_setup(setup)
    await ctx.send(f"New voice set to {new_voice}")

@bot.command(name="say", help="Reads whatever text is passed out loud")
async def say(ctx, *, arg: str):
    cleaned = re.sub('(<:.*:\d*>)', '', arg).strip()
    if setup["azure"]["max_chars"] == 0 or len(cleaned) <= setup["azure"]["max_chars"]:
        synthesizer = await setup_azure()
        synthesizer.speak_text_async(cleaned).get()
        vc = await connect_vc(ctx)
        vc.play(discord.FFmpegPCMAudio(source=f"./latest.wav"))
        while vc.is_playing():
            time.sleep(0.5)
        os.truncate("./latest.wav", 0)
    else:
        await ctx.send(f"The message is longer than {setup['azure']['max_chars']} characters")
    
@bot.command(name="ping", help="Shows the bot latency")
async def ping(ctx):
    ping_ = bot.latency
    ping =  round(ping_ * 1000)
    await ctx.send(f"My ping is {ping}ms")

bot.run(setup["discord"]["token"])