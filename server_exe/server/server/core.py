from mainapp.decos import login_required  #
from mainapp.settings import *  #
from mainapp.descriptors import Port  #
from mainapp.utils import *  #
from mainapp.metaclasses import ServerMaker
import threading
import logging
import select
import socket
import json
import hmac
import binascii
import os
import sys

sys.path.append('../')

SERVER_LOGGER = logging.getLogger('server')
qmessage = Message()


class MessageProcessor(threading.Thread):
    '''
    Основной класс сервера. Принимает содинения, словари - пакеты
    от клиентов, обрабатывает поступающие сообщения.
    Работает в качестве отдельного потока.
    '''
    port = Port()

    def __init__(self, listen_address, listen_port, database):
        self.addr = listen_address
        self.port = listen_port

        self.database = database

        self.sock = None

        self.clients = []

        self.listen_sockets = None
        self.error_sockets = None

        self.running = True

        self.names = dict()
        super().__init__()

    def run(self):
        '''Метод основной цикл потока.'''
        qmessage = Message()
        self.init_socket()
        while self.running:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                SERVER_LOGGER.info(
                    f'Установлено соединение с {client_address}')
                client.settimeout(5)
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            try:
                if self.clients:
                    recv_data_lst, self.listen_sockets, self.error_sockets = select.select(
                        self.clients, self.clients, [], 0)
            except OSError as err:
                SERVER_LOGGER.error(f'Ошибка работы с сокетами: {err.errno}')

            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(
                            qmessage.get_msg(client_with_message), client_with_message)
                    except (OSError, json.JSONDecodeError, TypeError) as err:
                        SERVER_LOGGER.debug(
                            f'Getting data from client exception.', exc_info=err)
                        self.remove_client(client_with_message)

    def remove_client(self, client):
        '''
        Метод обработчик клиента с которым прервана связь.
        Ищет клиента и удаляет его из списков и базы:
        '''
        SERVER_LOGGER.info(
            f'Клиент {client.getpeername()} отключился от сервера.')
        for name in self.names:
            if self.names[name] == client:
                self.database.user_logout(name)
                del self.names[name]
                break
        self.clients.remove(client)
        client.close()

    def init_socket(self):
        '''Метод инициализатор сокета.'''
        SERVER_LOGGER.info(
            f'Запущен сервер, порт для подключений: {self.port} , адрес с которого принимаются подключения:/'
            f' {self.addr}. Если адрес не указан, принимаются соединения с любых адресов.')

        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)

        self.sock = transport
        self.sock.listen(MAX_CONNECTIONS)

    def process_message(self, sock):
        '''
        Метод отправки сообщения клиенту.
        '''
        qmessage = Message()
        if sock[DESTINATION] in self.names and self.names[sock[DESTINATION]
                                                          ] in self.listen_sockets:
            try:
                qmessage.send_msg(self.names[sock[DESTINATION]], sock)
                SERVER_LOGGER.info(
                    f'Отправлено сообщение пользователю {sock[DESTINATION]} от пользователя {sock[SENDER]}.')
            except OSError:
                self.remove_client(sock[DESTINATION])
        elif sock[DESTINATION] in self.names and self.names[sock[DESTINATION]] not in self.listen_sockets:
            SERVER_LOGGER.error(
                f'Свзяь с клиентов {sock[DESTINATION]} была потеряна. Соединение закрыто, доставака невозможна')
            self.remove_client(self.names[sock[DESTINATION]])
        else:
            SERVER_LOGGER.error(
                f'Пользователь {sock[DESTINATION]} не зарегистрирован на сервере, отправка сообщения невозможна. ')

    @login_required
    def process_client_message(self, sock, client):
        '''Метод отбработчик поступающих сообщений.'''
        SERVER_LOGGER.debug(f'Разбор сообщения от клиента : {sock}')
        qmessage = Message()

        if ACTION in sock and sock[ACTION] == PRESENCE and TIME in sock and USER in sock:
            self.autorize_user(sock, client)

        elif ACTION in sock and sock[
            ACTION] == MESSAGE and DESTINATION in sock and TIME in sock and \
                SENDER in sock and MESSAGE_TEXT in sock and \
                self.names[sock[SENDER]] == client:
            if sock[DESTINATION] in self.names:
                self.database.process_message(sock[SENDER], sock[DESTINATION])
                self.process_message(sock)
                try:
                    qmessage.send_msg(client, RESPONSE_200)
                except OSError:
                    self.remove_client(client)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Пользователь не зарегистрирован на сервере'
                try:
                    qmessage.send_msg(client, response)
                except OSError:
                    pass
            return

        elif ACTION in sock and sock[ACTION] == EXIT and ACCOUNT_NAME in sock and self.names[
                sock[ACCOUNT_NAME]] == client:
            self.remove_client(client)

        elif ACTION in sock and sock[ACTION] == GET_CONTACTS and USER in sock and self.names[sock[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(sock[USER])
            try:
                qmessage.send_msg(client, response)
            except OSError:
                self.remove_client(client)

        elif ACTION in sock and sock[ACTION] == ADD_CONTACT and ACCOUNT_NAME in sock and USER in sock and self.names[
                sock[USER]] == client:
            self.database.add_contact(sock[USER], sock[ACCOUNT_NAME])
            try:
                qmessage.send_msg(client, RESPONSE_200)
            except OSError:
                self.remove_client(client)

        elif ACTION in sock and sock[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in sock and USER in sock and self.names[
                sock[USER]] == client:
            self.database.remove_contact(sock[USER], sock[ACCOUNT_NAME])
            try:
                qmessage.send_msg(client, RESPONSE_200)
            except OSError:
                self.remove_client(client)

        elif ACTION in sock and sock[ACTION] == USERS_REQUEST and ACCOUNT_NAME in sock and self.names[
                sock[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0]
                                   for user in self.database.users_list()]
            try:
                qmessage.send_msg(client, response)
            except OSError:
                self.remove_client(client)

        elif ACTION in sock and sock[ACTION] == PUBLIC_KEY_REQUEST and ACCOUNT_NAME in sock:
            response = RESPONSE_511
            response[DATA] = self.database.get_pubkey(sock[ACCOUNT_NAME])
            if response[DATA]:
                try:
                    qmessage.send_msg(client, response)
                except OSError:
                    self.remove_client(client)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Нет публичного ключа для данного пользователя'
                try:
                    qmessage.send_msg(client, response)
                except OSError:
                    self.remove_client(client)
        else:
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен.'
            try:
                qmessage.send_msg(client, response)
            except OSError:
                self.remove_client(client)

    def autorize_user(self, message, sock):
        '''Метод реализующий авторизцию пользователей.'''
        qmessage = Message()
        SERVER_LOGGER.debug(f'Start auth process for {message[USER]}')
        if message[USER][ACCOUNT_NAME] in self.names.keys():
            response = RESPONSE_400
            response[ERROR] = 'Имя пользователя уже занято.'
            try:
                SERVER_LOGGER.debug(f'Username busy, sending {response}')
                qmessage.send_msg(sock, response)
            except OSError:
                SERVER_LOGGER.debug('OS Error')
                pass
            self.clients.remove(sock)
            sock.close()
        elif not self.database.check_user(message[USER][ACCOUNT_NAME]):
            response = RESPONSE_400
            response[ERROR] = 'Пользователь не зарегистрирован'
            try:
                SERVER_LOGGER.debug(f'Unknown username, sending {response}')
                qmessage.send_msg(sock, response)
            except OSError:
                pass
            self.clients.remove(sock)
            sock.close()
        else:
            SERVER_LOGGER.debug('Correct username, starting passwd check.')
            message_auth = RESPONSE_511
            random_str = binascii.hexlify(os.urandom(64))
            message_auth[DATA] = random_str.decode('ascii')
            hash = hmac.new(
                self.database.get_hash(
                    message[USER][ACCOUNT_NAME]),
                random_str,
                'MD5')
            digest = hash.digest()
            SERVER_LOGGER.debug(f'Auth message = {message_auth}')
            try:
                qmessage.send_msg(sock, message_auth)
                ans = qmessage.get_msg(sock)
            except OSError as err:
                SERVER_LOGGER.debug('Error in auth, data:', exc_info=err)
                sock.close()
                return
            client_digest = binascii.a2b_base64(ans[DATA])
            if RESPONSE in ans and ans[RESPONSE] == 511 and hmac.compare_digest(
                    digest, client_digest):
                self.names[message[USER][ACCOUNT_NAME]] = sock
                client_ip, client_port = sock.getpeername()
                try:
                    qmessage.send_msg(sock, RESPONSE_200)
                except OSError:
                    self.remove_client(message[USER][ACCOUNT_NAME])
                self.database.user_login(
                    message[USER][ACCOUNT_NAME],
                    client_ip,
                    client_port,
                    message[USER][PUBLIC_KEY]
                )
            else:
                response = RESPONSE_400
                response[ERROR] = 'Неверный пароль'
                try:
                    qmessage.send_msg(sock, response)
                except OSError:
                    pass
                self.clients.remove(sock)
                sock.close()

    def service_update_lists(self):
        '''Метод реализующий отправки сервисного сообщения 205 клиентам.'''
        for client in self.names:
            try:
                qmessage.send_msg(self.names[client], RESPONSE_205)
            except OSError:
                self.remove_client(self.names[client])
