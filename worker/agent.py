"""
    Агент для запуска соревнований IU7Games Project.
"""

import os
import argparse

import gitlab
import worker.wiki
import worker.repo
from games.strgame import split_runner, strtok_runner


GIT_INST = gitlab.Gitlab.from_config("gitiu7", ["cfg/api_config.cfg"])
GIT_INST.auth()

IU7GAMES_ID = 2546
IU7GAMES = GIT_INST.projects.get(IU7GAMES_ID)


def start_competition(instance, game, group_name):
    """
        Старт соревнования с собранными стратегиями.
    """

    if game == "STRgame":
        results = worker.repo.get_group_artifacts(instance, game, group_name)
        deploy_job = worker.repo.get_deploy_job(
            IU7GAMES, game.lower(), "develop")
        worker.repo.get_artifacts(IU7GAMES, deploy_job)

        print("STRGAME RESULTS\n")
        for data in results:
            print(f"{data[0]}:")

            try:
                lib_path = os.path.abspath(f"{data[1][1:]}_split_lib.so")
                test_path = os.path.abspath("/tests/strgame/split")
                split_res = split_runner.start_split(lib_path, test_path)
            except OSError:
                split_res = (0, worker.wiki.NO_RESULT, worker.wiki.NO_RESULT)

            data.append(split_res[0])
            data.append(f"{split_res[1]:.7f}±{split_res[2]:.7f}")

            try:
                lib_path = os.path.abspath(f"{data[1][1:]}_strtok_lib.so")
                test_path = os.path.abspath("/tests/strgame/strtok")
                strtok_res = strtok_runner.start_strtok(lib_path, test_path)
            except OSError:
                strtok_res = (0, worker.wiki.NO_RESULT, worker.wiki.NO_RESULT)

            data.append(strtok_res[0])
            data.append(f"{strtok_res[1]:.7f}±{strtok_res[2]:.7f}")

            print()
    elif game == "XOgame":
        pass
    elif game == "TEEN48game":
        pass
    else:
        pass

    worker.wiki.update_wiki(IU7GAMES, game, results)


def add_args():
    """
        Добавление аргументов командной строки для агента.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("game", help="Select a game")
    parser.add_argument("group_name", help="Select a GitLab group")
    args = parser.parse_args()

    return args


if __name__ == "__main__":
    ARGS = add_args()

    start_competition(GIT_INST, ARGS.game, ARGS.group_name)