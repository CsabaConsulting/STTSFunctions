import functions_framework
import os

from flask import Response
from google.cloud import texttospeech

@functions_framework.http
def tts_test(request):
    """Synthesizes speech from the input string of text or ssml.
    Returns:
        Encoded audio file in the body.
    Note: ssml must be well-formed according to:
        https://www.w3.org/TR/speech-synthesis/
    """
    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_json and 'token' in request_json:
        token = request_json['token']
    elif request_args and 'token' in request_args:
        token = request_args['token']
    else:
        token = ''

    FN_TOKEN = os.environ.get('TOKEN', '***')
    if FN_TOKEN != token:
        return ''

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "key.json"

    if request_json and 'language_code' in request_json:
        language_code = request_json['language_code']
    elif request_args and 'language_code' in request_args:
        language_code = request_args['language_code']
    else:
        language_code = os.environ.get('LANGUAGE_CODE', 'en-US')

    if request_json and 'text' in request_json:
        text = request_json['text']
    elif request_args and 'text' in request_args:
        text = request_args['text']
    else:
        text = ''

    # Instantiates a client
    client = texttospeech.TextToSpeechClient()

    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code, ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.OGG_OPUS
    )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # Set response headers
    headers = {
        "Content-Type": "audio/ogg",
        "Content-Disposition": "attachment; filename=response.opus",
    }
    
    # Return binary data as a response
    return Response(response.audio_content, headers=headers)
