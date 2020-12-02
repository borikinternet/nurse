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

import ESL


class Nurse:

    def __init__(self, addr: str = '127.0.0.1', port: int = 8021, password: str = 'ClueCon', run_circles: int = -1):
        self._esl = ESL.ESLconnection(addr, str(port), password)
        self._handlers = []
        self._run_circles = run_circles
        if not self._esl.connected():
            raise Exception('Connection to FreeSWITCH failed!')

    def set_event_handler(self, event: str, handler: callable):
        self._handlers.append({
            'event': event,
            'handler': handler
        })

    def subscribe(self, event: str):
        self._esl.send('event plain %s' % event)

    def run(self):
        i = self._run_circles
        while i:
            e = self._esl.recvEventTimed(10)
            if i > 0: i -= 1
            if not e: continue
            if e.getHeader('Event-Type') == 'CUSTOM':
                h_name = e.getHeader('Event-Subclass')
            else:
                h_name = e.getHeader('Event-Type')
            for handler in self._handlers:
                if h_name == handler['event']:
                    handler['handler'](e)
            # todo add monitoring
        self._esl.disconnect()
