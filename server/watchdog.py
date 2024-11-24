import os
import signal
import threading

global _all_addresses
global _active_address
global _active_player
global _player_name

class Watchdog:

    def __init__(self, timeout=10):
        self.timeout = timeout
        self._t = None

    def do_expire(self):
        #os.kill(os.getpid(),signal.SIGKILL)
        os.kill(os.getpid(),signal.SIGINT)

    def set_addresses(self, address1: tuple, address2: tuple):
        global _all_addresses
        _all_addresses = [tuple(address1), tuple(address2)]

    @staticmethod
    def set_player(addr, player_name):
        global _player_name
        _player_name = player_name

        global _active_player
        global _active_address
        if addr == _all_addresses[0]:
            _active_player = 1
            _active_address = _all_addresses[0]
        else:
            _active_player = 2
            _active_address = _all_addresses[1]

    def _expire(self):
        from server import send_all
        from server import send_msg
        from server import play_again_player

        send_all(f"Partida Encerrada, Jogador P{_active_player} ({_player_name}) está AFK e perdeu 1 ponto no Scoreboard Geral\n", _all_addresses)
        send_msg("terminate", _active_address)

        #tira 1 ponto do jogador AFK
        afk_player = _player_name
        try:
            create_db = open("scoreboard.txt", "x")
        except FileExistsError:
            pass
        edit_db = open("scoreboard.txt", "a")
        read_db = open("scoreboard.txt", "r")
        content = read_db.readlines()
        content_line = -1
        i = 0
        for line in content:
            content_data = content[i].split(" : ")
            if content_data[0] == afk_player:
                content_line = i
                final_points = int(content_data[1]) - 1
                content[i] = f"{afk_player} : {final_points}\n"
                rewrite_db = open("scoreboard.txt", "w")
                rewrite_db.writelines(content)
                rewrite_db.close()
                break
        if content_line == -1:
            edit_db.write(f"{afk_player} : -1\n")
        read_db.close()
        edit_db.close()

        #Pergunta se quer jogar de novo para o jogador que não estava Afk
        if _active_address == _all_addresses[0]:
            play_again_player(_all_addresses[1])
        else:
            play_again_player(_all_addresses[0])

        print("\nWatchdog expire")
        self.do_expire()

    def start(self):
        if self._t is None:
            self._t = threading.Timer(self.timeout, self._expire)
            self._t.start()

    def stop(self):
        if self._t is not None:
            self._t.cancel()
            self._t = None

    def refresh(self):
        if self._t is not None:
             self.stop()
             self.start()