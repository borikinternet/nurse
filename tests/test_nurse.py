import pytest
import multiprocessing
import sys
import fake_fs
sys.path.extend(['./src'])
from nurse import Nurse

def test_nurse_connection_exception():
    with pytest.raises(Exception) as exc_info:
        nurse = Nurse('127.0.0.1', 8021, 'ClueCon', -1)
        assert 'Connection to FreeSWITCH failed!' in str(exc_info.value)

empty_event_list = multiprocessing.Array('I', [])
ds_event_list = multiprocessing.Array('I', [fake_fs.DS_EVENT])
all_event_list = multiprocessing.Array('I', [fake_fs.DS_EVENT, fake_fs.UPE_EVENT])
upe_event_list = multiprocessing.Array('I', [fake_fs.UPE_EVENT])

class TestNurse(object):

    @pytest.mark.parametrize('fake_fs_connected', [empty_event_list], indirect=['fake_fs_connected'])
    def test_nurse_connection(self, fake_fs_connected):
        nurse = Nurse('127.0.0.1', 8021, 'ClueCon', 1000)
        assert fake_fs_connected.is_set()

    @pytest.mark.timeout(15)
    @pytest.mark.parametrize('fake_fs_connected, wait_exception, event_name',
                             [(ds_event_list, False, 'DETECTED_SPEECH'),
                              (all_event_list, False, 'DETECTED_SPEECH'),
                              (upe_event_list, True, 'DETECTED_SPEECH'),
                              (upe_event_list, False, 'CUSTOM unimrcp::profile_error'),
                              (empty_event_list, True, 'DETECTED_SPEECH')],
                             indirect=['fake_fs_connected'])
    def test_nurse_subscribed(self, fake_fs_connected, wait_exception, event_name):
        _a = False
        def handler(event):
            nonlocal _a
            _a = True

        nurse = Nurse('127.0.0.1', 8021, 'ClueCon', 1000)
        if event_name.find('CUSTOM ') != -1:
            handler_name = event_name[event_name.find('CUSTOM ') + len('CUSTOM '):]
        else:
            handler_name = event_name
        nurse.set_event_handler(handler_name, handler)
        nurse.subscribe(event_name)
        nurse.run()

        assert fake_fs_connected.is_set()
        assert _a ^ wait_exception
