import dis


class ServerMaker(type):
    def __init__(cls, clsname, bases, clsdict):
        methods = []
        attrs = []
        for func in clsdict:
            try:
                rets = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for ret in rets:
                    if ret.opname == 'LOAD_GLOBAL':
                        if ret.argval not in methods:
                            methods.append(ret.argval)
                    elif ret.opname == 'LOAD_ATTR':
                        if ret.argval not in attrs:
                            attrs.append(ret.argval)
        if 'connect' in methods:
            raise TypeError(
                'Использование метода connect недопустимо в серверном классе')
        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Некорректная инициализация сокета.')
        super().__init__(clsname, bases, clsdict)


class ClientMaker(type):
    def __init__(cls, clsname, bases, clsdict):
        methods = []
        for func in clsdict:
            try:
                rets = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for ret in rets:
                    if ret.opname == 'LOAD_GLOBAL':
                        if ret.argval not in methods:
                            methods.append(ret.argval)
        for command in ('accept', 'listen', 'socket'):
            if command in methods:
                raise TypeError(
                    'В Классе обнаружено использование запрещенного метода')
        super().__init__(clsname, bases, clsdict)
