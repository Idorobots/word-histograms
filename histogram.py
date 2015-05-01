import getopt
from hyphen import Hyphenator
from hyphen import dictools
import json
import logging
import os.path
import sys


def histograms(word_gen):
    words = {}
    all_lengths = {}
    unique_lengths = {}

    for word in word_gen:
        length = len(word)
        inc(all_lengths, length)

        if word not in words:
            inc(unique_lengths, length)

        inc(words, word)

    return words, normalize(all_lengths), normalize(unique_lengths)

def inc(histogram, datum):
    try:
        histogram[datum] += 1

    except KeyError:
        histogram[datum] = 1

def normalize(d):
    frequency_sum = 0
    for k in d:
        frequency_sum += d[k]

    return {k: d[k]/frequency_sum for k in d}

def by_word(input_file):
    for word in open(input_file):
        yield word.strip().lower()

def by_syllable(input_file, install_lang_p):
    lang = os.path.basename(input_file)

    if install_lang_p and not dictools.is_installed(language):
        dictools.install(lang)

    hyphenator = Hyphenator(lang)

    for word in open(input_file):
        word = word.strip().lower()
        syllables = hyphenator.syllables(word)
        logging.debug("{} syllables: {}".format(word, syllables))
        for syllable in syllables:
            yield syllable

if __name__ == "__main__":
    options, args = getopt.getopt(sys.argv[1:], "", ["output-suffix=",
                                                     "install", "syllables",
                                                     "list",
                                                     "debug"])
    options = dict(options)

    words_gen = by_word

    logging_format = "%(levelname)s: %(message)s"
    if "--debug" in options:
        logging.basicConfig(format=logging_format, level=logging.DEBUG)
    else:
        logging.basicConfig(format=logging_format, level=logging.INFO)

    if "--syllables" in options:
        words_gen = lambda input_file: by_syllable(input_file, "--install" in options)

    for input_file in args:
        all_words, all_lengths, unique_lengths = histograms(words_gen(input_file))

        result = {"lengths" : all_lengths,
                  "unique_lengths" : unique_lengths}

        if "--list" in options:
            result["words"] = all_words

        if "--output-suffix" in options:
            output_file = input_file + options["--output-suffix"]
            logging.info("Saving file {}.".format(output_file))

            with open(output_file, "w") as out:
                out.write(json.dumps(result))

        else:
            print(input_file + ":")
            for k in sorted(result):
                print(k + ":", result[k])
