# Code Portfolio

Course and lab work by [Nate Dorleus](https://github.com/Nerddbucket).

## Projects

| Folder | What’s in it |
| --- | --- |
| [Java Code](./Java%20Code%20) | Java labs: to-do list, calculators, homework assignments |
| [Python](./Python%20) | Python labs: input/output, loops, homework assignments |

Related Docker / Linux lab (separate repo):

- [linuxhq-docker-desktop](https://github.com/Nerddbucket/linuxhq-docker-desktop) — Ubuntu desktop in Docker, used as a local Linux lab

## Setup

One command prepares every project in this repo. It checks Java and Python, and it installs the job applier's browser tools.

```bash
bash scripts/setup.sh
```

Run it again any time. It is safe to repeat.

## Run a project

Java labs live in `Java Code `. From that folder:

```bash
javac To_Do_List.java
printf '1\nBuy milk\n5\n' | java To_Do_List
```

Python labs live in `Python `. From that folder:

```bash
printf '90\n80\n70\n60\n95\n88\n' | python3 P2HW2_dorleus_nathan.py
```

The job applier lives in `job-applier`. See [job-applier/README.md](job-applier/README.md). From that folder, after copying `config.example.json` to `config.json`:

```bash
python3 -m applier
```

Open http://127.0.0.1:8765. Practice run stays on this computer. Start sends applications only after `submit` is true in the config.

## Notes

This repository is coursework and practice code. It is not a production app. No secrets, API keys, or credentials belong in this repo.
