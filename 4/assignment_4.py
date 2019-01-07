import sys


# reads csv file and assigns every game the number of good/bad ratings and comments
def read(file):
    globals = {"count": 0, "gut": 0, "schlecht": 0}
    games = {}

    handle = open(file, encoding="utf-8")
    for line in handle.readlines():
        cols = line.split("\t")

        name = cols[0]
        if name not in games:
            games[name] = {"count": 0, "gut": 0, "schlecht": 0, "comments": []}

        games[name]["count"] += 1
        games[name][cols[1]] += 1
        games[name]["comments"].append(cols[2])

        globals["count"] += 1
        globals[cols[1]] += 1

    # calculates the probability of the game within the class
    for k in games:
        game = games[k]
        game["p_c"] = game["count"] / globals["count"]
        game["p_g"] = game["gut"] / globals["gut"]
        game["p_b"] = game["schlecht"] / globals["schlecht"]

    return games, globals


if __name__ == "__main__":
    if len(sys.argv) < 2:
        exit(-1)

    games, globals = read(sys.argv[1])

    print(globals)

    for k in games:
        e = games[k]
        f = "{:20s}: {:10d} | gut: {:10d} | schlecht: {:10d}\n{:32f} | p_g: {:10f} | p_s: {:16f}\n"
        print(f.format(k, e["count"], e["gut"], e["schlecht"], e["p_g"], e["p_g"], e["p_b"]), "="*80, "\n", sep="")
