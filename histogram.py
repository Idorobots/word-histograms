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
        yield obj.lang, histograms(obj.words)

def histograms(word_gen):
    one_gram_lengths = {}

    two_gram_lengths = {}
    last_length = 0

    three_gram_lengths = {}
    last_last_length = 0

    unique_lengths = {}
    words = {}

    for word in word_gen:
        length = len(word)

        # Mundane 1-gram lengths
        inc(one_gram_lengths, length)

        # 2-gram lengths
        if last_length != 0:
            inc(two_gram_lengths, (last_length, length))

        # 3-gram lengths
        if last_last_length != 0:
            inc(three_gram_lengths, (last_last_length, last_length, length))

        last_last_length = last_length
        last_length = length

        # Unique lengths
        if word not in words:
            words[word] = True
            inc(unique_lengths, length)

    return {"1-gram lengths" : key_transform(normalize(one_gram_lengths), str),
            "2-gram lengths" : key_transform(normalize(two_gram_lengths), str),
            "3-gram lengths" : key_transform(normalize(three_gram_lengths), str),
            "unique lengths" : key_transform(normalize(unique_lengths), str)}

def key_transform(d, f):
    return {f(k): d[k] for k in d}

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

    for lang, result in all_histograms(read_files(args, word_gen)):
        if "--output-dir" in options:
            output_file = os.path.join(options["--output-dir"], get_langcode(lang) + ".json")
            logging.info("Saving file {}.".format(output_file))

            with open(output_file, "w") as out:
                out.write(json.dumps(result))

        else:
            print(input_file + ":")
            for k in sorted(result):
                print(k + ":", result[k])
