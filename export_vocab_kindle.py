import os
import sqlite3


import time
import genanki
from gtts import gTTS 
from PIL import Image
from six import BytesIO
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from textblob import TextBlob
import eng_to_ipa as Ipa

from PyDictionary import PyDictionary


# https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()


class KindleToAnki:
  def __init__(self):
    self.pydict = PyDictionary()

  def text_to_speech_file(self, text, output_file = 'text.mp3', language = 'en'):
    speech = gTTS(text = text, lang = language, slow = False)
    speech.save(output_file)
    return output_file

  def get_data_from_database(self, path =  "/media/nightfury/Kindle/system/vocabulary/vocab.db"):
    print("Path :",path)
    con = sqlite3.connect(path)
    cur = con.cursor()
    cur.execute("SELECT word, lang, stem FROM words")
    word_stem_lang = cur.fetchall()
    # print(word_stem_lang)

    self.word_dict = {} # word -> [lang, stem, usage]
    # Modify data 
    for tup in word_stem_lang: 
      self.word_dict[tup[0]] = [tup[1], tup[2]]
    
    cur.execute("SELECT word_key, usage FROM lookups")
    words_and_usages = cur.fetchall()
    for tup in words_and_usages:
      self.word_dict[tup[0][3:]].append(tup[1])

    # Delete database
    # cur.execute("DROP TABLE lookups")
    # cur.execute("DROP TABLE words")
    # print("Deleted")


  
  def create_deck_anki(self):
    self.my_model = genanki.Model(
      1380120064,
      'Example',
      fields=[
        {'name': 'Word'},
        {'name': 'Ipa'},
        {'name': 'Sound'},
        {'name': 'Translation'},
        {'name': 'Definition'},
        {'name': 'Usage'}
      ],
      templates=[
        {
          'name': 'Card 1',
          'qfmt': '{{Word}}   {{Ipa}}',
          'afmt': '{{FrontSide}} <br> <hr id="answer"> {{Translation}} <br> {{Usage}} {{Sound}} <br>  {{Definition}} '  
        },
      ])

    self.my_deck = genanki.Deck(
      # 2059400191,
      205940019,
      'Google')

    self.my_package = genanki.Package(self.my_deck)
    self.my_package.media_files = []
    # Add note after this line
  
  def add_note_to_anki(self, word, sound_name, translation, usage, ipa, meaning):
    note = genanki.Note(
      model=self.my_model,
      fields=[word, 
        ipa,
        "[sound:{}]".format(sound_name),
        translation,
        meaning,
        usage,
        ])
    self.my_deck.add_note(note)
    # add location of img or audio file
    self.my_package.media_files.append('sounds/' + sound_name) 
    print("Added new word successfully : %s | %s | %s " % (word, ipa, sound_name))

  def export_deck(self):
    self.my_package.write_to_file('output.apkg')

  # def translate(self, text, language = 'vi'):
    # print("translate : " , text)
    # translate = self.pydict.translate(text, "vi")
    # return translate

  def meaning(self, text, language = 'vi'):
    meaning = self.pydict.meaning(text)
    if meaning is None:
      return "Unrecognized word in the database :("

    # Transform to a string-like
    s = "-------<b>Definition:</b>-------<br>"
    for form in meaning.keys():
      s += '<b>'+ form + ':</b>' + '<br>'
      # print(meaning[form])
      fix_meaning = "<br> - ".join(meaning[form]) + "<br>"
      fix_meaning = fix_meaning.replace(text, '<b>' + text + '</b>')
      s += fix_meaning
    return s

  def translate(self, text, language = 'vi'):
    try:
      analysis = TextBlob(text)
      vi = analysis.translate(from_lang='en', to=language)
      return str(vi)
    except Exception as E:
      print(E)
      return "error (Max=~100 words per day)"

  def generate_note(self):
    i = 0
    # For testing : 
    # self.word_dict = {"book":["pass", "book", "I have a book"], "school": ["pass", "school", "I go to school"]}
    l = len(self.word_dict.keys())
    for word in self.word_dict.keys():
      stem = self.word_dict[word][1]
      usage = "<b>Usage:</b> <br>"
      usage += self.word_dict[word][2]
      usage = usage.replace(stem, '<b>' + stem + '</b>')
      translation = "<b>Translation:</b><br>"
      translation += self.translate(stem)
      meaning = self.meaning(stem)
      sound_name = stem + '.mp3'
      self.text_to_speech_file(stem, "sounds/" + sound_name)
      ipa = '->   /' + Ipa.convert(stem) + '/' 
      self.add_note_to_anki(stem, sound_name, translation, usage, ipa, meaning)
      printProgressBar(i + 1, l, prefix = 'Progress:', suffix = 'Complete', length = 50)
      i+=1

anki = KindleToAnki()
  
anki.get_data_from_database(path = "./vocab.db")
# anki.get_data_from_database()
anki.create_deck_anki()
anki.generate_note()
anki.export_deck()
print("Added ", len(anki.word_dict.keys())," new words !")
print("Job done, thank you for using our service")


