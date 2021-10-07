import requests
import datetime
import json

azure_token = {'token': '', 'expiration_date': datetime.datetime(1970,1,1)}


def get_token(setup):
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


def speak_text(text: str, filename: str, setup):
    """
    Downloads a recording of the given text with the given filename
    """
    url = f"https://{setup['azure']['region']}.tts.speech.microsoft.com/cognitiveservices/v1"
    payload = f"<speak version=\"1.0\" xmlns=\"http://www.w3.org/2001/10/synthesis\" xml:lang=\"en-US\"><voice name=\"{setup['azure']['voice']}\">{text}</voice></speak>".encode('utf-8')
    headers = {
        'Content-Type': 'application/ssml+xml',
        'X-Microsoft-OutputFormat': 'audio-16khz-32kbitrate-mono-mp3',
        'Authorization': f'Bearer {get_token(setup)}'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    with open(filename, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                file.write(chunk)


def get_voices(language, setup):
    """
    Downloads a recording of the given text with the given filename
    """
    fetch_voices_url = f"https://{setup['azure']['region']}.tts.speech.microsoft.com/cognitiveservices/voices/list"
    headers = {
        'Authorization': f"Bearer {get_token(setup)}",
        'User-Agent': 'tts_for_discord_bot'
    }
    response = requests.get(fetch_voices_url, headers=headers)
    voices = json.loads(str(response.text))
    voices_filtered = filter(lambda voice: voice['Locale'].startswith(language), voices)
    voice_names = map(lambda voice: voice['ShortName'], voices_filtered)
    return voice_names
