from invoke import task


@task
def build_macos(c):

    tag = c.run("git describe --exact-match --tags", hide=True).stdout.strip()
    c.run(f'flet build macos --build-version {tag} --copyright "César Del Solar"')
    c.run("mv build/macos/tourneypdf.app build/macos/WooglesTournamentManager.app")
    c.run(
        "cd build/macos && tar -cvjSf WooglesTournamentManager.tar.bz2 WooglesTournamentManager.app"
    )

    # print("Tag was", tag)

    # # Build universal mac executable. This only works on Mac:
    # c.run(f"GOOS=darwin GOARCH=amd64 go build -o macondo-amd64 ./cmd/shell")
    # c.run(f"GOOS=darwin GOARCH=arm64 go build -o macondo-arm64 ./cmd/shell")
    # c.run("lipo -create -output macondo macondo-amd64 macondo-arm64")
    # c.run(f"zip -r macondo-{tag}-osx-universal.zip ./macondo ./data")

    # for os, nickname, arch, executable in [
    #     ("linux", "linux-x86_64", "amd64", "macondo"),
    #     ("windows", "win64", "amd64", "macondo.exe"),
    # ]:
    #     c.run(f"GOOS={os} GOARCH={arch} go build -o {executable} ./cmd/shell")
    #     c.run(f"zip -r macondo-{tag}-{nickname}.zip ./{executable} ./data")
