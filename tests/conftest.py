import multiprocessing
import socket
from fake_fs import FakeFS
import pytest
import time
import select

def _process_connection(conn: socket.socket, addr: str, password: str,
                       do_exit: multiprocessing.Event,
                       conn_success: multiprocessing.Event,
                       events):
    fake_fs = FakeFS(conn, addr, password, do_exit, conn_success, events)
    fake_fs.run()

def _run_server(do_exit: multiprocessing.Event,
               conn_success: multiprocessing.Event,
               events):
    fs = socket.socket()
    fs.bind(('127.0.0.1', 8021))
    fs.listen()
    while not do_exit.is_set():
        readers, writers, errs = select.select([fs], [], [])
        if fs in readers:
            (conn, addr) = fs.accept()
            l_process = multiprocessing.Process(target=_process_connection,
                                                args=(conn, addr, 'ClueCon',
                                                      do_exit, conn_success, events))
            l_process.start()
        time.sleep(0.01)

    fs.close()
    for l_process in multiprocessing.active_children():
        l_process.join(1)
        l_process.terminate()
        l_process.join()

@pytest.fixture
def fake_fs_connected(request):
    do_exit = multiprocessing.Event()
    conn_success = multiprocessing.Event()
    process = multiprocessing.Process(target=_run_server, args=(do_exit, conn_success, request.param))
    process.start()
    time.sleep(0.1)

    yield conn_success

    do_exit.set()
    process.join(2)
    process.terminate()
    process.join()
    time.sleep(0.1)
