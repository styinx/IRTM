import sys
import re


# Normalizes the string by some heuristics
def normalize(term):
    #                      Ä     ä     Ö     ö     Ü     ü     ß     _
    not_allowed_chars = "[^\u00c4\u00e4\u00d6\u00f6\u00dc\u00fc\u00df a-zA-Z]"
    # chars that occur 3 or more times
    spam_chars = r'(.)(\1){2,}'

    normalized = re.sub(not_allowed_chars, "", term).lower()
    normalized = re.sub(spam_chars, r'\1\1', normalized)

    return normalized.replace("ß", "ss").replace("\n", "")


# reads csv file and assigns every game the number of good/bad ratings and comments
def read(file):
    globals = {"entries": 0, "tokens_gut": 0, "tokens_schlecht": 0, "gut": 0, "schlecht": 0}
    tokens = {}

    handle = open(file, encoding="utf-8")
    for line in handle.readlines():
        cols = line.split("\t")

        rating = cols[1]
        text = normalize(cols[2])
        words = text.split(" ")

        words = list(filter(None, words))

        for word in words:
            if word not in tokens:
                tokens[word] = {"gut": 1, "schlecht": 1, "p_gut": 0, "p_schlecht": 0}
            else:
                tokens[word][rating] += 1

        globals["entries"] += 1
        globals["tokens_" + rating] += len(words)
        globals[rating] += 1

    # calculate probabilities for tokens
    for k in tokens:
        token = tokens[k]
        token["p_gut"] = token["gut"] / globals["tokens_gut"] * 100
        token["p_schlecht"] = token["schlecht"] / globals["tokens_schlecht"] * 100

    return tokens, globals


if __name__ == "__main__":
    if len(sys.argv) < 2:
        exit(-1)

    tokens, globals = read(sys.argv[1])
    sorted_tokens = sorted(tokens, key=lambda x: (tokens[x]['p_gut']))

    for k in sorted_tokens:
        e = tokens[k]
        if e["gut"] + e["schlecht"] > 20:
            f = "{:15s} ({:6d})   |   gut ({:6d}) [{:.3f}%]   |   schlecht ({:6d}) [{:.3f}%]"
            print(f.format(k, e["gut"] + e["schlecht"], e["gut"], e["p_gut"], e["schlecht"], e["p_schlecht"]), "\n", sep="")

    print(globals)
