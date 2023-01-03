#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from functools import reduce
import os
import zipfile

# https://stackoverflow.com/a/48374671/89373
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plot
import requests


JMDICT_JSON_URL = 'https://github.com/scriptin/jmdict-simplified/releases/download/3.2.0%2B20230102121435/jmdict-eng-3.2.0+20230102121435.json.zip'
JMDICT_COMMON_JSON_URL = 'https://github.com/scriptin/jmdict-simplified/releases/download/3.2.0%2B20230102121435/jmdict-eng-common-3.2.0+20230102121435.json.zip'
JLPT_COLORS = {
    1: '#d84c43',
    2: '#f6934b',
    3: '#dd9f40',
    4: '#48a17a',
    5: '#5890c5',
}

SKIP_TYPES = {
    'n-pr', 'arch', 'int', 'biol', 'vulg', 'X', 'rare', 'v2k-k', 'v2g-k', 'v2t-k', 'v2d-k', 'v2h-k', 'v2b-k', 'v2m-k', 'v2y-k', 'v2r-k', 'v2k-s', 'v2g-s', 'v2s-s', 'v2z-s', 'v2t-s', 'v2d-s', 'v2n-s', 'v2h-s', 'v2b-s', 'v2m-s', 'v2y-s', 'v2r-s', 'v2w-s', 'v4k', 'v4g', 'v4s', 'v4t', 'v4n', 'v4b', 'v4m', 'v2a-s', 'v4h', 'v4r', 'kyb', 'osb', 'ksb', 'ktb', 'tsb', 'thb', 'tsug', 'kyu', 'rkb', 'nab', 'hob', 'adj-kari', 'adj-ku', 'adj-shiku', 'adj-nari', 'sens', 'astron', 'baseb', 'archit', 'astron', 'bot', 'geol', 'mahj', 'med', 'music', 'Shinto', 'shogi', 'sumo', 'zool', 'joc', 'Buddh', 'chem', 'oK', 'ok', 'obs', 'obsc', 'oik', 'on-mim', 'pn', 'proverb', 'mil', 'poet', 'physics', 'slang', 'ling', 'geom', 'MA', 'math', 'm-sl', 'col',
}
SKIP_ENTRIES = {
    u'わけ': [1502990], # skip 'division'
}
SKIP_ENTRY_IDS = {
    2014450, # Saint
    1162120, 1243660, 1268170, 1319280, 1334480, 1334570, 1334910, 1461560, 1476730, 1561330, 1300250, 1307180, # month counters
    2230280, # Qing dynasty
    2246360, 2246380, 2246370, 2247250, 2253330, 2253380, 2253370, 2253360, 2253350, 2253410, 2253420, 2254020, 2254070, 2254060, 2254180, 2254170, 2254160, 2246040, # Chinese dynasties
    1240710, # trees
    2830349, 1347690, 2581990, 1309710, 1436460, 2830349, 1551110, 1414430, 1522960, 2765940, 1613900, 1390170, 1537500, # unnecessary political/military terms
    1111490, # Frank in kana
    1984400, # jyan as in Ta-da!
    2524270, # particle koto indicating a command
    2426110, # Fox with supernatural powers
}
SKIP_GLOSS_SUBSTRINGS = [
    '(Catholic)', '(of China;', '(former province', 'ancient Chinese', 'ancient China,' 'Chinese zodiac)',
    ' shogunate', 'ancient Korean', 'Three Kingdoms period', 'Holy Communion', '(Edo-period',
    '(Muromachi period', '(God of', '(Greek god', '(Confucian', '(god of ', '(city in ', '(in archery', 'non-Yamato', 'Nara-period', '(sensation)', '(of a battlefield', 'Catholic ', '(of China', '(musical)', 'kingdom in China', '(Confucian', '(Roman ', '(dynasty of', '(Edo period', ' in the Edo ',
]
SKIP_WORDS = {
    u'モー', u'ジョン', u'ドン', u'メイス', u'スパー', 
    u'隼人', # Hayato people (ancient)
    u'ベラ', # wrase (fish)
    u'ラヴ', # love
    u'マニラ', u'ロンドン', u'ニューヨーク', # cities outside Japan
    u'宦官', # eunuch
    u'エルフ', u'アラン', u'フッ', u'ナン', u'プロレス', u'ヒステリー',
    u'殺人鬼', # bloodthirsty killer
    u'睾丸', # testicles
    u'強姦', # rape
    u'警視庁', u'警視', u'警部', u'巡査', # metropolitan police dept, other police words
    u'マスト', u'スー', u'フェ', u'リック',
    u'矛', # Chinese spear
    u'ディレクター', u'エース', u'トー', u'ゴー', u'ブラジャー', u'グリフィン',
    u'プライベート', u'ブルック', u'ヒロイン', u'クラフト', u'ベンツ', u'ブラウン',
    u'パルス', u'サイド', u'エリート', u'ライ', u'インデックス', u'アーチャー',
    u'グリーン', u'ランス', u'ボクシング', u'シエスタ',
    u'どす', # dagger
    u'連隊長', # regimental commander
    u'兵法', # art of war
    u'裁判長', # presiding judge
    u'水割り', # cutting alcohol
    u'日露戦争', # Russo-Japanese War
    u'べ',
    u'ぬ',
    u'お',
    u'う',
    u'しれる', # to become known
    u'ねえ', # right?
    u'レ', u'レイ', u'えと', u'クイーン', u'プリンス', u'ワン', u'ロー', u'ジン', u'フランク',
    u'ワイ', u'ニック', u'ムッソリーニ', u'クロス', u'クスクス', u'ウー',
    u'ブタ',
    u'茜', # Japanese madder
    u'クララ', # Sophora flavescens
    u'オレンジ色',
    u'本陣', # troop HQ
    u'オール', u'ハッチ',
    u'魔王', # Satan
    u'ハート', u'ローズ', u'エル', u'サム', u'ジョー',
    u'イギリス人', u'中国人', u'アメリカ人', u'ユダヤ人', u'フランス人', u'ドイツ人', u'インディアン',
    u'ドイツ語', u'タイ', u'イタリア人', u'韓国人', u'ロシア人', u'フランス語', u'ラテン語',
    u'クリ', u'ペニス', '男根', u'性器', # specific genital
    u'ユリ', u'タラ', u'ケイ',
    u'結界', # temple boundaries
    u'ドクター',
    u'ライフル',
    u'コル',
    u'巫女', # miko
    u'チン',
    u'ジープ', u'バーサーカー',
    u'特攻', # suicide attack
    u'ヒトラー',
    u'洗礼', # baptism
    u'ゴースト',
    u'拍車', # riding spur
    u'津軽', # Tsugaru in Aomori
    u'シャン', # beautiful
    u'ソウル',
    u'グラント', u'ブラッド',
    u'生首', # freshly severed head
    u'皆殺し', # massacre
    u'血だらけ', # covered in blood
    u'女体',
    u'ファミリー',
    u'ハーン', # khan
    u'パンティ',
    u'二ノ宮', # 2nd most important imperial shrine
    u'ウエスト', u'ダリア', u'マシーン', u'クリア', u'カイロ', u'フラ', u'ダッシュ',
    u'カイ', # chi (greek)
    u'エイダ', u'モーツァルト', u'リリアン',
    u'大黒', # god of wealth
    u'売春', u'遊女', u'女郎', u'娼婦',
    u'ホワイト', u'マック', u'コマ',
    u'後宮', # inner palace reserved for women
    u'なでしこ', # pink (flower type)
    u'アオイ', u'真弓', u'真木', u'ポワロ', # random plants
    u'クラスメート',
    u'モビル',
    u'浮気', # extramarital sex
    u'ぢ', # hemorrhoids
    u'レオ',
    u'セックス',
    u'地蔵', # buddhist word
    u'糞', # kuso
    u'ヨ',
    u'領民', # population of a fief
    u'溺死', # death by drowning
    u'パット', # putt
    u'ジュール', # joule
    u'律', # ancient east asian law
    u'ダンブル', # ship's hold
    u'アッラー', # allah
    u'フォード', u'マリア',
    u'レイン',
    u'ゝ', # repetition mark
    u'男爵', # baron
    u'ピストル', u'小銃', u'機関銃', u'拳銃', # guns
    u'殺人事件', # murder case
    u'フォン', # phon (unit of loudness)
}

def _char_is_kana(c) -> bool:
    return (u'\u3040' <= c <= u'\u309F') or (u'\u30A0' <= c <= u'\u30FF')

def _is_kana(s: str) -> bool:
    return all(_char_is_kana(c) for c in s)

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
    if not os.path.exists('build/jmdict-eng-3.2.0.json'):
        r = requests.get(JMDICT_JSON_URL, stream=True)
        r.raise_for_status()
        with open('build/jmdict_eng.json.zip', 'wb') as f:
            f.write(r.content)
        zip_ref = zipfile.ZipFile('build/jmdict_eng.json.zip', 'r')
        zip_ref.extractall('build/')
        zip_ref.close()
    with open('build/jmdict-eng-3.2.0.json', 'r', encoding="utf-8") as f:
        jmdict = json.load(f)
    return {int(entry['id']): entry for entry in jmdict['words']}


def _load_jmdict_common():
    '''
    Maps JMDict ID to JMDict entry.
    '''
    if not os.path.exists('build/jmdict-eng-common-3.2.0.json'):
        r = requests.get(JMDICT_COMMON_JSON_URL, stream=True)
        r.raise_for_status()
        with open('build/jmdict_eng_common.json.zip', 'wb') as f:
            f.write(r.content)
        zip_ref = zipfile.ZipFile('build/jmdict_eng_common.json.zip', 'r')
        zip_ref.extractall('build/')
        zip_ref.close()
    with open('build/jmdict-eng-common-3.2.0.json', 'r', encoding="utf-8") as f:
        jmdict = json.load(f)
    return {int(entry['id']): entry for entry in jmdict['words']}


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
            if int(line) not in jmdict.keys():
                print(f'    {int(line)} missing from JMDict; skipping.')
                continue
            items.append(jmdict[int(line)])
        jlpts[level] = items
    return jlpts


def write_jlpt_levels(jmdict, jmdict_common, jlpt_levels, word_frequencies):
    vocab_counts = {
        5: 800,
        4: 1500,
        3: 3750,
        2: 6000,
        1: 10000,
    }
    words = [e[0] for e in sorted(word_frequencies.items(), key=lambda x: x[1])]
    used_words = set()

    all_jmes = list(jmdict_common.values()) + list(jmdict.values())

    for (level_number, level_entries) in sorted(jlpt_levels.items(), key=lambda x: -x[0]):
        offset = 0
        with open(f'build/jlpt-n{level_number}.txt', 'w', encoding="utf-8") as f:
            for entry in level_entries:
                f.write(f"{entry['id']}\n")
                for kana in entry['kana']:
                    used_words.add(kana['text'])
                for kanji in entry['kanji']:
                    used_words.add(kanji['text'])
            offset += len(level_entries)
            remaining = vocab_counts[level_number] - offset

            for word in words:
                if word in SKIP_WORDS:
                    continue
                if word in used_words:
                    continue

                found_data = None
                for kana_only in [True, False]:
                    if found_data is not None:
                        continue
                    if kana_only and not _is_kana(word):
                        continue

                    for jme in all_jmes:
                        if int(jme['id']) in SKIP_ENTRIES.get(word, []) or int(jme['id']) in SKIP_ENTRY_IDS:
                            continue

                        ok_pos = False
                        for pos in [e['partOfSpeech'] for e in jme['sense']]:
                            if not set(pos).intersection(SKIP_TYPES):
                                ok_pos = True
                        if not ok_pos:
                            continue

                        ok_gloss = False
                        for gloss in [e['gloss'] for e in jme['sense']]:
                            for gloss_text in [g['text'] for g in gloss]:
                                if all(t not in gloss_text for t in SKIP_GLOSS_SUBSTRINGS):
                                    ok_gloss = True
                        if not ok_gloss:
                            continue

                        ok_field = False
                        for field in [e['field'] for e in jme['sense']]:
                            if all(t not in field for t in SKIP_TYPES):
                                ok_field = True
                        if not ok_field:
                            continue

                        if word in [e['text'] for e in jme['kanji'] if not {t for t in e['tags']}.intersection(SKIP_TYPES)] or word in [e['text'] for e in jme['kana'] if not {t for t in e['tags']}.intersection(SKIP_TYPES)]:
                            if kana_only and len(jme['kanji']) > 0:
                                continue
                            found_data = jme
                            break

                if found_data is not None:
                    print(f"N{level_number} {found_data['id']} {word} {found_data['sense'][0]['gloss'][0]['text']}")
                    #f.write(f"{found_data['id']} # {word} {found_data['sense'][0]['gloss'][0]['text']}")
                    f.write(f"{found_data['id']}\n")
                    offset += 1
                    remaining -= 1
                else:
                    print(f"Skipping {word}")

                if remaining == 0:
                    print()
                    break


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
    jmdict_common = _load_jmdict_common()

    print('Getting JLPT levels...')
    jlpt_lists = _get_jlpt_lists(jmdict)

    print('Getting Novel Word Frequencies...')
    novel_word_frequencies = _get_cb4960_word_frequencies()
    print('Writing JLPT levels per Novel Word Frequencies...')
    write_jlpt_levels(jmdict, jmdict_common, jlpt_lists, novel_word_frequencies)
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
