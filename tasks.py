from invoke import task


@task
def build_macos(c):

    tag = c.run("git describe --exact-match --tags", hide=True).stdout.strip()
    c.run(f'flet build macos --build-version {tag} --copyright "César Del Solar"')
    c.run("mv build/macos/tourneypdf.app build/macos/WooglesTournamentManager.app")
    c.run(
        "cd build/macos && tar -cvjSf WooglesTournamentManager.tar.bz2 WooglesTournamentManager.app"
    )
