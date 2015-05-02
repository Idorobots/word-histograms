import getopt
import histogram
import math
import simplejson as json
import sys


def key_transform(d):
    return {int(k): d[k] for k in d}

def load_language_file(filename):
    data = json.loads(open(filename).read())
    return key_transform(data["lengths"]), key_transform(data["unique_lengths"])

def value_or_0(d, key):
    try:
        return d[key]

    except KeyError:
        return 0

def similarity(a, b):
    union = a.copy()
    union.update(b)

    coefficient = 0

    # Actually computes the difference
    for key in union.keys():
        coefficient += (value_or_0(a, key) - value_or_0(b, key))**2

    return math.sqrt(coefficient)

if __name__ == "__main__":
    options, args = getopt.getopt(sys.argv[1:], "", ["input=", "unique-weight=", "full-weight="])
    options = dict(options)

    if len(args) == 0:
        raise Exception("At least one language file is required!")

    input_file = sys.stdin

    if "--input" in options:
        input_file = open(options["--input"])

    # Weights
    full_weight = 1.0
    if "--full-weight" in options:
        full_weight = float(options["--full-weight"])

    unique_weight = 0.25
    if "--unique-weight" in options:
        unique_weight = float(options["--unique-weight"])

    _, all_text, unique_text = histogram.histograms(histogram.by_word(input_file))

    scores = {}

    for lang in args:
        all_lang, unique_lang = load_language_file(lang)
        score_all = similarity(all_text, all_lang)
        score_unique = similarity(unique_text, unique_lang)
        score = score_all * full_weight + score_unique * unique_weight
        scores[lang] = (score, score_all, score_unique)

    f = "{:<30}{:<30}{:<30}{:<30}"
    print(f.format("language",
                   "full similarity * " + str(full_weight),
                   "unique similarity * " + str(unique_weight),
                   "score"))

    for lang in sorted(scores, key = lambda k: scores[k][0]):
        score, score_all, score_unique = scores[lang]
        print(f.format(lang, score_all, score_unique, score))
