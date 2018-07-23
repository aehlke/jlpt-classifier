#!/usr/bin/env python
import json
import os
import zipfile

# https://stackoverflow.com/a/48374671/89373
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plot
import requests


JMDICT_JSON_URL = 'https://github.com/scriptin/jmdict-simplified/releases/download/2.0.0/jmdict_eng.json.zip'
JLPT_COLORS = {
    1: '#d84c43',
    2: '#f6934b',
    3: '#dd9f40',
    4: '#48a17a',
    5: '#5890c5',
}


def _make_build_dir():
    if not os.path.exists('build'):
        os.makedirs('build')


def _get_cb4960_word_frequencies():
    '''
    Maps word to frequency_ordinal in corpus.
    '''
    frequencies = {}
    with open('cb4960_novel_word_freq.txt', 'r', encoding="utf-8") as f:
        for line_number, line in enumerate(f):
            frequency, word, *rest = line.split('\t')
            frequencies[word] = line_number
    return frequencies


def _get_wikipedia_word_frequencies():
    '''
    Maps word to frequency rank in corpus.
    '''
    frequencies = {}
    with open('japanese_wikipedia_word_freq.csv', 'r', encoding="utf-8") as f:
        next(f) # Skip header row.
        for line in f:
            rank, word, *rest = line.split(',')
            frequencies[word] = int(rank)
    return frequencies


def _get_vn_word_frequencies():
    '''
    Maps word to frequency rank in visual novel corpus.
    '''
    frequencies = {}
    with open('visual_novel_word_freq.txt', 'r', encoding="utf-8") as f:
        for (line_number, line) in enumerate(f):
            (freq, pos1, pos2, pos3, pos4, reading_spelling, etym, word_class,
             freq_raw, conj, pronunciation, spelling, *rest) = line.split('\t')
            frequencies[spelling] = line_number
    return frequencies


def _get_narou_word_frequencies():
    '''
    Maps word to frequency rank in corpus.
    '''
    frequencies = {}
    with open('narou_word_freq.txt', 'r', encoding="utf-8") as f:
        for (line_number, line) in enumerate(f):
            (freq, pos1, pos2, pos3, pos4, reading_spelling, etym, word_class,
             freq_raw, conj, pronunciation, spelling, *rest) = line.split('\t')
            frequencies[spelling] = line_number
    return frequencies


def _load_jmdict():
    '''
    Maps JMDict ID to JMDict entry.
    '''
    if not os.path.exists('build/jmdict_eng.json'):
        r = requests.get(JMDICT_JSON_URL, stream=True)
        r.raise_for_status()
        with open('build/jmdict_eng.json.zip', 'wb') as f:
            f.write(r.content)
        zip_ref = zipfile.ZipFile('build/jmdict_eng.json.zip', 'r')
        zip_ref.extractall('build/')
        zip_ref.close()
    with open('build/jmdict_eng.json', 'r', encoding="utf-8") as f:
        jmdict = json.load(f)
    return {entry['id']: entry for entry in jmdict['words']}


def _get_jlpt_lists(jmdict):
    '''
    Maps JLPT level integer to a list of JMDict entries.
    '''
    jlpts = {}
    for level in range(1, 6):
        with open(f'jlpt-n{level}.csv', 'r', encoding="utf-8") as f:
            content = f.readlines()
        items = []
        for line in content:
            if '#' in line:
                continue
            if int(line) not in jmdict:
                print(f'    {int(line)} missing from JMDict; skipping.')
                continue
            items.append(jmdict[int(line)])
        jlpts[level] = items
    return jlpts


def plot_jlpt_list_densities(jlpt_levels, word_frequencies):
    fig, ax = plot.subplots(5, sharex=True)
    ax[0].set_title(
        f'Histogram of JLPT Levels Mapped to Word Frequency List')
    ax[0].set_xlim([0, 10000])
    for (level_number, level_entries) in jlpt_levels.items():
        subplot = ax[level_number - 1]
        subplot.set_ylabel(f'N{level_number}')
        subplot.yaxis.set_visible(False)
        data = set()
        max_ordinal = 0
        for level_entry in level_entries:
            found_data = None
            for entry_subtype in ['kanji', 'kana']:
                for item in level_entry[entry_subtype]:
                    if item['text'] in word_frequencies:
                        frequency_ordinal = word_frequencies[item['text']]
                        found_data = frequency_ordinal
                        max_ordinal = max(frequency_ordinal, max_ordinal)
                        break
                if found_data is not None:
                    break
            if found_data is not None:
                data.add(found_data)

        sorted_data = sorted(list(data))
        n, bins, patches = subplot.hist(
            sorted_data,
            bins=max_ordinal//66,
            density=True,
            histtype='stepfilled',
            color=JLPT_COLORS[level_number])

    plot.show()


def classify():
    _make_build_dir()

    print('Loading JMDict...')
    jmdict = _load_jmdict()

    print('Getting JLPT levels...')
    jlpt_lists = _get_jlpt_lists(jmdict)

    print('Getting Novel Word Frequencies...')
    novel_word_frequencies = _get_cb4960_word_frequencies()
    print('Plotting Novel JLPT histograms...')
    plot_jlpt_list_densities(jlpt_lists, novel_word_frequencies)

    #print('Getting Visual Novels Word Frequencies...')
    #vn_word_frequencies = _get_vn_word_frequencies()
    #print('Plotting Visual Novels JLPT histograms...')
    #plot_jlpt_list_densities(jlpt_lists, vn_word_frequencies)

    #print('Getting Narou Word Frequencies...')
    #narou_word_frequencies = _get_narou_word_frequencies()
    #print('Plotting Narou JLPT histograms...')
    #plot_jlpt_list_densities(jlpt_lists, narou_word_frequencies)

    # I did not find this Wikipedia word freq list useful.
    #print('Getting Wikipedia Word Frequencies...')
    #wikipedia_word_frequencies = _get_wikipedia_word_frequencies()
    #print('Plotting Wikipedia JLPT histograms...')
    #plot_jlpt_list_densities(jlpt_lists, wikipedia_word_frequencies)


if __name__ == '__main__':
    classify()
