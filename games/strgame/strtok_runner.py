"""
    strtok runner v.1.2

    Данный скрипт предназначен для тестирования самописной функции strtok,
    реализованной на СИ. Функция на СИ имеет сигнатуру:

    char *strtok(char *string, const char *delim)

    char *string - указатель на начало разбиваемой строки
    const char *delim - указатель на начало строки с разделителями

    Возвращаемое значение: указатель на следующий элемент
    после первого встреченного делителя.
    Функция должна полностью повторять поведение стандартного strtok c99.
"""


import ctypes
from timeit import Timer
from time import process_time_ns
from functools import partial
from games.strgame.runner import runner

OK = 0
INVALID_PTR = 1

DELIMITERS = " ,.;:"
ENCODING = "utf-8"
NULL = 0

TIMEIT_REPEATS = 1


def check_strtok_correctness(player_ptr, correct_ptr):
    """
        Проверка корректности возвращаемого указателя
        из функции strtok, сравнение со стандартным поведением
        функции в СИ.
    """

    if not player_ptr and correct_ptr:
        return INVALID_PTR

    if player_ptr.value is not None:
        if player_ptr.value.decode(ENCODING) != correct_ptr.value.decode(ENCODING):
            return INVALID_PTR

    return OK


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
        Замеры времени ранинга с помощью timeit.

        libs[0] - lib_player (библиотека с функцией игрока)
        libs[1] - libc (стандартная бибилотека СИ)
    """

    player_ptr = libs[0].strtok(c_string_player, c_delimiters_string)
    libary_ptr = libs[1].strtok(c_string, c_delimiters_string)

    error_code = check_strtok_correctness(
        ctypes.cast(player_ptr, ctypes.c_char_p),
        ctypes.cast(libary_ptr, ctypes.c_char_p)
    )

    return error_code, ctypes.cast(libary_ptr, ctypes.c_char_p)


def strtok_timer(player_lib, c_string_player, c_delimiters_string):
    """
        Простой запуск strtok без проверки на корректность
        для замеров времени.
    """

    player_ptr = player_lib.strtok(c_string_player, c_delimiters_string)
    while player_ptr.value is not None:
        player_ptr = player_lib.strtok(NULL, c_delimiters_string)


def run_strtok_test(delimiters, libs, test_data):
    """
        Запуск функций strtok, пока исходная строка не будет
        полностью уничтожена (функция strtok вернёт NULL).
    """

    bytes_string = test_data.encode(ENCODING)
    c_delimiters_string, c_string, c_string_player = \
        create_c_objects(bytes_string, delimiters.encode(ENCODING))

    error_code, std_ptr = \
        strtok_iteration(c_delimiters_string, c_string_player, c_string, libs)

    while std_ptr.value is not None and not error_code:
        error_code, std_ptr = strtok_iteration(c_delimiters_string, NULL, NULL, libs)

    timeit_timer = Timer(
        partial(strtok_timer, libs[0], c_string_player, c_delimiters_string),
        process_time_ns
    )

    run_time = timeit_timer.timeit(TIMEIT_REPEATS)

    return run_time, error_code


def start_strtok(player_lib, tests_dir):
    """
        Открытие библиотек, запуск ранера, печать результатов.
    """

    lib_player = ctypes.CDLL(player_lib)
    libc = ctypes.CDLL("libc.so.6")
    libc.strtok.restype = ctypes.POINTER(ctypes.c_char)
    lib_player.strtok.restype = ctypes.POINTER(ctypes.c_char)

    total_tests, total_time = runner(
        tests_dir,
        partial(run_strtok_test, DELIMITERS, [lib_player, libc])
    )

    print("STRTOK TESTS:", total_tests, "/ 1 TIME:", total_time)
    return total_tests, total_time


if __name__ == "__main__":
    start_strtok("./strtok_lib.so", "tests/strtok")
