"""
      ===== NUMBERS RUNNER v.1.0a =====
      Copyright (C) 2019 IU7Games Team.

      - Ранер для игры NUM63RSGAME, суть которой заключается в получении
        минимально возможного числа, который делится на все числа на интервале [a, b]

      - В соревновании принимают функции, имеющие следующую сигнатуру:
      - int numbers_game(int min, int max)

      - int min - левая граница интервала
      - int max - правая граница интервал

      - Возвращаемое значение: минимально возможное число, являющееся решением задачи.
"""

import ctypes
from worker.wiki import NO_RESULT
from random import randint
from timeit import Timer
from time import process_time_ns
from math import sqrt

MAX_LBORDER = 1
MAX_RBORDER = 22

TIMEIT_REPEATS = 10001


def parsing_name(lib_path):
    """
        Преобразование полного пути к файлу с библиотекой игрока
        к gitlab логину игрока.
    """
    return lib_path[lib_path.rindex('/') + 1: len(lib_path) - 3]


def print_results(results, players_info):
    """
        Печать финальных результатов для каждого игрока.
    """

    for i in range(len(players_info)):
        if players_info[i] != "NULL":
            print(
                "PLAYER:", parsing_name(players_info[i]),
                "SOLUTION:", results[i]["solution"],
                "MEDIAN:", results[i]["median"],
                "DISPERSON:", results[i]["dispersion"]
            )


def round_intervals():
    """
        Генерация левой, правой границы интервала и решения для текущего раунда.
    """

    lib = ctypes.CDLL("solution_hs.so")

    left_border = randint(MAX_LBORDER, MAX_RBORDER)
    right_border = randint(left_border, MAX_RBORDER)

    lib.hs_init(0, 0)
    solution = lib.solution_hs(left_border, right_border)
    lib.hs_exit()

    return {"l_border": right_border, "r_border": left_border, "solution": solution}


def player_results(player_lib, intervals):
    """
        Получение и обработка результатов игрока. Подсчёт времени выполнения его функции.
    """

    player_solution = player_lib.numbers_game(intervals["l_border"], intervals["r_border"])
    if player_solution != intervals["solution"]:
        return {"solution": False, "median": 0, "dispersion": 0}

    def timeit_wrapper():
        """
            Обёртка для Timeit.
        """

        player_lib.numbers_game(intervals["l_border"], intervals["r_border"])

    time_results = Timer(timeit_wrapper, process_time_ns).repeat(TIMEIT_REPEATS, 1)
    time_results.sort()

    median = time_results[TIMEIT_REPEATS // 2]
    avg_time = sum(time_results) / len(time_results)
    time_results = list(map(lambda x: (x - avg_time) * (x - avg_time), time_results))
    dispersion = sqrt(sum(time_results) / len(time_results))

    return {"solution": True, "median": median, "dispersion": dispersion}


def start_numbers_game(players_info):
    """
        Открытие библиотек с функциями игроков, подсчёт времени исполнения их функций,
        печать результатов.
    """

    intervals = round_intervals()
    results = []

    for player_lib in players_info:
        if player_lib != "NULL":
            lib = ctypes.CDLL(player_lib)
            results.append(player_results(lib, intervals))
        else:
            results.append((NO_RESULT, 0, 0))

    print_results(results, players_info)
    return results

if __name__ == "__main__":
    start_numbers_game(["./test.so", "NULL"])
