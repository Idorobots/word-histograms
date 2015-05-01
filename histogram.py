from corpora import get_lang, get_langcode
import getopt
from hyphen import Hyphenator
from hyphen import dictools
import json
import logging
import os
import os.path
import sys
import types

def all_histograms(word_gens):
    for obj in word_gens:
        result = histograms(obj.words)
        yield pack(obj.lang, *result)

def pack(*args):
    return args

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

def by_word(input_gen):
    for word in input_gen:
        w = word.strip().lower()
        logging.debug("word: {}".format(w))
        yield w

def by_syllable(input_gen, lang, install_lang_p):
    if install_lang_p and not dictools.is_installed(lang):
        dictools.install(lang)

    hyphenator = Hyphenator(lang)

    for word in input_gen:
        syllables = hyphenator.syllables(word)
        logging.debug("syllables: {}".format(syllables))
        for syllable in syllables:
            yield syllable

def read_files(files, word_gen):
    for f in files:
        obj = types.SimpleNamespace()
        obj.lang = get_lang(os.path.basename(f))
        obj.words = word_gen(open(f))
        yield obj

if __name__ == "__main__":
    options, args = getopt.getopt(sys.argv[1:], "", ["output-dir=",
                                                     "install", "syllables",
                                                     "list",
                                                     "debug"])
    options = dict(options)

    word_gen = by_word

    logging_format = "%(levelname)s: %(message)s"
    if "--debug" in options:
        logging.basicConfig(format=logging_format, level=logging.DEBUG)
    else:
        logging.basicConfig(format=logging_format, level=logging.INFO)

    if "--syllables" in options:
        word_gen = lambda input_file: by_syllable(by_word(input_file),
                                                  os.path.basename(input_file), # FIXME Hax :(
                                                  "--install" in options)

    if "--output-dir" in options and not os.path.isdir(options["--output-dir"]):
        os.makedirs(options["--output-dir"])

    for lang, all_words, all_lengths, unique_lengths in all_histograms(read_files(args, word_gen)):
        result = {"lengths" : all_lengths,
                  "unique_lengths" : unique_lengths}

        if "--list" in options:
            result["words"] = all_words

        if "--output-dir" in options:
            output_file = os.path.join(options["--output-dir"], get_langcode(lang) + ".json")
            logging.info("Saving file {}.".format(output_file))

            with open(output_file, "w") as out:
                out.write(json.dumps(result))

        else:
            print(input_file + ":")
            for k in sorted(result):
                print(k + ":", result[k])
