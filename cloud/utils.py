from collections import namedtuple

BreadCrumb = namedtuple("BreadCrumb", ["name", "link"])


def make_crumbs(path):
    splitted = path.split("/")
    crumbs = [BreadCrumb("root", "/")]
    for i in range(len(splitted)):
        crumbs.append(BreadCrumb(splitted[i], "/" + "/".join(splitted[: i + 1])))
    return crumbs


def humanize_bytes(size: int) -> str:
    if size < 0.5e6:
        return f"{size/1e3:.1f}Kb"
    elif size < 0.5e9:
        return f"{size/1e6:.1f}Mb"
    else:
        return f"{size/1e9:.1f}Gb"

