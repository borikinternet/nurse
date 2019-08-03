import multiprocessing
import socket
import sys
import pytest
import time
sys.path.extend(['./src'])
from nurse import Nurse
# import pydevd_pycharm

FS_AUTH_ACCEPTED_REPLY = b'Content-Type: command/reply\nReply-Text: +OK accepted\n\n'
FS_AUTH_DENIED_REPLY = b'Content-Type: command/reply\nReply-Text: -ERR invalid\n\n'
FS_EXIT_REPLY = b'Content-Type: command/reply\nReply-Text: +OK bye\n\n'
FS_ERR_COMMAND_NOT_FOUND = b'Content-Type: command/reply\nReply-Text: -ERR command not found\n\n'
FS_DISCONNECT_NOTICE = b'Content-Type: text/disconnect-notice\nContent-Length: 67'
FS_AUTH_INVITE = b'Content-Type: auth/request\n\n'

class FakeFS(object):

    def __init__(self, conn: socket.socket, addr: str, password: str) -> None:
        self._conn = conn
        self._addr = addr
        self._password = password

    def run(self, do_exit: multiprocessing.Event,
            conn_success: multiprocessing.Event):
        import logging
        logging.warning('Fake FS connection child started')
        self._conn.send(FS_AUTH_INVITE)
        buf = ''
        while not do_exit.is_set():
            l_buf = self._conn.recv(256)
            if not l_buf: break
            buf += l_buf.decode('ascii')
            while not buf.find('\n\n') == -1:
                if not self._process_message(buf[:buf.find('\n\n')], conn_success): return
                buf = buf[buf.find('\n\n')+2:]

    def _process_message(self, msg: str,
                         conn_success: multiprocessing.Event) -> bool:
        import logging
        if msg.find(' '):
            cmd = msg[:msg.find(' ')]
        else:
            cmd = msg
        logging.warning('Message: %s' % msg)
        if cmd == 'auth':
            if msg[msg.find(' ')+1:] == self._password:
                self._conn.send(FS_AUTH_ACCEPTED_REPLY)
                conn_success.set()
            else:
                self._conn.send(FS_AUTH_DENIED_REPLY)
                self._conn.send(FS_DISCONNECT_NOTICE)
                self._conn.close()
                return False
        elif cmd == 'exit':
            self._conn.send(FS_EXIT_REPLY)
            self._conn.send(FS_DISCONNECT_NOTICE)
            self._conn.close()
            return False
        else:
            logging.warning('Unknown command: %s' % cmd)
            self._conn.send(FS_ERR_COMMAND_NOT_FOUND)
        return True


class TestNurse(object):

    @pytest.mark.timeout(5)
    def test_nurse_connection(self):
        def process_connection(conn: socket.socket, addr: str, password: str,
                               do_exit: multiprocessing.Event,
                               conn_success: multiprocessing.Event):
            import logging

            logging.warning('Accepted new connection')
            fake_fs = FakeFS(conn, addr, password)
            fake_fs.run(do_exit, conn_success)

        def run_server(do_exit: multiprocessing.Event,
                                conn_success: multiprocessing.Event):
            import logging
            logging.warning('Starting server')
            fs = socket.socket()
            fs.bind(('127.0.0.1', 8021))
            fs.listen()
            while not do_exit.is_set():
                (conn, addr) = fs.accept()
                l_process = multiprocessing.Process(target=process_connection,
                                                    args=(conn, addr, 'ClueCon',
                                                          do_exit, conn_success))
                l_process.daemon = True
                l_process.start()

            for l_process in multiprocessing.active_children():
                l_process.terminate()
                l_process.join()

            logging.warning('All forked procs are stopped')

        do_exit = multiprocessing.Event()
        conn_success = multiprocessing.Event()

        process = multiprocessing.Process(target=run_server, args=(do_exit, conn_success))
        process.start()
        time.sleep(0.1)

        nurse = Nurse('127.0.0.1', 8021, 'ClueCon')

        process.terminate()
        process.join()

        assert conn_success.is_set()

    def test_nurse_connection_exception(self):
        with pytest.raises(Exception) as exc_info:
            nurse = Nurse('127.0.0.1', 8021, 'ClueCon')
            assert 'Connection to FreeSWITCH failed!' in str(exc_info.value)

if __name__ == '__main__':
    test = TestNurse()
    test.test_nurse_connection()