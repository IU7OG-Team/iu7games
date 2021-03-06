"""
    ===== STRTOK RUNNER v.1.3c =====
    Copyright (C) 2019 - 2020 IU7Games Team.

    - Данный скрипт предназначен для тестирования самописной функции strtok,
    реализованной на СИ. Функция на СИ имеет сигнатуру:

    - char *strtok(char *string, const char *delim)

    - char *string - указатель на начало разбиваемой строки
    - const char *delim - указатель на начало строки с разделителями

    - Возвращаемое значение: указатель на следующий элемент
    после первого встреченного делителя.
    - Функция должна полностью повторять поведение стандартного strtok (c99).
"""


import ctypes
from timeit import Timer
from time import process_time_ns
from functools import partial
import games.utils.utils as utils

STRING_MULTIPLIER = 1500
TIMEIT_REPEATS = 1
TIME_COUNTER_REPEATS = 11


def check_strtok_correctness(player_ptr, correct_ptr):
    """
        Проверка корректности возвращаемого указателя
        из функции strtok, сравнение со стандартным поведением
        функции в СИ.
    """

    if (player_ptr.value is None) != (correct_ptr.value is None):
        return utils.Error.invalid_ptr

    if player_ptr.value is not None:
        if player_ptr.value.decode(utils.Constants.utf_8) != correct_ptr.value.decode(utils.Constants.utf_8):
            return utils.Error.invalid_ptr

    return utils.GameResult.okay


def create_c_objects(bytes_string, delimiters):
    """
        Создание объектов для языка СИ, используемых функцией strtok
        1. c_delimiters_string - массив символов-компараторов (char *delim)
        2. c_string_player - массив символов для игрока (const char *string)
        3. c_string - массив символов для проверки ходов игрока (const char *string)
    """

    c_delimiters_string = ctypes.create_string_buffer(delimiters)
    c_string = ctypes.create_string_buffer(bytes_string)
    c_string_player = ctypes.create_string_buffer(bytes_string)

    return c_delimiters_string, c_string, c_string_player


def strtok_iteration(c_delimiters_string, c_string_player, c_string, libs):
    """
        Запуск одной итерации функции strtok игрока,
        и одной итерации функци strtok из стандартной билиотеки.
        Сравнение возвращаемых результатов этих функций.
    """

    player_ptr = libs["player"].strtok(c_string_player, c_delimiters_string)
    libary_ptr = libs["libary"].strtok(c_string, c_delimiters_string)

    player_ptr = ctypes.cast(player_ptr, ctypes.c_char_p)
    libary_ptr = ctypes.cast(libary_ptr, ctypes.c_char_p)
    error_code = check_strtok_correctness(player_ptr, libary_ptr)

    return error_code, libary_ptr


def strtok_time_counter(test_data, delimiters, iterations, player_lib_name):
    """
        Запуск strtok без проверки на корректность действий,
        для замеров времени.
    """

    test_data *= STRING_MULTIPLIER
    bytes_string = test_data.encode(utils.Constants.utf_8)
    iterations *= STRING_MULTIPLIER

    c_strtok_timer = ctypes.CDLL("strtok_timer.so")
    player_name = ctypes.create_string_buffer(
        player_lib_name.encode(utils.Constants.utf_8))
    run_time_info = []

    def timeit_wrapper():
        """
            Обёртка для timeit.
        """

        c_strtok_timer.strtok_wrapper(
            player_name, c_string_player,
            c_delimiters_string, ctypes.c_int(iterations)
        )

    for _ in range(TIME_COUNTER_REPEATS):
        c_delimiters_string, _, c_string_player = \
            create_c_objects(
                bytes_string, delimiters.encode(utils.Constants.utf_8))

        run_time_info.append(
            Timer(timeit_wrapper, process_time_ns).timeit(TIMEIT_REPEATS))

    median, dispersion = utils.process_time(run_time_info)
    return median, dispersion


def run_strtok_test(delimiters, libs, player_name, test_data):
    """
        Запуск функции strtok, пока исходная строка не будет
        полностью уничтожена (функция strtok вернёт NULL).
        Сначала тестируется корректность работы функции, далее
        замеряется время работы.
    """

    bytes_string = test_data.encode(utils.Constants.utf_8)
    c_delimiters_string, c_string, c_string_player = \
        create_c_objects(
            bytes_string, delimiters.encode(utils.Constants.utf_8))

    error_code, std_ptr = \
        strtok_iteration(c_delimiters_string, c_string_player, c_string, libs)

    iterations = 0
    while std_ptr.value is not None and not error_code:
        error_code, std_ptr = strtok_iteration(
            c_delimiters_string, utils.Constants.null, utils.Constants.null, libs)
        iterations += 1

    if error_code == utils.GameResult.okay:
        run_time, dispersion = strtok_time_counter(
            test_data, delimiters, iterations, player_name)
    else:
        run_time, dispersion = 0.0, 0.0

    return run_time, error_code, dispersion


def start_strtok(player_lib_name, tests_path):
    """
        Открытие библиотек, запуск ранера, печать результатов.
    """

    # utils.redirect_ctypes_stdout()
    utils.print_memory_usage("STRTOK START")

    lib_player = ctypes.CDLL(player_lib_name)
    libc = ctypes.CDLL("libc.so.6")
    libc.strtok.restype = ctypes.POINTER(ctypes.c_char)
    lib_player.strtok.restype = ctypes.POINTER(ctypes.c_char)
    libs = {"player": lib_player, "libary": libc}

    incorrect_test, total_time, dispersion = utils.strgame_runner(
        tests_path,
        partial(run_strtok_test, utils.Constants.strtok_delimiters,
                libs, player_lib_name)
    )

    utils.print_strgame_results(
        "STRTOK", incorrect_test, total_time, dispersion)

    return incorrect_test, total_time, dispersion


if __name__ == "__main__":
    start_strtok("games/strgame/strtok_lib.so", "games/strgame/tests/strtok")
