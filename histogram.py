import getopt
from hyphen import Hyphenator
from hyphen import dictools
import sys


def install_language(language):
    if not dictools.is_installed(language):
        dictools.install(language)

def inc(histogram, datum):
    try:
        histogram[datum] += 1

    except KeyError:
        histogram[datum] = 1

def compute_length_histograms(word_gen):
    words = {}
    all_lengths = {}
    unique_lengths = {}

    for word in word_gen:
        length = len(word)
        inc(all_lengths, length)

        if word not in words:
            inc(unique_lengths, length)

        inc(words, word)

    return words, all_lengths, unique_lengths

def by_word(input_file):
    for word in input_file:
        yield word.strip().lower()

def by_syllable(input_file, hyphenator):
    for word in input_file:
        for syllable in hyphenator.syllables(word.strip().lower()):
            yield syllable

if __name__ == "__main__":
    options, args = getopt.getopt(sys.argv[1:], "", ["input=", "lang=", "install", "syllables"])
    options = dict(options)

    input_file = sys.stdin

    if "--input" in options:
        input_file = open(options["--input"])

    words = []

    if "--syllables" in options:
        if "--lang" not in options:
            raise Exception("You must supply --lang option in order to use syllables!")

        if "--install" in options:
            install_language(options["--lang"])

        hyphenator = Hyphenator(options["--lang"])

        words = by_syllable(input_file, hyphenator)

    else:
        words = by_word(input_file)

    all_words, all_lengths, unique_lengths = compute_length_histograms(words)
    print("frequencies:   ", all_words)
    print("lengths:       ", all_lengths)
    print("unique lengths:", unique_lengths)
