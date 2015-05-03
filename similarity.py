import getopt
import histogram
import json
import math
import sys


def match(cypher_histogram, lang_histograms, weights):
    scores = {}
    for lang, histo in lang_histograms:
        score = {}
        total_score = 0

        for metric in histo:
            s = similarity(cypher_histogram[metric], histo[metric])
            score[metric] = s
            total_score += s * value_or_0(weights, metric)

        score["score"] = total_score
        scores[lang] = score
    return scores

def similarity(a, b):
    union = a.copy()
    union.update(b)

    coefficient = 0

    # Actually computes the difference
    for key in union.keys():
        coefficient += (value_or_0(a, key) - value_or_0(b, key))**2

    return math.sqrt(coefficient)

def value_or_0(d, key):
    try:
        return d[key]

    except KeyError:
        return 0

def load_language_file(filename):
    with open(filename) as data:
         return filename, json.loads(data.read())

if __name__ == "__main__":
    options, args = getopt.getopt(sys.argv[1:], "", ["input=", "output=", "weights="])
    options = dict(options)

    if len(args) == 0:
        raise Exception("At least one language file is required!")

    input_file = sys.stdin

    if "--input" in options:
        input_file = open(options["--input"])

    weights = {"1-gram lengths" : 1,
               "2-gram lengths" : 0.5,
               "3-gram lengths" : 0.25,
               "unique lengths" : 0.1}

    if "--weights" in options:
        weights = json.loads(options["--weights"])

    histo = histogram.histograms(histogram.by_word(input_file))
    scores = match(histo, [load_language_file(lang) for lang in args], weights)

    if "--output" in options:
        with open(options["--output"], "w") as out:
            out.write(json.dumps(scores))

    else:
        f = "{:<29}" + "{:<20} " * (len(histo) + 1)
        columns = sorted(histo.keys())

        print(f.format("language", "score", *columns))

        for lang in sorted(scores, key = lambda k: scores[k]["score"]):
            s = [scores[lang][column] for column in columns]
            print(f.format(lang, scores[lang]["score"], *s))
