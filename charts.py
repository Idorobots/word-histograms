import getopt
import json
import sys
import os.path
import numpy as np
import matplotlib.pyplot as plt

if __name__ == '__main__':
    options, args = getopt.getopt(sys.argv[1:], '', ['input='])
    options = dict(options)

    input_file = sys.stdin
    title = 'STDIN'
    if '--input' in options:
        input_file = open(options['--input'])
        title = options['--input']

    scores = json.load(input_file)

    langs = sorted(scores, key = lambda k: scores[k]['score'])
    langs_abbr = [os.path.splitext(os.path.basename(lang))[0] for lang in langs]
    ys = [scores[lang]['score'] for lang in langs]
    xs = np.arange(len(langs))

    fig, ax = plt.subplots()

    bar1 = ax.bar(xs, ys, 0.8, alpha = 0.4, color = 'b', label = 'Similarity')
    ax.set_xlabel('Language')
    ax.set_ylabel('Score')
    ax.set_title(title)
    ax.set_xticks(xs + 0.8)
    ax.set_xticklabels(langs_abbr, rotation = 90)

    plt.tight_layout()
    plt.show()
