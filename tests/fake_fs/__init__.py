import multiprocessing
import socket
import threading
import select
import time

FS_AUTH_ACCEPTED_REPLY = b'Content-Type: command/reply\nReply-Text: +OK accepted\n\n'
FS_AUTH_DENIED_REPLY = b'Content-Type: command/reply\nReply-Text: -ERR invalid\n\n'
FS_EXIT_REPLY = b'Content-Type: command/reply\nReply-Text: +OK bye\n\n'
FS_ERR_COMMAND_NOT_FOUND = b'Content-Type: command/reply\nReply-Text: -ERR command not found\n\n'
FS_DISCONNECT_NOTICE = b'Content-Type: text/disconnect-notice\nContent-Length: 67'
FS_AUTH_INVITE = b'Content-Type: auth/request\n\n'

DS_EVENT = 0
UPE_EVENT = 1


class _FakeFsEvent(object):

    def __init__(self, event_type: str):
        self._headers = list()
        self._body = ''
        self.add_header('Event-Type', event_type)

    def serialize(self) -> str:
        result = ''
        for (name, value) in self._headers:
            result += '%s: %s\n' % (name, value)
        if len(self._body):
            result += 'Content-Length: %i' % len(self._body)
        result += '\n%s' % self._body
        return result

    def add_header(self, header: str, value: str) -> None :
        self._headers.append((header, value))

    def add_body(self, body: str) -> None:
        self._body = body

    def get_header(self, header: str) -> (str, None):
        for (h,v) in self._headers:
            if h == header:
                return v
        return None


class _FakeFsEventList(list):

    def __init__(self, events: list):
        super().__init__()
        for event in events:
            if isinstance(event, _FakeFsEvent):
                self.append(event)

    def __add__(self, other):
        if isinstance(other, _FakeFsEventList):
            super().__add__(other)

    def append(self, _object: _FakeFsEvent) -> None:
        super().append(_object)

_ds_event = _FakeFsEvent('DETECTED_SPEECH')
_ds_event.add_header('Speech-Type', 'detected-speech')
_ds_event.add_header('ASR-Completion-Cause', '006')
_upe_event = _FakeFsEvent('CUSTOM')
_upe_event.add_header('Event-Subclass', 'unimrcp::profile_error')
_upe_event.add_header('MRCP-Channel-Timeout', '5000')
_fs_events = []
_fs_events.insert(DS_EVENT, _ds_event)
_fs_events.insert(UPE_EVENT, _upe_event)


class FakeFS(object):

    def __init__(self, conn: socket.socket, addr: str, password: str,
                 do_exit: multiprocessing.Event,
                 conn_success: multiprocessing.Event,
                 events: list) -> None:
        self._conn = conn
        self._addr = addr
        self._password = password
        self._event_types = []
        self._custom_event_subtypes = []
        self._do_exit = do_exit
        self._conn_success = conn_success
        self._event_generator = threading.Thread(target=self._generate_events)
        self._events = _FakeFsEventList([_fs_events[event] for event in events])

    def run(self):
        self._conn.send(FS_AUTH_INVITE)
        buf = ''
        while not self._do_exit.is_set():
            readers, writers, ers = select.select([self._conn], [], [])
            if not self._conn in readers:
                time.sleep(0.01)
                continue
            l_buf = self._conn.recv(4096)
            if not l_buf: break
            buf += l_buf.decode('ascii')
            while not buf.find('\n\n') == -1:
                if not self._process_message(buf[:buf.find('\n\n')]): return
                buf = buf[buf.find('\n\n')+2:]

    def _process_message(self, msg: str) -> bool:
        if msg.find(' '):
            cmd = msg[:msg.find(' ')]
        else:
            cmd = msg
        if cmd == 'auth':
            if msg[msg.find(' ')+1:] == self._password:
                self._conn.send(FS_AUTH_ACCEPTED_REPLY)
                self._conn_success.set()
            else:
                self._conn.send(FS_AUTH_DENIED_REPLY)
                self._conn.send(FS_DISCONNECT_NOTICE)
                return False
        elif cmd == 'exit':
            self._conn.send(FS_EXIT_REPLY)
            self._conn.send(FS_DISCONNECT_NOTICE)
            return False
        elif cmd == 'event':
            if not msg.split(' ')[1] == 'plain':
                raise Exception('Fake FS do not understand other event types than plain')
            if msg.find('CUSTOM') == -1:
                self._event_types += msg.split(' ')[2:]
            else:
                self._event_types += msg[:msg.find(' CUSTOM')].split(' ')[2:]
                self._custom_event_subtypes += msg[msg.find('CUSTOM ')+len('CUSTOM '):].split(' ')
            if not self._event_generator.is_alive(): self._event_generator.run()
        else:
            self._conn.send(FS_ERR_COMMAND_NOT_FOUND)
        return True

    def _generate_events(self):
        while not self._do_exit.is_set():
            for event in self._events:
                if event.get_header('Event-Type') in self._event_types or \
                    event.get_header('Event-Type') == 'CUSTOM' and \
                    event.get_header('Event-Subclass') in self._custom_event_subtypes:
                    try:
                        self._conn.send(event.serialize().encode('ascii'))
                    except BrokenPipeError:
                        return