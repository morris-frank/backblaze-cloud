from collections import namedtuple

BreadCrumb = namedtuple("BreadCrumb", ["name", "link"])


def make_crumbs(path):
    splitted = path.split("/")
    crumbs = [BreadCrumb("root", "/")]
    for i in range(len(splitted)):
        crumbs.append(BreadCrumb(splitted[i], "/" + "/".join(splitted[: i + 1])))
    return crumbs
