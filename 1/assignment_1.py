import sys
import re
from time import time
import pickle
import bisect

READ_MAX_LINES = -1
EYE_CANCER = True


#
# Formats a timestamp
#
def duration(diff):
    millis = diff * 1000
    hours = int(millis / (1000 * 60 * 60)) % 24
    minutes = int(millis / (1000 * 60)) % 60
    seconds = int(millis / 1000) % 60
    nanos = int(millis * 1000) % 1000
    millis = int(millis) % 1000

    res = ""
    if hours > 0:
        res += str(hours) + "h "
    if minutes > 0:
        res += str(minutes) + "m "
    if seconds > 0:
        res += str(seconds) + "s "
    if millis > 0:
        res += str(millis) + "ms "
    if nanos > 0:
        res += str(nanos) + "ns "

    return res


#
# Normalizes the string by some heuristics
#
def normalize(term):
    # discard commands
    normalized = term.replace("[NEWLINE]", "")

    # discard links
    normalized = re.sub("http(s)?://[^ ]+", "", normalized)

    # discard punctuation and special signs
    normalized = re.sub('[,\?\!"\'…`#@;\[\]\(\)\{\}\/&„“<=>\*\+\n]+', "", normalized)

    # replace concatenated symbols with characters by a space
    normalized = re.sub('(\.\.\.)', " ", normalized)

    # handle dates and times with special signs
    # replace all . : / where no number is before and after the sign
    normalized = re.sub('[^0-9]+[\.:\/][^0-9]?', "", normalized)

    # # remove trailing s
    # if len(term) > 4 and term[-1] == "s":
    #     term = term[:-1]

    return normalized.lower()


#
# Caches the current result
#
class Cache:
    def __init__(self):
        self.read_lines = 0
        self.dict = None
        self.docs = {}

    @staticmethod
    def save(what, name="tweets.cached"):
        pickle.dump(what, open(name, "wb"))

    @staticmethod
    def load(name="tweets.cached"):
        return pickle.load(open(name, "rb"))


#
# Represents a document. Saves timestamp, user id and user name.
#
class Document:
    # set the document properties
    def __init__(self, timestamp, user_id, user_name, text):
        self.timestamp = timestamp
        self.user_id = user_id
        self.user_name = user_name
        self.text = text

    # Prints the document and highlights given search terms if an argument is given
    def p(self, needles=""):
        formatted = self.text

        if needles != "":

            form = "\033[1;5;31m"
            if not EYE_CANCER:
                form = "\033[1;31m"

            for needle in needles:
                formatted = re.sub("(" + needle + ")", form + r'\1' + "\033[0m", formatted, flags=re.IGNORECASE)

        print("\t\033[1;32m", self.timestamp, ": ", self.user_id, " (", self.user_name, ")\033[0m")
        print("\t", formatted, end="\n\n")


class PostingsList:
    def __init__(self, doc_id):
        self.documents = {doc_id: 1}

    # add document to postings list, stores also the occurrences of the term in the document
    def add(self, doc_id):
        if doc_id not in self.documents:
            self.documents[doc_id] = 1
        else:
            self.documents[doc_id] += 1

    # prints the term and the postings list
    def p(self):
        for d in self.documents:
            print(doc, " [", self.documents[d], "] -> ", end="")


class Dictionary:
    def __init__(self):
        self.terms = {}

    def postingsList(self, term):
        try:
            return self.terms[term].documents
        except KeyError:
            return {}

    # add a new term to the dictionary, or add a document to the postings list
    def add(self, term, doc_id):
        if term != "":
            if term not in self.terms:
                self.terms[term] = PostingsList(doc_id)
            else:
                self.terms[term].add(doc_id)

        return self

    def p(self):
        for term in self.terms:
            print(term, " : ", end="")
            self.terms[term].p()
            print("\n")


#
# Performs a query on the dictionary and returns the documents where matches were found.
#
def query(*args):
    print("process query: \033[1m", " AND ".join(args), "\033[0m")

    # one term -> return the postings list
    if len(args) == 1:
        return dictionary.postingsList(args[0])

    # two terms -> search for intersections
    elif len(args) == 2:
        intersection = []
        it1 = iter(dictionary.postingsList(args[0]))
        it2 = iter(dictionary.postingsList(args[1]))

        try:
            v1, v2 = next(it1), next(it2)
        except StopIteration:
            return []

        while it1 and it2:
            try:
                if v1 == v2:
                    intersection.append(v1)
                    v1 = next(it1)
                    v2 = next(it2)
                elif v1 < v2:
                    v1 = next(it1)
                else:
                    v2 = next(it2)
            except StopIteration:
                # one postings list iterator is at the end
                break

    # more than two -> magic
    else:
        for arg in args:
            pass

    return intersection


#
# Reads a document and separates it by documents
#
def index(name):
    file = open(name, "r")
    docs = 0
    for line in file.readlines():

        if READ_MAX_LINES != -1 and docs == READ_MAX_LINES:
            break

        args = line.split("\t")

        # read all terms in document and store them normalized in the dictionary
        for term in args[4].split(" "):
            dictionary.add(normalize(term), args[1])

        documents[args[1]] = Document(args[0], args[2], args[3], args[4])
        docs += 1

    return docs


if __name__ == "__main__":
    cache = None
    dictionary = Dictionary()
    documents = {}
    search = ["nacht", "schlafen"]

    # read search term from console
    if len(sys.argv) > 2:
        search = [x.lower() for x in sys.argv[2].split(",")]

    # read only until specific line (reduces computing time)
    if len(sys.argv) > 3:
        READ_MAX_LINES = int(sys.argv[3])

    # remove eye cancer
    if len(sys.argv) > 4:
        EYE_CANCER = False

    # load cached file or process new file
    if sys.argv[1].split(".")[-1] == "cached":
        cache = Cache.load(sys.argv[1])
        dictionary = cache.dict
        documents = cache.docs
    else:
        t = time()
        print("process file: ", sys.argv[1])
        print(index(sys.argv[1]), " documents searched")
        print("processing took ", duration(time() - t), end="\n\n")

    # gets length for each postings list, print top 10 matches
    # uncomment from here to print the top results:
    #
    # lengths = {}
    # for t in dictionary.terms:
    #     lengths[t] = len(dictionary.terms[t].documents)
    #
    # s = [(k, lengths[k]) for k in sorted(lengths, key=lengths.get, reverse=True)]
    # i = 0
    # for v, k in s:
    #     if i == 10:
    #         break
    #     print(k, ": ", v)
    #     i += 1

    # process a query
    t = time()
    matching_docs = query(*search)
    print("result: ", matching_docs)
    for doc in matching_docs:
        documents[doc].p(search)
    print("query took ", duration(time() - t), end="\n\n")

    # cache processed values
    if cache is None:
        cache = Cache()
        cache.dict = dictionary
        cache.docs = documents
        Cache.save(cache)
