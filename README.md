# TTS for Discord
TTS for Discord is a Python project that uses Discord.py and the Azure Cognitive Services Python SDK to bring Azure text to speech to Discord

## Installation

### Prerequisites

- Python 3.9.x (I have tested it so far on Python 3.9.4)

- An Azure Speech subscription Key and Region (create one for free [here](https://azure.microsoft.com/en-us/services/cognitive-services/text-to-speech/), see how to get credentials [here](https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/overview#try-the-speech-service-for-free))

- A Discord Bot token (you can find how to create one [here](https://discordpy.readthedocs.io/en/stable/discord.html))

### Set up and launching

1. Clone this repo to your local computer, then install the prequisite packages with ```pip install -r requirements.txt```.
We recommend using a Python virtual environment like [virtualenv](https://virtualenv.pypa.io/en/latest/) beforehand to isolate the bot and avoid versioning issues.

2. Run ```python3 start.py```. This will create the settings file and exit.

3. Fill in the blanks on ```settings.toml```. The discord.token, azure.key and azure.region fields are mandatory. A list of options for azure.voice can be found [here](https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support#text-to-speech), or you can leave it blank or fill "default" to autodetect the language and use voices accordingly (be aware that language autodetection is spotty at best and will make for hilariously bad results very often). You can see an in depth explanation of the settings below.

4. Run ```python3 start.py``` again. If everything goes well, you'll see a message saying "Logged in as \<username>"

5. Invite the bot to your server using the instructions [here](https://discordpy.readthedocs.io/en/stable/discord.html#inviting-your-bot). Please note I've used it so far with permissions to View Channels, Send Messages, Read Message History, Add Reactions, Connect and Speak, I recommend granting at least those permissions.

6. Done! You can see a command guide by writing $help on any text channel on your server (that the bot has access to, of course)

## Usage

You can find the command guide by typing $help on any text channel, but the main command you'll want is $say \<text>, which will prompt the bot to connect to the voice channel you're on, and read out loud the text you've given it.

To avoid spammers, trolls or grifters, the bot will only talk to people already connected to VC, it'll try to prune emojis and trim whitespace from the prompts, and it won't read out anything longer than 280 characters (measured after pruning and trimming). Although most of these anti-grifting safeguards can be turned off in the settings below.

### Settings

- Discord Token: This is the Discord Bot token that allows the bot to connect to a Discord account

- Discord Prefix: The prefix that indicates a command. Default is $

- Discord Ignore Case: This setting controls whether the bot is case insensitive when recognizing commands (e.g. whether ´´´$say´´´ and ´´´$Say´´´ are considered the same)

- Discord Ignore Disconnected: This setting controls whether the bot will respond to $say commands from users who aren't connected to a voice channel. To avoid spammers and grifters changing it on the go, it can only be changed from the settings.toml file and requires restarting the bot.

- Azure Key: This is the Azure Speech Key that allows the bot to connect to the Azure Speech SDK

- Azure Region: This is the Azure Speech Region that allows the bot to connect to the Azure Speech SDK

- Azure Voice: This is the voice that the bot will use to read text out loud. A full list of possible voices is available [here](https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support#text-to-speech)

- Azure Max Chars: This is the max text length that the bot will read out. You can change it to any value, or 0 to disable it. **IMPORTANT:** Please mind Azure currently provides 5M free characters per month for normal voices, or 500k free characters for Neural voices, after which it'll start charging your account. **I very highly recommend keeping the default character limit or setting up your own to avoid being rate limited or getting unexpected charges on your account**

## Support

File an issue if you encounter any bugs or wish to submit a feature request. Please use the templates provided for any of these two. **All bugs or feature requests submitted without the provided templates will be disregarded.**

## Roadmap

So far the idea is to expand a bit on what the bot can do and add an option for heroku and Docker deployment. 

## Contributing

If you wish to see any new features or commands, feel free to file a feature request under issues! Or better yet, submit a pull request with a proposed implementation! In any case I'll get in touch as soon as possible.

## Authors and acknowledgement

The code here was written by Diego Rivero using the quickstarts and documentation provided by the team behind [Discord.py](https://github.com/Rapptz/discord.py) and the team at Microsoft behind the [Python Speech SDK and tutorial](https://github.com/Azure-Samples/cognitive-services-speech-sdk/tree/master/quickstart/python/text-to-speech)

## License

This code is open sourced under the [MIT license](https://github.com/isthistechsupport/tts_for_discord/blob/main/LICENSE.md)