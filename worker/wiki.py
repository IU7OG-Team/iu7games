"""
    Модуль для работы над Wiki-страницами.
"""


import os
import pickle
import operator
from datetime import datetime
from copy import deepcopy

STRG_TABLE_WIDTH = 6

STRG_TESTS_COL = 2
STRG_RES_COL = 3
STRG_SORT_KEYS = (STRG_TESTS_COL, STRG_RES_COL)

SPLIT_TESTS_COL = 2
SPLIT_STRG_RES_COL = 3
SPLIT_REMOVABLE = (SPLIT_TESTS_COL, SPLIT_STRG_RES_COL)

STRTOK_TESTS_COL = 4
STRTOK_STRG_RES_COL = 5
STRTOK_REMOVABLE = (STRTOK_TESTS_COL, STRTOK_STRG_RES_COL)

XOG_TABLE_WIDTH = 5

XOG_RES_COL = 2
XOG_SORT_KEYS = (XOG_RES_COL, )

XOG_3X3_RES_COL = 2
XOG_5X5_RES_COL = 3

XOG_3X3_REMOVABLE = (XOG_5X5_RES_COL, XOG_5X5_RES_COL)
XOG_5X5_REMOVABLE = (XOG_3X3_RES_COL, XOG_3X3_RES_COL)

NO_RESULT = -1337
NO_RESULT_PRECISE = "-1337.0000000"
MSG = "Отсутствует стратегия"
OUTPUT_PARAMS = (NO_RESULT, MSG, NO_RESULT_PRECISE)

POS_CHANGE = ("🔺", "🔻")


def create_page(project, title, content):
    """
        Создание Wiki-страницы.
    """

    project.wikis.create(
        {
            "title": title,
            "content": content
        }
    )


def update_page(project, page_slug, title, content):
    """
        Обновление Wiki-страницы.
    """

    page = project.wikis.get(page_slug)
    page.title = title
    page.content = content
    page.save()


def delete_page(project, page_slug):
    """
        Удаление Wiki-страницы.
    """

    page = project.wikis.get(page_slug)
    page.delete()


def fix_date(results):
    """
        Перемещение даты завершения job'ы в последний столбец таблицы.
    """

    for rec in results:
        job_date = rec.pop(2)
        rec.append(job_date)

    return results


def form_table(results, removable, sort_keys, output_params, game):
    """
        Предварительное формирование таблицы.
    """

    new = deepcopy(results)

    for rec in new:
        del rec[removable[0]:removable[1] + 1]

    if game == "STRgame":
        new = sorted(new, key=operator.itemgetter(sort_keys[1]))
        new = sorted(new, key=operator.itemgetter(sort_keys[0]), reverse=True)

        for rec in new:
            rec[sort_keys[0]] = f"{str(rec[sort_keys[0]])}/1"

            if rec[sort_keys[1]] == f"{output_params[2]}±{output_params[2]}":
                rec[sort_keys[1]] = output_params[1]

    if game == "XOgame":
        new = sorted(new, key=operator.itemgetter(sort_keys[0]), reverse=True)

        for rec in new:
            if rec[sort_keys[0]] == output_params[0]:
                rec[sort_keys[0]] = 0

    return new


def print_table(head, theme, columns, results, compet):
    """
        Печать таблицы с предопределенной шапкой.
    """

    results_old = []

    if os.path.exists(f"tbdump_{compet}.obj"):
        results_dump = open(f"tbdump_{compet}.obj", "rb")
        results_old = pickle.load(results_dump)

    res = theme + head

    prize = {1: "🥇", 2: "🥈", 3: "🥉"}

    num = 1
    for i in range(len(results)):
        place = prize.setdefault(num, str(num))

        for j in range(len(results_old)):
            if results[i][1] == results_old[j][1]:
                if i > j:
                    place += f"{POS_CHANGE[1]}-{i - j}"
                elif i < j:
                    place += f"{POS_CHANGE[0]}+{j - i}"

        res += f"|{place}|"
        for field in range(columns - 1):
            res += f"{results[i][field]}|"
        num += 1
        res += "\n"

    return res


def update_wiki(project, game, results):
    """
        Обновление Wiki-страницы с обновленными результатами.
    """

    games = {
        "XOgame Leaderboard": "XOgame-Leaderboard",
        "STRgame Leaderboard": "STRgame-Leaderboard",
        "TEEN48game Leaderboard": "TEEN48game-Leaderboard"
    }
    games_keys = games.keys()

    res = ""

    results = fix_date(results)

    if game == "STRgame":
        split_theme = "# SPLIT\n\n"
        strtok_theme = "\n# STRTOK\n\n"
        split_head = "|**№**|**ФИ Студента**|**GitLab ID**|**SPLIT Тесты**|"\
            "**SPLIT Время**|**Последнее обновление**|\n"\
            "|---|---|---|---|---|---|\n"
        strtok_head = "|**№**|**ФИ Студента**|**GitLab ID**|**STRTOK Тесты**|"\
            "**STRTOK Время**|**Последнее обновление**|\n"\
            "|---|---|---|---|---|---|\n"

        sorted_split = form_table(
            results, STRTOK_REMOVABLE, STRG_SORT_KEYS, OUTPUT_PARAMS, game)
        sorted_strtok = form_table(
            results, SPLIT_REMOVABLE, STRG_SORT_KEYS, OUTPUT_PARAMS, game)

        res += print_table(split_head, split_theme,
                           STRG_TABLE_WIDTH, sorted_split, "split")
        res += print_table(strtok_head, strtok_theme,
                           STRG_TABLE_WIDTH, sorted_strtok, "strtok")

        split_dump = open("tbdump_split.obj", "wb")
        pickle.dump(sorted_split, split_dump)

        strtok_dump = open("tbdump_strtok.obj", "wb")
        pickle.dump(sorted_strtok, strtok_dump)

    elif game == "XOgame":
        div_3x3_theme = "# 3X3 DIVISION\n\n"
        div_5x5_theme = "\n# 5X5 DIVISION\n\n"
        xo_head = "|**№**|**ФИ Студента**|**GitLab ID**|"\
            "**Очки**|**Последнее обновление**|\n"\
            "|---|---|---|---|---|\n"

        sorted_3x3 = form_table(
            results, XOG_3X3_REMOVABLE, XOG_SORT_KEYS, OUTPUT_PARAMS, game)
        sorted_5x5 = form_table(
            results, XOG_5X5_REMOVABLE, XOG_SORT_KEYS, OUTPUT_PARAMS, game)

        res += print_table(xo_head, div_3x3_theme,
                           XOG_TABLE_WIDTH, sorted_3x3, "xogame_3x3")
        res += print_table(xo_head, div_5x5_theme,
                           XOG_TABLE_WIDTH, sorted_5x5, "xogame_5x5")

        results_3x3_dump = open("tbdump_xogame_3x3.obj", "wb")
        pickle.dump(sorted_3x3, results_3x3_dump)

        results_5x5_dump = open("tbdump_xogame_5x5.obj", "wb")
        pickle.dump(sorted_5x5, results_5x5_dump)

    now = datetime.now()
    date = now.strftime("%d/%m/%Y %H:%M:%S")

    res += f"\n**Обновлено:** {date} **МСК**"

    for key in games_keys:
        if game in key:
            update_page(project, games.get(key), key, res)
