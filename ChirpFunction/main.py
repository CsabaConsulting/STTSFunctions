import functions_framework
import google.cloud.logging
import gzip
import logging
import os

from google.api_core.client_options import ClientOptions
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech


def transcribe_chirp_auto_detect_language(
    project_id: str,
    region: str,
    audio_bytes: str,
) -> cloud_speech.RecognizeResponse:
    """Transcribe an audio file and auto-detect spoken language using Chirp.

    Please see https://cloud.google.com/speech-to-text/v2/docs/encoding for more
    information on which audio encodings are supported.
    """
    # Instantiates a client
    client = SpeechClient(
        client_options=ClientOptions(
            api_endpoint=f"{region}-speech.googleapis.com",
        )
    )

    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=["auto"],  # Set language code to auto to detect language.
        model="chirp",
    )

    request = cloud_speech.RecognizeRequest(
        recognizer=f"projects/{project_id}/locations/{region}/recognizers/_",
        config=config,
        content=audio_bytes,
    )

    # Transcribes the audio into text
    response = client.recognize(request=request)

    transcripts = []
    for result in response.results:
        transcripts.append(result.alternatives[0].transcript)
        transcripts.append(result.language_code)

    return transcripts


@functions_framework.http
def chirp_test(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): Carries the PCM16 audio with WAV header as body.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        Alternating list of transcript and the language of the preceding transcript.
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_json and 'token' in request_json:
        token = request_json['token']
    elif request_args and 'token' in request_args:
        token = request_args['token']
    else:
        token = ''

    results = []

    FN_TOKEN = os.environ.get('TOKEN', '***')
    if FN_TOKEN != token:
        return results

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "key.json"

    if request_json and 'project_id' in request_json:
        project_id = request_json['project_id']
    elif request_args and 'project_id' in request_args:
        project_id = request_args['project_id']
    else:
        project_id = os.environ.get('PROJECT_ID', 'duet-ai-roadshow-415022')

    if request_json and 'region' in request_json:
        region = request_json['region']
    elif request_args and 'region' in request_args:
        region = request_args['region']
    else:
        region = os.environ.get('REGION', 'us-central1')

    try:
        gzipped_bytes = request.get_data()
        uncompressed_bytes = gzip.decompress(gzipped_bytes)
        results = transcribe_chirp_auto_detect_language(project_id, region, uncompressed_bytes)
    except Exception as e:
        client = google.cloud.logging.Client()
        client.setup_logging()
        logging.exception(e)
        return results

    return results
