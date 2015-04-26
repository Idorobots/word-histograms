import babelfish
import csv
import getopt
import logging
import nltk
import os
import shutil
import sys
import tarfile
import types
import urllib.request


class Corpora(dict):
    def __getitem__(self, key):
        try:
            return super(Corpora, self).__getitem__(key)
        except KeyError:
            f = "Tried '{}'. Only following corpora are supported: {}"
            raise Exception(f.format(key, ", ".join(["'{}'".format(k) for k in self.keys()])))


class LangFiles(dict):
    def __getitem__(self, lang):
        try:
            return super(LangFiles, self).__getitem__(lang)
        except KeyError:
            file = open(os.path.join(data_dir, lang.alpha3), 'a+')
            self[lang] = file
            return file

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        for file in self.values():
            file.close()


def download(url, target_dir, output_name):
    os.makedirs(target_dir, exist_ok=True)
    filehandle = os.path.join(target_dir, output_name)
    urllib.request.urlretrieve(url, filehandle)
    return filehandle


def extract(filehandle, target_dir, clean=True):
    tar = tarfile.open(filehandle)
    tar.extractall(path=target_dir)
    tar.close()
    if clean:
        os.remove(filehandle)


def init(download_handler, preprocess_handler):
    obj = types.SimpleNamespace()
    obj.download = download_handler
    obj.preprocess = preprocess_handler
    return obj


def run(source, download_only=False, overwrite=False):
    handler = supported_corpora[source]
    source_dir = os.path.join(corpora_dir, source)
    logging.info("Downloading data for {}...".format(source))
    handler.download(source_dir, overwrite)
    if not download_only:
        logging.info("Preprocessing data for {}...".format(source))
        handler.preprocess()


# corpora specific code

def download_tatoeba(target_dir, overwrite=False):
    if (not os.path.exists(os.path.join(target_dir, "sentences.csv"))) or overwrite:
        filehandle = download(url="http://downloads.tatoeba.org/exports/sentences.tar.bz2",
                              target_dir=target_dir,
                              output_name="sentences.tar.bz2")
        extract(filehandle=filehandle, target_dir=target_dir)


def preprocess_tatoeba():
    tatoeba_path = os.path.join(corpora_dir, "tatoeba/sentences.csv")
    tatoeba_file = open(tatoeba_path)

    with open(tatoeba_path) as tatoeba_file, LangFiles() as files:
        sentences = csv.reader(tatoeba_file, delimiter='\t')
        for sentence in sentences:
            try:
                lang = babelfish.Language(sentence[1])
                filehandle = files[lang]
                words = tokenizer.tokenize(sentence[2])
                for word in words:
                    print(word, file=filehandle)
            except ValueError as err:
                logging.debug("{}. Dropping sentence...".format(err))


if __name__ == "__main__":
    options, args = getopt.getopt(sys.argv[1:], "", ["download=", "preprocess=", "debug"])
    options = dict(options)

    corpora_dir = os.path.abspath(os.path.join(__file__, os.path.join(os.pardir, "corpora")))
    data_dir = os.path.join(corpora_dir, "data")
    supported_corpora = Corpora(
        [("tatoeba", init(download_tatoeba, preprocess_tatoeba))]
    )

    logging_format = "%(levelname)s: %(message)s"
    if "--debug" in options:
        logging.basicConfig(format=logging_format, level=logging.DEBUG)
    else:
        logging.basicConfig(format=logging_format, level=logging.INFO)

    if "--download" in options:
        source = options["--download"]
        if source == "all":
            for key, handler in supported_corpora.items():
                run(key, download_only=True, overwrite=True)
        else:
            run(source, download_only=True, overwrite=True)

    if "--preprocess" in options:
        shutil.rmtree(data_dir, ignore_errors=True)
        # nltk.download('punkt')
        tokenizer = nltk.tokenize.WordPunctTokenizer()
        os.makedirs(data_dir, exist_ok=True)
        source = options["--preprocess"]
        if source == "all":
            for key in supported_corpora.keys():
                run(key, download_only=False, overwrite=False)
        else:
            run(source, download_only=False, overwrite=False)
