#  Copyright (c) 2020. borik.internet@gmail.com
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

import pytest
import pytest_rabbitmq
import multiprocessing
import sys
import fake_fs
sys.path.extend(['./src'])
from nurse import Nurse
import handlers


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

        nurse = Nurse(run_circles=1000)
        if event_name.find('CUSTOM ') != -1:
            handler_name = event_name[event_name.find('CUSTOM ') + len('CUSTOM '):]
        else:
            handler_name = event_name
        nurse.set_event_handler(handler_name, handler)
        nurse.subscribe(event_name)
        nurse.run()

        assert fake_fs_connected.is_set()
        assert _a ^ wait_exception

    @pytest.mark.timeout(15)
    @pytest.mark.parametrize('fake_fs_connected, wait_exception, event_name',
                             [(ds_event_list, False, 'DETECTED_SPEECH'),
                              (all_event_list, False, 'DETECTED_SPEECH'),
                              (empty_event_list, True, 'DETECTED_SPEECH')],
                             indirect=['fake_fs_connected'])
    def test_nurse_multihandlers(self, fake_fs_connected, wait_exception, event_name):
        _a = False
        _b = False

        def handle_a(event):
            nonlocal _a
            _a = True

        def handle_b(event):
            nonlocal _b
            _b = True

        nurse = Nurse(run_circles=1000)
        if event_name.find('CUSTOM ') != -1:
            handler_name = event_name[event_name.find('CUSTOM ') + len('CUSTOM '):]
        else:
            handler_name = event_name
        nurse.set_event_handler(handler_name, handle_a)
        nurse.set_event_handler(handler_name, handle_b)
        nurse.subscribe(event_name)
        nurse.run()

        assert fake_fs_connected.is_set()
        assert _a ^ wait_exception
        assert _b ^ wait_exception


class TestHandlers(object):

    @pytest.mark.timeout(15)
    @pytest.mark.parametrize('fake_fs_connected, wait_exception, event_name, rabbitmq_proc',
                             [(ds_event_list, False, 'DETECTED_SPEECH', None),
                              (all_event_list, False, 'DETECTED_SPEECH', None),
                              (upe_event_list, True, 'DETECTED_SPEECH', None),
                              (empty_event_list, True, 'DETECTED_SPEECH', None)],
                             indirect=['fake_fs_connected', 'rabbitmq_proc'])
    def test_handler_detected_speech(self, fake_fs_connected, wait_exception, event_name, rabbitmq_proc):
        ds_handler = handlers.DetectedSpeechHandler()
        nurse = Nurse(run_circles=1000)
        nurse.set_event_handler(event_name, ds_handler)
        nurse.subscribe(event_name)
        nurse.run()
        # todo принять в RabbitMQ и потом проверить на наличие в очереди сообщение:
        """
        queue name: 'garm_borik asr_health'
        method: 'change_profile'
        args: []
        kwargs: {bad_profile=???}
        """
        # todo записать в tarantool значение переменной asr_last_profile в формате,
        #  который будет понятен объекту RobotHandler
        # todo подключить репо twin, что б импортировать в тест класс ASR_Health

    @pytest.mark.timeout(15)
    @pytest.mark.parametrize('fake_fs_connected, wait_exception, event_name, rabbitmq_proc',
                             [(ds_event_list, False, 'DETECTED_SPEECH', None),
                              (all_event_list, False, 'DETECTED_SPEECH', None),
                              (upe_event_list, True, 'DETECTED_SPEECH', None),
                              (upe_event_list, False, 'CUSTOM unimrcp::profile_error', None),
                              (empty_event_list, True, 'DETECTED_SPEECH', None)],
                             indirect=['fake_fs_connected', 'rabbitmq_proc'])
    def test_handler_custom_unimrcp_profile_error(self, fake_fs_connected, wait_exception, event_name, rabbitmq_proc):
        pass
