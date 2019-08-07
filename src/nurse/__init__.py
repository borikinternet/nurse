import ESL

class Nurse:

    def __init__(self, addr: str, port: int, password: str, run_circles: int):
        self._esl = ESL.ESLconnection(addr, str(port), password)
        self._handlers = dict()
        self._run_circles = run_circles
        if not self._esl.connected():
            raise Exception('Connection to FreeSWITCH failed!')

    def set_event_handler(self, event: str, handler: callable):
        self._handlers[event] = handler

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
            if h_name in self._handlers:
                self._handlers[h_name](e)
            # todo add monitoring
        self._esl.disconnect()
