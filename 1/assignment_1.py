import sys
import re
from time import mktime
from _datetime import datetime


class Document:
    # set the document properties
    def __init__(self, time, tweet_id, user_id, user_name):
        self.terms = {}
        self.id = tweet_id
        self.timestamp = mktime(datetime.strptime(time, "%Y-%m-%d %H:%M:%S %z").timetuple())
        self.user_id = user_id
        self.user_name = user_name

    # += operator: adds word to 'terms', discards empty string
    def __iadd__(self, other):
        if other != "":
            if other not in self.terms:
                self.terms[other] = 1
            else:
                self.terms[other] += 1

        return self

    # test print function
    def p(self):
        print(self.id, "(", self.timestamp, ", ", self.user_id, ", ", self.user_name, "): ")
        for term in self.terms:
            print(term, end=" ")
        print("\n")


def normalize(term):
    # discard commands
    term = term.replace("[NEWLINE]", "")

    # discard links
    term = re.sub("http(s)?://[^ ]+", "", term)

    # discard punctuation and special signs
    term = re.sub('[,\?\!"\'…`#@;\[\]\(\)\{\}\/&„“<=>\*\+]+', "", term)

    #
    term = re.sub('(\.\.\.)', " ", term)

    # handle dates and times with special signs
    # replace all . : / where no number is before and after the sign
    term = re.sub('[^0-9]+[\.:\/][^0-9]?', "", term)

    # # remove trailing s
    # if len(term) > 4 and term[-1] == "s":
    #     term = term[:-1]

    return term


def index(name):
    file = open(name, "r")
    for i, line in enumerate(file.readlines()):

        if i > 100:
            break

        args = line.split("\t")
        document = Document(args[0], args[1], args[2], args[3])

        for term in args[4].split(" "):
            document += normalize(term)

        document.p()


if __name__ == "__main__":
    index(sys.argv[1])
