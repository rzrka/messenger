import logging
import log.configs.server_log_config
import log.configs.client_log_config
from mainapp.settings import *
import json
import sys

sys.path.append('../')


class Log:
    def __call__(self, func):
        def log_saver(*args, **kwargs):
            ret = func(*args, **kwargs)
            if sys.argv[0].find('client') == -1:
                LOGGER = logging.getLogger('server')
            else:
                LOGGER = logging.getLogger('client')
            LOGGER.debug(
                f'Была вызвана функция {func.__name__} с параметрами {args}, {kwargs}.'
                f'Вызов из модуля {func.__module__}.')
            return ret

        return log_saver


class Message:
    @Log()
    def get_msg(self, client):
        encoded_response = client.recv(MAX_PACKAGE_LENGTH)
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        else:
            raise TypeError

    @Log()
    def send_msg(self, sock, message):
        js_message = json.dumps(message)
        encoded_message = js_message.encode(ENCODING)
        sock.send(encoded_message)
