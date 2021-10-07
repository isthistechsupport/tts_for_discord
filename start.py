import sqlalchemy
from dbschema import connect_db
from speech import get_voices, speak_text
import discord
from discord.ext import commands
import emoji
import datetime
import toml
import time
import uuid
import os
import re
import reddit


def save_setup(setup):
    """
    Writes the setup to settings.toml
    """
    f = open("settings.toml", "w")
    f.write(toml.dumps(setup))
    f.close()


def replace_emoji(string, replace='', language='en', ):
    """
    Replace unicode emoji in a customizable string.
    """
    return re.sub(u'\ufe0f', '', (emoji.get_emoji_regexp(language).sub(replace, string)))


# Tries to load the settings, otherwise creates a new settings.toml and prompts the user to fill it
try:
    setup = toml.load("settings.toml")
    assert setup['discord']['token'] != "", "A Discord Token is required"
    assert setup['azure']['key'] != "", "An Azure Speech Key is required"
    assert setup['azure']['region'] != "", "An Azure Speech Region is required"
    assert setup['reddit']['id'] != "", "A Reddit client ID is required"
    assert setup['reddit']['secret'] != "", "A Reddit client secret is required"
except:
    setup = toml.load("settings.template.toml")
    save_setup(setup)
    print("Fill settings.toml and try again")
    quit(1)


bot = commands.Bot(command_prefix=setup['discord']['prefix'])
bot.case_insensitive = setup['discord']['ignore_case']
if setup['cache']['file'] == "":
    setup['cache']['file'] = "history.db"
    save_setup(setup)
engine = connect_db(setup['cache']['file'])


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
            speak_text(text, filename, setup)
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
    voice_names = get_voices(locale, setup)
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


@bot.command(name="say", aliases=["make"], help="Reads whatever text is passed out loud")
async def say(ctx, *, text: str):
    filename = f"{uuid.uuid4().hex}.wav"
    cleaned_text = replace_emoji(re.sub('(<:.*:\d*>)', '', text).strip())
    if setup['azure']['max_chars'] == 0 or len(cleaned_text) <= setup['azure']['max_chars']:
        await speak(ctx, cleaned_text, filename, True)
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


@bot.command(name="post", help="Gets a post from a subreddit")
async def post(ctx, subreddit, dupe: bool = False):
    await ctx.send(f"https://redd.it/{reddit.get_post(subreddit, str(ctx.guild), ctx.guild.id, str(ctx.channel), ctx.channel.id, str(ctx.author), ctx.author.id, dupe, engine, setup).id}")


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


@bot.event
async def on_message(message):
    if not message.author.bot:
        for file in message.attachments:
            try:
                await file.save(f"{str(datetime.datetime.now()).replace(' ', '_')}_{file.filename}")
                print(f"Saved file as {file.filename}")
            except:
                try:
                    await file.save(f"{str(datetime.datetime.now()).replace(' ', '_')}_cached_{file.filename}", use_cached=True)
                    print(f"Saved file as {file.filename}")
                except:
                    print(f"File couldn't be saved")
    if str(message.author) == "Chismander#8766" and ((str(message.content)).count(":(") > 0 or (str(message.content)).count(":c") > 0):
        await message.channel.send("Típico de Piscis")
    await bot.process_commands(message)


bot.run(setup['discord']['token'])