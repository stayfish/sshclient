import re
import socket
import time

import paramiko

import os
import sys
class Ssh2Client:
    def __init__(self, host: str, port: int):
        self.__host = host
        self.__port = port
        self.__ssh = None
        self.__channel = None

        # 7-bit C1 ANSI sequences
        self.__ansi_escape = re.compile(r'''
                \x1B  # ESC
                (?:   # 7-bit C1 Fe (except CSI)
                [@-Z\\-_]
                |     # or [ for CSI, followed by a control sequence
                \[
                [0-?]*  # Parameter bytes
                [ -/]*  # Intermediate bytes
                [@-~]   # Final byte
            )
        ''', re.VERBOSE)

    def __del__(self):
        self.__close()

    def connect(self, user: str, pwd: str) -> bool:
        self.__close()

        self.__ssh = paramiko.SSHClient()
        self.__ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.__ssh.connect(self.__host, username=user, password=pwd, port=self.__port)
        return True

    def exec(self, cmd: str, end_str=('# ', '$ ', '? ', '% '), timeout=30):
        if not self.__channel:
            self.__channel = self.__ssh.invoke_shell(term='xterm', width=4096, height=48)
            time.sleep(0.020)
            result = self.__channel.recv(4096).decode()
            print(result, end='')
            result = self.__channel.recv(4096).decode()
            print(result, end='')
        while True:
            cmd = input('')
            for i in range(0, len(cmd)):
                print(int(i))
            if cmd.endswith('\n'):
                self.__channel.send(cmd)
            else:
                self.__channel.send(cmd + '\n')
            if cmd.strip().lower() == 'exit':
                break
            result = self.__recv(self.__channel, end_str, timeout)
            print(result, end='')
            # begin_pos = result.find('\r\n')
            # end_pos = result.rfind('\r\n')
            # if begin_pos == end_pos:
            #     return ''
        return
    def __recv(self, channel, end_str, timeout) -> str:
        result = ''
        out_str = ''
        max_wait_time = timeout * 1000
        channel.settimeout(0.05)
        while max_wait_time > 0:
            try:
                out = channel.recv(1024 * 1024).decode()

                if not out or out == '':
                    continue
                out_str = out_str + out

                match, result = self.__match(out_str, end_str)
                if match is True:
                    return result.strip()
                else:
                    max_wait_time -= 50
            except socket.timeout:
                max_wait_time -= 50

        raise Exception('recv data timeout')

    def __match(self, out_str: str, end_str: list) -> (bool, str):
        result = self.__ansi_escape.sub('', out_str)

        for it in end_str:
            if result.endswith(it):
                return True, result
        return False, result

    def __close(self):
        if not self.__ssh:
            return
        self.__ssh.close()
        self.__ssh = None
