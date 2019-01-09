import sys
import re


# Normalizes the string by some heuristics
def normalize(term):
    #                      Ae    ae    Oe    oe    Ue    ue    ss    _
    not_allowed_chars = "[^\u00c4\u00e4\u00d6\u00f6\u00dc\u00fc\u00df a-zA-Z]"
    # chars that occur 3 or more times
    spam_chars = r'(.)(\1){2,}'
    stop_words = ["der", "die", "das", "es", "ist"]

    normalized = re.sub(not_allowed_chars, "", term).lower()
    normalized = re.sub(spam_chars, r'\1\1', normalized)

    for w in stop_words:
        normalized = normalized.replace(w, "")

    return normalized.replace("\u00df", "ss").replace("\n", "")


# reads train-csv file and classifies every token
def classifier(file):
    globals = {"tokens_gut": 0, "tokens_schlecht": 0,
               "gut":        0, "schlecht": 0,
               "p_gut":      0, "p_schlecht": 0}
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
                tokens[word] = {"gut":   1, "schlecht": 1,
                                "p_gut": 0, "p_schlecht": 0}
            else:
                tokens[word][rating] += 1

        globals["tokens_" + rating] += len(words)
        globals[rating] += 1

    # calculate probabilities for tokens with add-one-smoothing
    vocabulary = len(tokens)
    for k in tokens:
        token = tokens[k]
        token["p_gut"] = (token["gut"] + 1) / \
                         (globals["tokens_gut"] + vocabulary) * 100
        token["p_schlecht"] = (token["schlecht"] + 1) / \
                              (globals["tokens_schlecht"] + vocabulary) * 100

    # calculate probabilities for classes
    c_entries = globals["tokens_gut"] + globals["tokens_schlecht"]
    globals["p_gut"] = globals["tokens_gut"] / c_entries * 100
    globals["p_schlecht"] = globals["tokens_schlecht"] / c_entries * 100

    return tokens, globals


# read test-csv file and calculate class prediction
def evaluate(file, tokens, globals):
    evaluation = {"TP": 0, "FP": 0, "FN": 0, "TN": 0}

    handle = open(file, encoding="utf-8")
    for line in handle.readlines():
        cols = line.split("\t")

        rating = cols[1]
        text = normalize(cols[2])
        words = text.split(" ")

        words = list(filter(None, words))

        if words:

            p_c_gut = globals["p_gut"]
            p_c_schlecht = globals["p_schlecht"]

            for token in words:
                if token in tokens:
                    p_c_gut *= (tokens[token]["p_gut"])
                    p_c_schlecht *= (tokens[token]["p_schlecht"])

            gut = p_c_gut > p_c_schlecht

            if gut and rating == "gut":
                evaluation["TP"] += 1
            elif not gut and rating == "gut":
                evaluation["FN"] += 1
            elif gut and rating == "schlecht":
                evaluation["FP"] += 1
            elif not gut and rating == "schlecht":
                evaluation["TN"] += 1

    return evaluation


if __name__ == "__main__":
    if len(sys.argv) < 3:
        exit(-1)

    tokens, globals = classifier(sys.argv[1])

    # print all tokens that occur more than 20 times in all documents
    # sorted_tokens = sorted(tokens, key=lambda x: (tokens[x]['p_gut']))
    # for k in sorted_tokens:
    #     e = tokens[k]
    #     if e["gut"] + e["schlecht"] > 20:
    #         f = "{:11s} ({:5d}) | gut ({:5d}) [{:.32}%] | schlecht ({:4d}) [{:.2f}%]"
    #         print(f.format(k, e["gut"] + e["schlecht"], e["gut"], e["p_gut"],
    #                        e["schlecht"], e["p_schlecht"]), sep="")

    evaluation = evaluate(sys.argv[2], tokens, globals)
    tp = evaluation["TP"]
    fp = evaluation["FP"]
    fn = evaluation["FN"]
    tn = evaluation["TN"]

    p = tp / (tp + fp)
    r = tp / (tp + fn)
    f = 2*p*r / (p + r)

    t = "\nPrecision: {}\nRecall: {}\nF: {}\n\nTP({:5d}) | FP({:5d})\n" + '-'*21 + "\nFN({:5d}) | TN({:5d})\n"
    print(t.format(p, r, f, tp, fp, fn, tn))
