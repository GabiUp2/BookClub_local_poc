import subprocess

def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], stderr=subprocess.DEVNULL)\
                     .decode().strip()

def git_commit_and_branch():
    # full and short commit hashes
    full = _git("rev-parse", "HEAD")
    short = _git("rev-parse", "--short", "HEAD")

    # branch or best-effort ref when in detached HEAD
    try:
        ref = _git("symbolic-ref", "--short", "-q", "HEAD")  # e.g., main/feature-x
        if not ref:
            raise RuntimeError
    except Exception:
        # detached: try exact tag, else a descriptive ref, else hash
        try:
            ref = _git("describe", "--tags", "--exact-match")
        except Exception:
            ref = _git("describe", "--tags", "--dirty", "--always")

    return {"commit": full, "short": short, "ref": ref}

if __name__ == "__main__":
    info = git_commit_and_branch()
    print(info)  # {'commit': 'f3c1…', 'short': 'f3c1a2b', 'ref': 'main' or 'v1.2.3' or 'f3c1a2b'}
