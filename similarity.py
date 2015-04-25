import getopt
import histogram
import math
import simplejson as json
import sys

def key_transform(d):
    return {int(k): d[k] for k in d}

def load_language_file(filename):
    data = json.loads(open(filename).read())
    return data["all_words"], key_transform(data["all_lengths"]), key_transform(data["unique_lengths"])

def value_or_0(d, key):
    try:
        return d[key]

    except KeyError:
        return 0

def normalize(d):
    frequency_sum = 0
    for k in d:
        frequency_sum += d[k]

    return {k: d[k]/frequency_sum for k in d}

def compute_similarity(a, b):
    a = normalize(a)
    b = normalize(b)

    union = a.copy()
    union.update(b)

    coefficient = 0

    # Actually computes the difference
    for key in union.keys():
        coefficient += (value_or_0(a, key) - value_or_0(b, key))**2

    return math.sqrt(coefficient)

if __name__ == "__main__":
    options, args = getopt.getopt(sys.argv[1:], "", ["input="])
    options = dict(options)

    if len(args) == 0:
        raise Exception("At least language file is required!")

    input_file = sys.stdin

    if "--input" in options:
        input_file = open(options["--input"])

    _, all_text, unique_text = histogram.compute_length_histograms(histogram.by_word(input_file))

    f = "{:>30}{:>30}{:>30}"
    print(f.format("language", "full similarity", "unique similarity"))
    for lang in args:
        _, all_lang, unique_lang = load_language_file(lang)
        print(f.format(lang,
                       compute_similarity(all_text, all_lang),
                       compute_similarity(unique_text, unique_lang)))
