"""
Support for the yandex speechkit tts  service.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/tts/yandextts/
"""
import asyncio
import logging

import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant.const import CONF_API_KEY
from homeassistant.components.tts import Provider, PLATFORM_SCHEMA, CONF_LANG
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv


_LOGGER = logging.getLogger(__name__)

YANDEX_API_URL = "https://tts.voicetech.yandex.net/generate?"

SUPPORT_LANGUAGES = [
    'ru-RU', 'en-US', 'tr-TR', 'uk-UK'
]

SUPPORT_CODECS = [
    'mp3', 'wav', 'opus',
]

SUPPORT_VOICES = [
    'jane', 'oksana', 'alyss', 'omazh',
    'zahar', 'ermil'
]

SUPPORTED_EMOTION = [
    'good', 'evil', 'neutral'
]

MIN_SPEED = 0.1
MAX_SPEED = 3

CONF_CODEC = 'codec'
CONF_VOICE = 'voice'
CONF_EMOTION = 'emotion'
CONF_SPEED = 'speed'

DEFAULT_LANG = 'en-US'
DEFAULT_CODEC = 'mp3'
DEFAULT_VOICE = 'zahar'
DEFAULT_EMOTION = 'neutral'
DEFAULT_SPEED = 1

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_KEY): cv.string,
    vol.Optional(CONF_LANG, default=DEFAULT_LANG): vol.In(SUPPORT_LANGUAGES),
    vol.Optional(CONF_CODEC, default=DEFAULT_CODEC): vol.In(SUPPORT_CODECS),
    vol.Optional(CONF_VOICE, default=DEFAULT_VOICE): vol.In(SUPPORT_VOICES),
    vol.Optional(CONF_EMOTION, default=DEFAULT_EMOTION):
        vol.In(SUPPORTED_EMOTION),
    vol.Optional(CONF_SPEED, default=DEFAULT_SPEED):
        vol.Range(min=MIN_SPEED, max=MAX_SPEED)
})


@asyncio.coroutine
def async_get_engine(hass, config):
    """Setup VoiceRSS speech component."""
    return YandexSpeechKitProvider(hass, config)


class YandexSpeechKitProvider(Provider):
    """VoiceRSS speech api provider."""

    def __init__(self, hass, conf):
        """Init VoiceRSS TTS service."""
        self.hass = hass
        self._codec = conf.get(CONF_CODEC)
        self._key = conf.get(CONF_API_KEY)
        self._speaker = conf.get(CONF_VOICE)
        self._language = conf.get(CONF_LANG)
        self._emotion = conf.get(CONF_EMOTION)
        self._speed = str(conf.get(CONF_SPEED))
        self.name = 'YandexTTS'

    @property
    def default_language(self):
        """Default language."""
        return self._language

    @property
    def supported_languages(self):
        """List of supported languages."""
        return SUPPORT_LANGUAGES

    @asyncio.coroutine
    def async_get_tts_audio(self, message, language, options=None):
        """Load TTS from yandex."""
        websession = async_get_clientsession(self.hass)

        actual_language = language

        request = None
        try:
            with async_timeout.timeout(10, loop=self.hass.loop):
                url_param = {
                    'text': message,
                    'lang': actual_language,
                    'key': self._key,
                    'speaker': self._speaker,
                    'format': self._codec,
                    'emotion': self._emotion,
                    'speed': self._speed
                }

                request = yield from websession.get(YANDEX_API_URL,
                                                    params=url_param)

                if request.status != 200:
                    _LOGGER.error("Error %d on load url %s.",
                                  request.status, request.url)
                    return (None, None)
                data = yield from request.read()

        except (asyncio.TimeoutError, aiohttp.errors.ClientError):
            _LOGGER.error("Timeout for yandex speech kit api.")
            return (None, None)

        finally:
            if request is not None:
                yield from request.release()

        return (self._codec, data)
