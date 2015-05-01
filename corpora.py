import csv
import getopt
import gzip
import iso639
import logging
import multiprocessing as mp
import nltk
import os
import re
import shutil
import sys
import tarfile
import types
import uuid
import urllib.request

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


class Corpora(dict):
    def __getitem__(self, key):
        try:
            return super(Corpora, self).__getitem__(key)
        except KeyError:
            f = "Tried '{}'. Only following corpora are supported: {}"
            raise Exception(f.format(key, ", ".join(["'{}'".format(k) for k in self.keys()])))


class LangFiles(dict):
    def __init__(self, output_dir):
        self.output_dir = output_dir

    def __getitem__(self, lang):
        try:
            return super(LangFiles, self).__getitem__(lang)
        except KeyError:
            f = open(os.path.join(self.output_dir, get_langcode(lang)), 'w+')
            self[lang] = f
            return f

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        for file in self.values():
            file.close()


class Extract:
    def __random_path(self, root):
        return os.path.join(root, "."+uuid.uuid4().hex)

    def __walk(self, root):
        for name in os.listdir(root):
            abs_path = os.path.join(root, name)
            if (os.path.isdir(abs_path)):
                self.__walk(abs_path)
            elif (tarfile.is_tarfile(abs_path)):
                tar = tarfile.open(abs_path)
                path = self.__random_path(abs_path)
                tar.extractall(path)
                tar.close()
                self.__walk(path)
            elif (re.match(self.name_filter, abs_path)):
                yield abs_path

    def __init__(self, file, name_filter):
        self.file = file
        self.tmp = self.__random_path(cache_dir)
        self.name_filter = name_filter

    def __enter__(self):
        tar = tarfile.open(self.file)
        tar.extractall(self.tmp)
        tar.close()
        return self.__walk(self.tmp)

    def __exit__(self, type, value, traceback):
        shutil.rmtree(self.tmp, ignore_errors=True)


def get_langcode(lang):
    lang_name = lang.part3
    if not lang_name:
        logging.debug("iso639-3 for lang '{}' not found.".format(lang.name))
        lang_name = lang.part2b
        if not lang_name:
            raise Exception("iso639-2b for lang '{}' not found.".format(lang.name))
    return lang_name


def get_lang(lang_code):
    try:
        lang = iso639.languages.part3[lang_code]
    except KeyError:
        try:
            logging.debug("Reconstructing lang from iso639-3 '{}' failed.".format(lang_code))
            lang = iso639.languages.retired[lang_code]
        except KeyError:
            logging.debug("Reconstructing lang from iso639-3 retired '{}' failed.".format(lang_code))
            try:
                lang = iso639.languages.part2b[lang_code]
            except KeyError:
                raise Exception("Reconstructing lang from iso639-2b '{}' failed.".format(lang_code))
    return lang


def download(url, target):
    urllib.request.urlretrieve(url, target)
    return target


def preprocess(source, name_filter, lang_files, handler):
    with Extract(source, name_filter) as files:
        for f in files:
            handler(f, lang_files)


def init(download_url, target_name, preprocess_handler, name_filter='.+'):
    obj = types.SimpleNamespace()
    obj.url = download_url
    obj.cache = os.path.join(cache_dir, target_name)
    obj.download = lambda: download(url=obj.url, target=obj.cache)
    obj.preprocess = lambda lang_files: preprocess(
        source=obj.cache,
        name_filter=name_filter,
        lang_files=lang_files,
        handler=preprocess_handler
    )
    return obj


def run_download(source):
    handler = supported_corpora[source]
    logging.info("Downloading data for '{}'...".format(source))
    handler.download()
    logging.info("Data for '{}' downloaded.".format(source))


def run_preprocess(source):
    handler = supported_corpora[source]
    if (os.path.isfile(handler.cache)):
        logging.info("Found cached data for '{}'.".format(source))
    else:
        run_download(source)
    logging.info("Preprocessing data for '{}'...".format(source))
    output_dir = os.path.join(corpora_dir, source)
    os.makedirs(output_dir, exist_ok=True)
    with LangFiles(output_dir) as lang_files:
        handler.preprocess(lang_files)
    logging.info("Data for '{}' preprocessed.".format(source))


def get_supported_corpora():
    return supported_corpora.keys()


def read_corpora(source):
    if source not in os.listdir(corpora_dir):
        run_preprocess(source)
    path = os.path.join(corpora_dir, source)
    result = []
    for lang_code in os.listdir(path):
        obj = types.SimpleNamespace()
        obj.lang = get_lang(lang_code)
        obj.words = (word for word in open(os.path.join(path, lang_code), 'r'))
        result.append(obj)
    return result


# corpora specific code

def preprocess_bible(gzxmlfile, lang_files):
    with gzip.open(gzxmlfile) as xmlfile:
        tree = ET.fromstring(xmlfile.read())
        lang = get_lang(tree.find('./cesHeader/profileDesc/langUsage/language').get('iso639'))
        filehandle = lang_files[lang]
        for verse in tree.findall('./text//seg[@type="verse"]'):
            text = verse.text
            if text is not None:
                for word in tokenizer.tokenize(text):
                    print(word, file=filehandle)


def preprocess_tatoeba(f, lang_files):
    with open(f, 'r') as csvfile:
        lines = csv.reader(csvfile, delimiter='\t')
        for line in lines:
            try:
                lang = get_lang(line[1])
                filehandle = lang_files[lang]
                for word in tokenizer.tokenize(line[2]):
                    print(word, file=filehandle)
            except Exception as err:
                logging.debug("{}. Dropping sentence.".format(err))


# init module
global cache_dir
cache_dir = os.path.abspath(os.path.join(__file__, os.path.join(os.pardir, ".cache")))
os.makedirs(cache_dir, exist_ok=True)

global corpora_dir
corpora_dir = os.path.abspath(os.path.join(__file__, os.path.join(os.pardir, "corpora")))
os.makedirs(corpora_dir, exist_ok=True)

global supported_corpora
supported_corpora = Corpora([
    ("bible", init(
        download_url="http://homepages.inf.ed.ac.uk/s0787820/bible/XML_Bibles.tar.gz",
        target_name="bibles.tar.gz",
        preprocess_handler=preprocess_bible,
        name_filter='^.+\.xml.gz$'
    )),
    ("tatoeba", init(
        download_url="http://downloads.tatoeba.org/exports/sentences.tar.bz2",
        target_name="tatoeba.tar.bz2",
        preprocess_handler=preprocess_tatoeba,
        name_filter='^.+\.csv$'
    ))
])


if __name__ == "__main__":
    options, args = getopt.getopt(sys.argv[1:], "", ["download=", "preprocess=", "debug"])
    options = dict(options)

    datefmt = "%Y-%m-%d %H:%M:%S"
    fmt = "%(asctime)s %(levelname)s in %(processName)s: %(message)s"
    if "--debug" in options:
        logging.basicConfig(format=fmt, datefmt=datefmt, level=logging.DEBUG)
    else:
        logging.basicConfig(format=fmt, datefmt=datefmt, level=logging.INFO)

    processes = []

    if "--download" in options:
        source = options["--download"]
        if source == "all":
            for key in supported_corpora.keys():
                p = mp.Process(target=run_download, args=(key,), name="Process-"+key)
                processes.append(p)
                p.start()
        else:
            run_download(source)

    if "--preprocess" in options:
        # nltk.download('punkt')
        tokenizer = nltk.tokenize.RegexpTokenizer('\w+')
        source = options["--preprocess"]
        if source == "all":
            for key in supported_corpora.keys():
                p = mp.Process(target=run_preprocess, args=(key,), name="Process-"+key)
                processes.append(p)
                p.start()
        else:
            run_preprocess(source)

    for p in processes:
        p.join()
