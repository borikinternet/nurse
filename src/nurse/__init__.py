import ESL

class Nurse:

    def __init__(self, addr: str, port: int, password: str):
        self._esl = ESL.ESLconnection(addr, str(port), password)
        if not self._esl.connected():
            raise Exception('Connection to FreeSWITCH failed!')
