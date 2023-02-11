#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from functools import reduce
import os
import zipfile
import sys

import requests

JMDICT_VERSION = '3.3.1'
JMDICT_JSON_URL = 'https://github.com/scriptin/jmdict-simplified/releases/download/3.3.1%2B20230206121907/jmdict-eng-3.3.1+20230206121907.json.zip'
JMDICT_COMMON_JSON_URL = 'https://github.com/scriptin/jmdict-simplified/releases/download/3.3.1%2B20230206121907/jmdict-eng-common-3.3.1+20230206121907.json.zip'
JLPT_COLORS = {
    1: '#d84c43',
    2: '#f6934b',
    3: '#dd9f40',
    4: '#48a17a',
    5: '#5890c5',
}

SKIP_TYPES = {
    'n-pr', 'arch', 'int', 'biol', 'vulg', 'X', 'rare', 'v2k-k', 'v2g-k', 'v2t-k', 'v2d-k', 'v2h-k', 'v2b-k', 'v2m-k', 'v2y-k', 'v2r-k', 'v2k-s', 'v2g-s', 'v2s-s', 'v2z-s', 'v2t-s', 'v2d-s', 'v2n-s', 'v2h-s', 'v2b-s', 'v2m-s', 'v2y-s', 'v2r-s', 'v2w-s', 'v4k', 'v4g', 'v4s', 'v4t', 'v4n', 'v4b', 'v4m', 'v2a-s', 'v4h', 'v4r', 'kyb', 'osb', 'ksb', 'ktb', 'tsb', 'thb', 'tsug', 'kyu', 'rkb', 'nab', 'hob', 'adj-kari', 'adj-ku', 'adj-shiku', 'adj-nari', 'sens', 'astron', 'baseb', 'archit', 'astron', 'bot', 'geol', 'mahj', 'med', 'music', 'Shinto', 'shogi', 'sumo', 'zool', 'joc', 'Buddh', 'chem', 'oK', 'ok', 'obs', 'obsc', 'oik', 'on-mim', 'proverb', 'mil', 'poet', 'physics', 'slang', 'ling', 'geom', 'MA', 'math', 'm-sl', 'col', 'chn', 'hist', 'derog', 'sl',
}
SKIP_ENTRIES = {
    u'わけ': [1502990], # skip 'division'
    u'たち': [1408340], # skip 'long sword'
    u'よし': [1152820], # reed
    u'がたい': [2079640, 2676050], # body build, blastema
}
SKIP_ENTRY_IDS = {
    2014450, # Saint
    1162120, 1243660, 1268170, 1319280, 1334480, 1334570, 1334910, 1461560, 1476730, 1561330, 1300250, 1307180, # month counters
    2230280, # Qing dynasty
    2246360, 2246380, 2246370, 2247250, 2253330, 2253380, 2253370, 2253360, 2253350, 2253410, 2253420, 2254020, 2254070, 2254060, 2254180, 2254170, 2254160, 2246040, # Chinese dynasties
    1240710, # trees
    2830349, 1347690, 2581990, 1309710, 1436460, 2830349, 1551110, 1414430, 1522960, 2765940, 1613900, 1390170, 1537500, 1660180, 1413650, 1395070, 1355750, 1248080, 1729190, 1411530, 1390320, 1596740, 1780070, 1623710, 1785770, 1205470, 1273760, 2645860, 1248950, 1853880, 1316480, 1390410, 1517630, 1498730, 1942530, 1762590, 1302580, 1956440, 1221020, 1661100, 1316730, 1933960, 1498430, 1505580, # unnecessary political/military/govt terms
    1322180, # unnecessary violence
    1486490, # unnecessary sexualization
    1440400, 1042500, 1517200, 1800800, 1345210, 1364860, 1770950, 1940460, 2532610, 1582070, 1042540, # unnecessary religious words
    1111490, # Frank in kana
    1984400, # jyan as in Ta-da!
    2524270, # particle koto indicating a command
    2426110, # Fox with supernatural powers
    1241450, # koto (zither)
    1265960, # ancient city
    1521450, # divining
    2835604, # fold, gets confused with ore as I
    1550770, # historical term ("Japanese league")
    1267460, # groin ("mata")
    2701220, # Moro people
    2207500, # wrong ramen
}
SKIP_GLOSS_SUBSTRINGS = [
    '(Catholic)', '(of China;', '(former province', 'ancient Chinese', 'ancient China', 'Chinese zodiac)',
    ' shogunate', 'ancient Korean', 'Three Kingdoms period', 'Holy Communion', '(Edo-period', '(Edo period',
    '(Muromachi period', '(God of', '(Greek god', '(Confucian', '(god of ', '(city in ', '(in archery', 'non-Yamato', 'Nara-period', '(sensation)', '(of a battlefield', 'Catholic ', '(of China', '(musical)', 'kingdom in China', '(Confucian', '(Roman ', '(dynasty of', '(Edo period', ' in the Edo ', "o'clock", ' dynasty (', 'Chinese state', '(Japanese history', 'historical Japanese', 'the Edo period', '(region)', 'warship', ' noh ',
 ' constellation ', '(Meiji period)', 'in the Edo period', 'former province ', 'one of the Four Books', 'one of the trigrams', 'goddess', 'god of ', 'feudal era ', '(archaeological', 'archaeological mound', 'former province located ', '(language)', ' the I Ching']
SKIP_WORDS = {
    u'うい', # ??
    u'チャン',
    u'まう', # to finish ...
    u'た', # did
    u'あっし', # death by crushing
    u'て', # you said
    u'いく', # some
    u'ウィング', # wing
    u'ヒューズ', # fuse
    u'プラカード', # placard
    u'モーターボート', # motorboat
    u'人狼', # werewolf
    u'幇間', # professional jester
    u'グランデ', # grand
    u'若党', # foot soldier
    u'国府', # Nationalist Government (of China; i.e. under the Kuomintang)
    u'ハンマー', # hammer
    u'ホー', # oh
    u'ルーツ', # roots
    u'ガン', # gun
    u'ます used to indicate respect for the listener (or reader',
    u'自由党', # Liberal Party
    u'ウェイ', # way
    u'守護神', # guardian deity
    u'女子大生',
    u'クルー', # crew
    u'モー', u'ジョン', u'ドン', u'メイス', u'スパー', 
    u'隼人', # Hayato people (ancient)
    u'宋', u'清国', # Song dynasty, other China dynasty words
    u'ベラ', # wrase (fish)
    u'ラヴ', # love
    u'ショート', # short
    u'ラスト', u'ヘッド', u'シティ', u'フル', u'スポンサー', u'プロセス', u'スリー', u'ビルマ', u'ロング',
    u'サリー', # saree
    u'三神', # the three gods of creation
    u'魔法陣', # summoning circle
    u'マニラ', u'ロンドン', u'ニューヨーク', u'ベルリン', u'モスクワ', u'シベリア', u'ウィーン', u'パリ', u'カリフォルニア', u'シカゴ', u'シカゴ', u'河内', u'ワシントン', u'メッカ', u'アムステルダム', u'ナイル', u'バグダード', u'バグダード', u'テキサス', u'リマ', u'ロチェスター', u'蜀', u'ホノルル', # cities/areas outside Japan
    u'難波', # Naniwa (former name for Osaka region)
    u'グリフォン', # griffon
    u'ドワーフ', # dwarf (esp. in folklore or fantasy literature)
    u'信州', # Shinshū (alt. name of former Shinano province)
    u'ピンク色', # pink
    u'犬神', # evil dog spirit
    u'ハイランド', # highland
    u'スリップ', # slip
    u'サック', # sheath
    u'ギャラ', # fee paid to performing artists, etc.
    u'シャフト', # shaft (e.g. machinery)
    u'ストーン', # stone
    u'交尾', # copulation (among animals)
    u'シチュエーション', # situation
    u'ブラ', # bra
    u'アカデミー', # academy
    u'みゆき', # imperial visit
    u'ヤード', # yard (unit of distance)
    u'フン', # Huns
    u'ハンター', # hunter
    u'軍司令官', # army commander
    u'ショール', # shawl
    u'船橋', # pontoon bridge
    u'コネ', # connection
    u'ラッキー', # lucky
    u'バトラー', # butler
    u'人馬', # man and horse
    u'コミュニケー', # communiqué
    u'住職', # chief priest (of a Buddhist temple)
    u'デッキ', # deck (e.g. ship, tape, cassette, observation, train vestibule)
    u'びく', # bhikkhu (fully ordained Buddhist monk)
    u'キング', # king
    u'ムード', # mood
    u'弾正', # judge (of the Imperial Prosecuting and Investigating Office)
    u'レッド', # red
    u'シスター', # sister (sibling)
    u'ゼウス', # Zeus
    u'四天王', # the Four Heavenly Kings
    u'竜神', # dragon god
    u'クリスタル', # crystal
    u'コニャック', # cognac
    u'金太郎', # Kintarō
    u'コスプレ', # cosplay
    u'ラッシュ', # rush
    u'焼酎', # shōchū
    u'シャー', # shah
    u'クラン', # clan
    u'アポロ', # Apollo program
    u'オブ', # of
    u'マーチ', # march
    u'カッター', # cutter
    u'青酸カリ', # potassium cyanide
    u'ディナー', # dinner
    u'マドンナ', # madonna
    u'くノ一', # female ninja
    u'ホープ', # hope
    u'ランタン', # lantern
    u'エッグ', # egg (esp. chicken eggs)
    u'マンモス', # mammoth
    u'コカイン', # cocaine
    u'ブローカー', # broker
    u'カウント', # count
    u'軍馬', # warhorse
    u'邪神', # evil god
    u'オウム', # Aum Shinrikyo
    u'カトリック', # Catholic
    u'ラッド', # common rudd
    u'インキ', # ink
    u'アタッシェケース', # attaché case
    u'ギャル', # gyaru
    u'ユーモラス', # humorous
    u'修道女', # (Catholic) nun
    u'アイドル', # performer
    u'アトラス', # Atlas
    u'鶯', # Japanese bush warbler
    u'マックス', # maximum
    u'バール', # bar
    u'メガ', # mega
    u'ストリップ', # strip show
    u'コサック', # Cossack
    u'スタッド', # stud
    u'スキュラ', # Scylla monster
    u'オランダ人',
    u'永禄', # Eiroku era
    u'貂', # Japanese marten
    u'グレイス', # grace
    u'ブレイク', # break (rest)
    u'ポーカー', # poker
    u'ブレード', # blade
    u'袍', # hou, round neck robe for imperial court
    u'ラブレター', # love letter
    u'ゴリ', # a specific fish
    u'エアロック', # air lock
    u'キュー', # cue (billiards, pool)
    u'トランス', # transformer
    u'舞子', # Maiko
    u'大納言', # chief councillor of state
    u'スタン', # stun
    u'リン', # ring or name?
    u'リリー', # lily
    u'フット', # foot
    u'焼夷弾', # incendiary bomb
    u'ブレイク', # break (rest)
    u'スロープ', # slope
    u'てる', # teiru but finds weird matches, colloquialism
    u'ナチス',
    u'ウルフ', # wolf
    u'ビーム', u'エッセイ', u'パック', u'ホーン', u'ハント', u'オー', u'ディス', u'ベイ',
    u'ショート',
    u'ロ', # iroha poem system, and music term.
    u'尺', # shaku unit of distance
    u'レス', # respond (abbr)
    u'シート', u'ヒル', u'ビュー', u'ノブ', u'ジャングル',
    u'庵', # hermitage
    u'ピアニスト',
    u'ターゲット',
    u'ボストンバッグ',
    u'宦官', # eunuch
    u'エルフ', u'アラン', u'フッ', u'ナン', u'プロレス', u'ヒステリー', u'ステラ', u'フレンチ',
    u'殺人鬼', # bloodthirsty killer
    u'マジック',
    u'平家', # historical term
    u'睾丸', # testicles
    u'強姦', # rape
    u'斬る', u'太刀', u'おの', u'ドス', u'脇差', # to kill using a blade; sword terms
    u'キャスター', u'バーン',
    u'殺意', # intent to kill
    u'宮城', # imperial palace esp. from 1888-1946
    u'爆撃', # bomding (raid)
    u'琵琶', # biwa (lute)
    u'警視庁', u'警視', u'警部', u'巡査', # metropolitan police dept, other police words
    u'マスト', u'スー', u'フェ', u'リック', u'ビスケット',
    u'ジプシー',
    u'矛', # Chinese spear
    u'ディレクター', u'エース', u'トー', u'ゴー', u'ブラジャー', u'グリフィン',
    u'プライベート', u'ブルック', u'ヒロイン', u'クラフト', u'ベンツ', u'ブラウン',
    u'パルス', u'サイド', u'エリート', u'ライ', u'インデックス', u'アーチャー',
    u'グリーン', u'ランス', u'ボクシング', u'シエスタ',
    u'どす', # dagger
    u'連隊長', # regimental commander
    u'兵法', # art of war
    u'裁判長', # presiding judge
    u'クソ',
    u'マフィア',
    u'水割り', # cutting alcohol
    u'日露戦争', # Russo-Japanese War
    u'マール', # volcano crater
    u'征伐', # conquest
    u'べ',
    u'厚子', # ainu elm bark clothes
    u'ぬ',
    u'お',
    u'う',
    u'しれる', # to become known
    u'ねえ', # right?
    u'レ', u'レイ', u'えと', u'クイーン', u'プリンス', u'ワン', u'ロー', u'ジン', u'フランク',
    u'ワイ', u'ニック', u'ムッソリーニ', u'クロス', u'クスクス', u'ウー', u'スケッチ',
    u'ブス',
    u'ボン', # good
    u'ブタ',
    u'茜', # Japanese madder
    u'クララ', # Sophora flavescens
    u'オレンジ色',
    u'本陣', # troop HQ
    u'領主', # feudal lord
    u'旗本', # shogunal vassal
    u'エスパー', # ESPer
    u'ヒーロー', # hero
    u'オール', u'ハッチ',
    u'魔王', # Satan
    u'ハート', u'ローズ', u'エル', u'サム', u'ジョー', u'マーク', u'フィリップ',
    u'ハード',
    u'花鶏', # brambling (bird)
    u'ですが', # but
    u'イギリス人', u'中国人', u'アメリカ人', u'ユダヤ人', u'フランス人', u'ドイツ人', u'インディアン',
    u'ドイツ語', u'タイ', u'イタリア人', u'韓国人', u'ロシア人', u'フランス語', u'ラテン語', u'日本人',
    u'クリ', u'ペニス', '男根', u'性器', u'股間', u'膣', u'勃起', u'陰茎', # specific genital
    u'ユリ', u'タラ', u'ケイ',
    u'結界', # temple boundaries
    u'ドクター', u'エリア',
    u'ライフル',
    u'コル',
    u'巫女', # miko
    u'チン',
    u'ジープ', u'バーサーカー',
    u'特攻', u'心中', u'自殺', u'遺書', u'切腹', u'自害', # suicide
    u'ビクター', # victor
    u'セールスマン', # salesman
    u'シリング', # shillin
    u'ケイン', # cane
    u'ヒトラー',
    u'チビ', # "small child"
    u'洗礼', # baptism
    u'ゴースト',
    u'拍車', # riding spur
    u'津軽', # Tsugaru in Aomori
    u'シャン', # beautiful
    u'ソウル',
    u'グラント', u'ブラッド',
    u'生首', # freshly severed head
    u'デー', # day (as in holiday)
    u'皆殺し', # massacre
    u'ナチ', u'ナチス', u'ヒットラー', # Nazi
    u'海兵隊', # Marine Corps
    u'同人誌', # dōjinshi
    u'山の神', # mountain god
    u'井戸端', # side of well
    u'キャン', # yelp
    u'アタック', # attack
    u'艦船', # warships and other vessels
    u'福音書', # the Gospels
    u'チャクラ', # chakra
    u'リアリティ', # reality
    u'総司令官', # commander-in-chief
    u'クリーム色', # cream (colour, color)
    u'フィン', # (diving) fin
    u'リンチ', # beating (inflicted as punishment)
    u'チャンピオン', # champion
    u'ガール', # girl
    u'旧約聖書', # Old Testament
    u'般若', # prajna (wisdom required to attain enlightenment)
    u'サンダー', # thunder
    u'テイラー', # tailor
    u'ポリス', # police
    u'血だらけ', u'血まみれ', u'致命傷', # covered in blood; wounds
    u'ブラック',
    u'アナ',
    u'レス', #ereply (on an Internet message board, chat clitnt, etc.)
    u'聖職者', # clergyman
    u'クッキー', # cookie
    u'女体',
    u'ファミリー',
    u'クソ', # damn
    u'御台所', # wife of a shogun
    u'リムジン', # limousine
    u'ユニコーン', # unicorn
    u'ハーン', # khan
    u'カーン', # kern
    u'パンティ',
    u'コンドーム', # condom
    u'キャンバス', # canvas
    u'キラー', # killer
    u'キック', # kick
    u'ハイジャック', # hijack
    u'ビキニ', # bikini (swimwear)
    u'モルヒネ', # morphine
    u'武家屋敷', # samurai residence
    u'ワゴン',
    u'二ノ宮', # 2nd most important imperial shrine
    u'ウエスト', u'ダリア', u'マシーン', u'クリア', u'カイロ', u'フラ', u'ダッシュ',
    u'カイ', # chi (greek)
    u'エイダ', u'モーツァルト', u'リリアン',
    u'大黒', # god of wealth
    u'売春', u'遊女', u'女郎', u'娼婦',
    u'ホワイト', u'マック', u'コマ',
    u'後宮', # inner palace reserved for women
    u'なでしこ', # pink (flower type)
    u'アオイ', u'真弓', u'真木', u'ポワロ', u'葵', u'せり', u'榊', u'芭蕉', u'伊吹', u'藤', u'李', u'カシュー', u'桔梗', u'青柳', u'メリッサ', u'正木', u'萩', u'鳶', u'葛', u'狸', u'蔦', u'山吹', u'ゆり', u'郁子', u'山吹', u'欅', u'ヒース', u'赤木', u'ナギ', u'クス', # random plants
    u'皇后', # (Japanese) empres
    u'関ケ原', # Sekigahara (battle site, 1600)
    u'レベリオン', # rebellion
    u'バスト', # bust (measurement)
    u'ギリシア人', u'ヨーロッパ人',
    u'ブーメラン', # boomerang
    u'如来', # Tathagata
    u'いい天気',
    u'グリップ', # grip
    u'シップ', # ship
    u'マドレーヌ', # madeleine (cake)
    u'マジック', # magic
    u'ビジネスマン', # businessman
    u'マスターズ', # the Masters (golf tournament)
    u'テール', # tail
    u'御前会議', # Imperial Council
    u'キャバレー', # cabaret
    u'剣客', # master swordsman
    u'コーン', # cone
    u'ディン', u'ジェイ', u'ミスター', u'パ', u'マス', u'トラップ', u'ジェイ',
    u'越', # ancient china kingdom, abbreviation for vietnam
    u'フィート', u'キリスト教',
    u'旗本', # shogunal vassal
    u'家臣', # vassal
    u'ん', # yes
    u'シェル', # unix shell
    u'ン', u'あら',
    u'わし', # old timer contraction of watashi I think, from old books maybe
    u'ホ', u'リム', u'ゴブリン', u'ショット',
    u'鳳', u'翡翠', # chinese firebird; animals
    u'ホームズ',
    u'ハムレット',
    u'マン', #  man
    u'キリスト教徒', # Christian
    u'キリスト教', # Christianity
    u'メイド',
    u'おいおい',
    u'ろ',
    u'ヘリオス', # Helios
    u'ギロチン', # guillotine
    u'シェリー', # sherry
    u'スコープ', # scope
    u'テレ', # tele
    u'ペンス', # pence (monetary unit)
    u'ノーマル', # normal
    u'アーミン', # ermine
    u'ヘア', # hair (of the head
    u'げー', # yuck
    u'文久', # Bunkyū era
    u'そ',
    u'クラスメート',
    u'ツイ', # Twitter
    u'ウインドウ', # window
    u'エーテル', # ether
    u'ブック', # book
    u'マガジン', # magazine
    u'テラ', # tera-
    u'アルプス', # the Alps
    u'ホームレス', # homeless
    u'ティッシュ', # tissue
    u'ごまかし', # hanky-panky
    u'チョン', # derogatory slang
    u'ハリス',
    u'ディーン', # dean
    u'ノエル', # Christmas
    u'モビル',
    u'イブ', # eve (esp. Christmas Eve)
    u'浮気', # extramarital sex
    u'オナニー',
    u'勃起', # erection
    u'売春婦',
    u'ぢ', # hemorrhoids
    u'レオ',
    u'セックス', u'性欲', u'エロ',
    u'地蔵', # buddhist word
    u'糞', # kuso
    u'スペード', # spades (suit)
    u'ヨ',
    u'領民', # population of a fief
    u'溺死', # death by drowning
    u'パット', # putt
    u'ジュール', # joule
    u'律', # ancient east asian law
    u'御子', # Son of God
    u'一万円',
    u'フルート', # flute
    u'クオリア', # quale
    u'聖戦', # holy war
    u'テレパシー', # telepathy
    u'イングランド', # England
    u'バリケード', # barricade
    u'魔剣', # magic sword
    u'袈裟', # kasaya
    u'ピット', # pit
    u'永禄', # Eiroku era
    u'サッカー', # soccer
    u'グレイ', # grey
    u'ベージュ', # beige
    u'スコッチ', # Scotch
    u'聖母', # holy mother
    u'聖杯', # chalice (for Holy Communion)
    u'キリスト', # Christ
    u'麻', # cannabis
    u'マダム', # madam
    u'キノ', # keno (casino game)
    u'スパイ', # spy
    u'メイ', # May
    u'セ', # Central League (Japanese baseball league)
    u'ぶす', # ugly woman
    u'殿様', # nobleman
    u'チェッカー', # checkers (board game)
    u'ホステス', # hostess
    u'ライダー', # rider
    u'ダンブル', # ship's hold
    u'くそ', # damn
    u'説教', # sermon
    u'畜生', # damnit
    u'アッラー', # allah
    u'ホントに',
    u'怨霊', # revengeful ghost
    u'殺し屋', # pro killer
    u'殺人犯', # murderer
    u'フォード', u'マリア',
    u'レイン',
    u'ゝ', u'ゞ', u'ヽ', # repetition mark
    u'男爵', # baron
    u'ピストル', u'小銃', u'機関銃', u'拳銃', # guns
    u'殺人事件', # murder case
    u'フォン', u'ホン', # phon (unit of loudness)
    u'きく', # covered already by 聞く in JLPT list
    u'ゴシック体', # Gothic typeface (shows up as N4)
    u'がたい', # jmdict matches to other words, not the grammar construct bc nikui matches separately
}


def _char_is_cjk(character):
    return any([start <= ord(character) <= end for start, end in 
                [(4352, 4607), (11904, 42191), (43072, 43135), (44032, 55215), 
                 (63744, 64255), (65072, 65103), (65381, 65500), 
                 (131072, 196607)]
                ])


def _is_cjk(s: str) -> bool:
    return all(_char_is_cjk(c) for c in s)


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
    if not os.path.exists(f'build/jmdict-eng-{JMDICT_VERSION}.json'):
        r = requests.get(JMDICT_JSON_URL, stream=True)
        r.raise_for_status()
        with open('build/jmdict_eng.json.zip', 'wb') as f:
            f.write(r.content)
        zip_ref = zipfile.ZipFile('build/jmdict_eng.json.zip', 'r')
        zip_ref.extractall('build/')
        zip_ref.close()
    with open(f'build/jmdict-eng-{JMDICT_VERSION}.json', 'r', encoding="utf-8") as f:
        jmdict = json.load(f)
    return {int(entry['id']): entry for entry in jmdict['words']}


def _load_jmdict_common():
    '''
    Maps JMDict ID to JMDict entry.
    '''
    if not os.path.exists(f'build/jmdict-eng-common-{JMDICT_VERSION}.json'):
        r = requests.get(JMDICT_COMMON_JSON_URL, stream=True)
        r.raise_for_status()
        with open('build/jmdict_eng_common.json.zip', 'wb') as f:
            f.write(r.content)
        zip_ref = zipfile.ZipFile('build/jmdict_eng_common.json.zip', 'r')
        zip_ref.extractall('build/')
        zip_ref.close()
    with open(f'build/jmdict-eng-common-{JMDICT_VERSION}.json', 'r', encoding="utf-8") as f:
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


def match_word(word, all_jmes, used_ids=set()):
    found_data = None
    for kana_only in [True, False]:
        if found_data is not None:
            continue
        if kana_only and not _is_kana(word):
            continue

        for jme in all_jmes:
            # TODO: It should iterate over candidate senses and reject in turn if any fail,
            # instead of approving each qualification independently.
            if int(jme['id']) in SKIP_ENTRIES.get(word, []) or int(jme['id']) in SKIP_ENTRY_IDS or int(jme['id']) in used_ids:
                continue

            ok_pos = False
            for pos in [e['partOfSpeech'] for e in jme['sense']]:
                if ok_pos:
                    break
                for single_pos in pos:
                    if single_pos not in SKIP_TYPES:
                        ok_pos = True
                        break
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

            ok_misc = False
            for misc in [e['misc'] for e in jme['sense']]:
                if all(t not in misc for t in SKIP_TYPES):
                    ok_misc = True
            if not ok_misc:
                continue

            if word in [e['text'] for e in jme['kanji'] if not {t for t in e['tags']}.intersection(SKIP_TYPES)] or word in [e['text'] for e in jme['kana'] if not {t for t in e['tags']}.intersection(SKIP_TYPES)]:
                if kana_only and len(jme['kanji']) > 0:
                    continue
                if len(jme['kanji']) > 0 and not _is_cjk(jme['kanji'][0]['text']):
                    continue
                found_data = jme
                break
    return found_data


def write_jlpt_levels(all_jmes, jlpt_levels, word_frequencies):
    vocab_counts = {
        5: 800,
        4: 1500,
        3: 3750,
        2: 6000,
        1: 10000,
    }
    words = [e[0] for e in sorted(word_frequencies.items(), key=lambda x: x[1])]
    used_words = set()
    used_ids = set()

    for (level_number, level_entries) in sorted(jlpt_levels.items(), key=lambda x: -x[0]):
        offset = 0
        with open(f'build/jlpt-n{level_number}.txt', 'w', encoding="utf-8") as f:
            for entry in level_entries:
                print(f"N{level_number} {entry['id']} {entry['kanji'][0] if entry['kanji'] else entry['kana'][0]} {entry['sense'][0]['gloss'][0]['text']}")
                f.write(f"{entry['id']}\n")
                used_ids.add(int(entry['id']))
                # TODO: this kana dedupe could be improved
                if any('uk' in s['misc'] for s in entry['sense']) or any(kana['common'] for kana in entry['kana']) or not entry['kanji']:
                    for kana in entry['kana']:
                        used_words.add(kana['text'])
                for kanji in entry['kanji']:
                    used_words.add(kanji['text'])
                for sense in entry['sense']:
                    for related in sense['related']:
                        used_words.add(related[0])
            offset += len(level_entries)
            remaining = vocab_counts[level_number] - offset

            for word in words:
                if word in SKIP_WORDS:
                    continue
                if word in used_words:
                    continue

                found_data = match_word(word, all_jmes, used_ids=used_ids)

                if found_data is not None:
                    print(f"N{level_number} {found_data['id']} {word} {found_data['sense'][0]['gloss'][0]['text']}")
                    #f.write(f"{found_data['id']} # {word} {found_data['sense'][0]['gloss'][0]['text']}")
                    f.write(f"{found_data['id']}\n")
                    offset += 1
                    remaining -= 1
                    
                    used_ids.add(int(found_data['id']))
                    for kanji in found_data['kanji']:
                        used_words.add(kanji['text'])
                    used_words.add(word)
                    if any('uk' in s['misc'] for s in found_data['sense']) or any(kana['common'] for kana in found_data['kana']) or not found_data['kanji']:
                        for kana in found_data['kana']:
                            used_words.add(kana['text'])
                    for sense in found_data['sense']:
                        for related in sense['related']:
                            used_words.add(related[0])
                else:
                    print(f"Skipping {word}")

                if remaining == 0:
                    print()
                    break


def plot_jlpt_list_densities(jlpt_levels, word_frequencies):
    # https://stackoverflow.com/a/48374671/89373
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plot

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


def classify(search=None):
    _make_build_dir()

    print('Loading JMDict...')
    jmdict = _load_jmdict()
    jmdict_common = _load_jmdict_common()
    all_jmes = list(jmdict_common.values()) + list(jmdict.values())

    print('Getting JLPT levels...')
    jlpt_lists = _get_jlpt_lists(jmdict)

    print('Getting Novel Word Frequencies...')
    novel_word_frequencies = _get_cb4960_word_frequencies()
    if search is None:
        print('Writing JLPT levels per Novel Word Frequencies...')
        write_jlpt_levels(all_jmes, jlpt_lists, novel_word_frequencies)
    else:
        return match_word(search, all_jmes)
    if search is not None:
        return search_match
    #print('Plotting Novel JLPT histograms...')
    #plot_jlpt_list_densities(jlpt_lists, novel_word_frequencies)

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
    if len(sys.argv) == 2:
        search = sys.argv[1]
        match = classify(search=search)
        if match is None:
            print("No match")
        else:
            print(f"{match['id']} {match['sense'][0]['gloss'][0]['text']}")
    else:
        classify()
