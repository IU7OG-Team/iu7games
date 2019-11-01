""" Worker for IU7Games project. """


import gitlab
import os
import subprocess
import argparse

from datetime import datetime


def create_page(instance, project, title, content):
    """ Create Wiki page. """

    project.wikis.create(
        {
            "title": title,
            "content": content
        }
    )


def update_page(instance, project, page_slug, title, content):
    """ Update Wiki page. """

    page = project.wikis.get(page_slug)
    page.title = title
    page.content = content
    page.save()


def delete_page(instance, project, page_slug):
    """ Delete Wiki page. """

    page = project.wikis.get(page_slug)
    page.delete()


def get_group(instance, name):
    """ Get group by it's name. """

    group = None

    groups = instance.groups.list(all=True)
    for grp in groups:
        if grp.name == name:
            group = grp

    return group


def get_group_projects(instance, group):
    """ Get group's projects. """

    group = instance.groups.get(group.id)
    projects = group.projects.list(all=True)

    return projects


def get_project(instance, group, name):
    """ Get project by it' name. """

    project = None

    projects = get_group_projects(instance, group)
    for prj in projects:
        if prj.name == name:
            project = instance.projects.get(prj.id)

    return project


def get_last_success_job(project, ref):
    """ Get project's last success job by ref name. """

    job = None

    jobs = project.jobs.list(all=True)
    for jb in jobs:
        if jb.status == "success" and jb.ref == ref:
            job = jb

    return job


def get_artifacts(project, success_job):
    """ Get success job's artifacts. """

    job = project.jobs.get(success_job.id)

    ziparts = job.user.get("username") + ".zip"

    with open(ziparts, "wb") as f:
        job.artifacts(streamed=True, action=f.write)
    subprocess.run(["unzip", "-bo", ziparts])
    os.unlink(ziparts)


def update_wiki(instance, project, game, results):
    """ Update Wiki pages with new games results. """

    games = {
        "XOgame Leaderboard": "XOgame-Leaderboard",
        "STRgame Leaderboard": "STRgame-Leaderboard",
        "TEEN48game Leaderboard": "TEEN48game-Leaderboard"
    }
    games_keys = games.keys()

    res = None

    if game == "strgame":
        res = "|**ФИ Студента**|**GitLab ID**|**SPLIT Тесты**|**SPLIT Время**|" \
            "**STRTOK Тесты**|**STRTOK Время**|\n" \
            "|---|---|---|---|---|---|\n"

        for student in range(len(results)):
            res += "|{0}|{1}|||||\n".format(results[student][0], results[student][1])

    now = datetime.now()
    date = now.strftime("%d/%m/%Y %H:%M:%S")

    res += "\n**Обновлено:** {0} **МСК**".format(date)

    for key in games_keys:
        if game in key.lower():
            update_page(instance, project, games.get(key), key, res)


def start_competition(game, group_name):
    """ Start competition with collected strategies. """

    gl = gitlab.Gitlab.from_config("gitiu7", ["cfg/api_config.cfg"])
    gl.auth()

    group = get_group(gl, group_name)
    projects = get_group_projects(gl, group)

    iu7games_id = 2546
    iu7games = gl.projects.get(iu7games_id)

    results = []

    for prj in projects:
        project = get_project(gl, group, prj.name)
        job = get_last_success_job(project, game)
        user_result = [job.user.get("name"), "@" + job.user.get("username")]
        results.append(user_result)
        get_artifacts(project, job)

    if game == "strgame":
        for data in results:
            subprocess.run(["python3", "games/strgame/split_runner.py", data[1][1:] + "_split_lib.so"])
            # WIP
    elif game == "xogame":
        pass
    elif game == "teen48game":
        pass
    else:
        pass

    update_wiki(gl, iu7games, "strgame", results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("game", help="Select a game to be played")
    parser.add_argument(
        "group_name", help="Select a GitLab group name to be searched")
    args = parser.parse_args()

    start_competition(args.game, args.group_name)
