"""
          ===== RUNNERS UTILS v.1.0b =====
          Copyright (C) 2019 - 2020 IU7Games Team.

        - Модуль с функциями и константами, которые вызываются в нескольких ранерах.
"""


import sys
import os
import subprocess
import logging
from dataclasses import dataclass
from statistics import median, pvariance
from functools import reduce
from multiprocessing import Process, Value
from psutil import virtual_memory


@dataclass
class GameResult:
    """
        Константы представления рез-ов игр
    """
    okay = 0
    fail = 1
    no_result = -1337


@dataclass
class Error:
    """
        Константы представления ошибок
    """
    invalid_ptr = 1
    segfault = -1
    char_segfault = '0'
    ptr_segfault = '0'
    memory_leak = -2
    memory_leak_check_error = -3


@dataclass
class Constants:
    """
        Прочие константы утилит
    """
    sample_path = "/c_samples"
    memory_leak_executable_path = "/sandbox/memory_leak_check.out"
    utf_8 = "utf-8"
    test_file = "/test_data.txt"
    strtok_delimiters = " ,.;:"
    split_delemiter = ' '
    null = 0


def call_libary(player_lib, wrapper, argtype, stdval, *args):
    """
        Вызов функции игрока с помощью multiprocessing, для отловки segfault.
    """

    move = Value(argtype, stdval)
    proc = Process(target=wrapper, args=(player_lib, move, *args))

    try:
        proc.start()
        proc.join()
    except OSError as error:
        print(f"Ctypes call error: {error}") # return out of memory?

    return move.value


def print_memory_usage(stage):
    """
        Печать текущего состояния использования памяти
    """

    memory_usage = virtual_memory()

    print(
        f"STAGE: {stage} "
        f"AVAILABLE MEMORY: {memory_usage[1]} "
        f"USAGE PERCENTAGE: {memory_usage[2]}"
    )


def memory_leak_check(sample_path, lib_path, sample_args):
    """
        Проверка наличия утечек памяти через valgrind

        sample_path - полный путь до тестовой программы
        lib_path - полный путь до тестируемой библиотеки
        sample_args - аргументы запуска тестовой программы

        Возвращаемое значение - кол-во утечек
    """

    path = lib_path.split('/')
    process = subprocess.run(
        [
            "gcc",
            "--std=c99",
            "-O3",
            "-L" + "/".join(path[:-1]),
            "-Wl,-rpath=" + "/".join(path[:-1]),
            "-o",
            Constants.memory_leak_executable_path,
            sample_path,
            "-l:" + path[-1]
        ],
        stderr=subprocess.PIPE,
        check=False
    )
    del path

    if process.returncode != 0:
        logging.error('\n%s', process.stderr.decode(Constants.utf_8).rstrip())
        logging.error("Sample path is %s", sample_path)
        logging.error("Lib path is %s", lib_path)
        logging.error("Sample args is %s\n", str(sample_args))
        return -1

    process = subprocess.run(
        [
            "valgrind",
            "--quiet",
            "--verbose",
            "--leak-check=full",
            "--show-leak-kinds=all",
            "--track-origins=yes",
            "--error-exitcode=1",
            Constants.memory_leak_executable_path
        ] + sample_args,
        stderr=subprocess.PIPE,
        check=False
    )

    if process.returncode != 0:
        logging.error('\n%s', process.stderr.decode(Constants.utf_8).rstrip())
        logging.error("Sample path is %s", sample_path)
        logging.error("Lib path is %s", lib_path)
        logging.error("Sample args is %s\n", str(sample_args))
        return -1

    subprocess.run(["rm", Constants.memory_leak_executable_path], check=True)

    check_res = process.returncode
    return -1 if check_res else int(next(filter(
        lambda x: x.isdigit(),
        process.stderr.decode(Constants.utf_8).split("\n")[-2].split()
    )))


def redirect_ctypes_stdout():
    """
        Выключение принтов в стратегиях игроков.
    """

    new_stdout = os.dup(1)
    sys.stdout.flush()
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 1)
    os.close(devnull)
    sys.stdout = os.fdopen(new_stdout, 'w')


def process_time(time_results):
    """
        Обработка результатов (по времени) игрока. Подсчёт медианы и дисперсии.
    """

    return median(time_results), pvariance(time_results)


def parsing_name(lib_path):
    """
        Преобразование полного пути к файлу с библиотекой игрока
        к gitlab логину игрока.
    """
    return lib_path[lib_path.rindex('/') + 1: len(lib_path) - 3]


def start_game_print(player1, player2):
    """
        Информация о начале раунда.
    """

    print(
        f"GAME",
        f"{parsing_name(player1)} VS",
        f"{parsing_name(player2)}"
    )


def end_game_print(player, info, space_amount):
    """
        Печать результатов раунда.
    """

    print(
        f"{parsing_name(player)} {info} \n",
        f"{'=' * space_amount}", sep=""
    )


def print_score_results(points, players_info, players_amount):
    """
        Печать результатов в виде:
        ИГРОК : ОЧКИ
    """

    for i in range(players_amount):
        if players_info[i][0] != "NULL":
            print(
                f"PLAYER: {parsing_name(players_info[i][0])} ",
                f"POINTS: {points[i]}"
            )


def print_strgame_results(game, incorrect_test, total_time, dispersion):
    """
        Печать результатов для STRGAME.
    """

    print(
        f"{game} TESTS: {'FAIL' if incorrect_test else 'OK'} "
        f"TIME: {total_time} "
        f"DISPERSION: {dispersion}"
    )


def print_time_results(results, players_info):
    """
        Печать финальных результатов для каждого игрока.
    """

    for player, result in zip(players_info, results):
        if player != "NULL":
            print(
                f"PLAYER: {parsing_name(player)} ",
                f"SOLUTION: {'FAIL' if result[0] else 'OK'} ",
                f"MEDIAN: {result[1]} ",
                f"DISPERSION: {result[2]}"
            )


def concat_strings(f_obj):
    """
        Склеивание каждой строки файла в одну единственную строку,
        удаление символов окончания строки.
    """

    return reduce(lambda x, y: x + y[:-1], f_obj)


def strgame_runner(tests_path, tests_runner):
    """
        Универсальная функция, производящая запуск STR игр (split, strtok)
    """

    with open(tests_path + Constants.test_file, "r") as f_obj:
        test_data = concat_strings(f_obj)

    time, error_code, dispersion = tests_runner(test_data)

    return error_code, time, dispersion


def calculate_coefficient(pts):
    """
        Подсчёт коэффициента, который отвечает за
        балансировку набора очков.
    """

    if pts > 2400:
        return 10

    if pts > 1800:
        return 20

    return 40


def calculate_expectation(pts1, pts2):
    """
        Подсчёт математического ожидания.
    """

    return 1 / (1 + 10 ** ((pts2 - pts1) / 400))


def calculate_elo_rating(pts1, pts2, result):
    """
        Подсчёт рейтинга Эло.
    """

    expected_value = calculate_expectation(pts1, pts2)
    coefficient = calculate_coefficient(pts1)
    pts1 += coefficient * (result - expected_value)

    return pts1
