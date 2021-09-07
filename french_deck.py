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
from larousse_api.larousse import Larousse


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

  def text_to_speech_file(self, text, output_file = 'text.mp3', language = 'fr'):
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
        {'name': 'Sound'},
        {'name': 'Translation'},
        {'name': 'Definition'},
        {'name': 'Locution'},
        {'name': 'Synonyme'},
        {'name': 'Citation'},
      ],
      templates=[
        {
          'name': 'Card 1',
          'qfmt': '{{Word}} ',
          'afmt': '{{FrontSide}} <br> <hr id="answer"> {{Translation}} <br> {{Sound}} <br> {{Definition}} <br> {{Locution}} <br> {{Synonyme}} <br> {{Citation}}'
      },
      ])

    self.my_deck = genanki.Deck(
      # 2059400191,
      205940019,
      "French")

    self.my_package = genanki.Package(self.my_deck)
    self.my_package.media_files = []
    # Add note after this line
  
  def add_note_to_anki(self, word, sound_name, translation, definition, locution, synonymes, citation):
    note = genanki.Note(
      model=self.my_model,
      fields=[word, 
        "[sound:{}]".format(sound_name),
        translation,
        definition,
        locution,
        synonymes,
        citation,
        ])
    self.my_deck.add_note(note)
    # add location of img or audio file
    self.my_package.media_files.append('sounds/' + sound_name) 
    print("Added new word successfully : %s | %s | %s " % (word, translation, sound_name))

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
      vi = analysis.translate(from_lang='fr', to=language)
      return str(vi)
    except Exception as E:
      print(E)
      return "error (Not found or Max=~100 words per day)"

  def to_string(self, tup, word):
    ans = ""
    for l in tup :
      if l == tup[len(tup) - 1]: continue
      if l is None : continue
      for s in l:
        if s is None : continue
        s = str(s) + '<br>'
        s = s.replace(word, '<b>' + word + '</b>')
        word_upcase = word[0].upper() + word[1:]
        s = s.replace(word_upcase, '<b>' + word_upcase + '</b>')
        ans +=  s
    return ans

  def generate_note(self):
    i = 0
    # For testing : 
    # self.word_dict = {"book":["pass", "book", "I have a book"], "school": ["pass", "school", "I go to school"]}
    print("'OK' to finish!")
    self.word_dict = []
    new_word = ""
    while (new_word != "OK"):
      new_word = input()
      if new_word != "OK" and new_word != "":
        self.word_dict.append(new_word)
    l = len(self.word_dict)
    for word in self.word_dict:
      look_up = Larousse(word)
      # usage = "<b>Usage:</b> <br>"
      # usage += self.word_dict[word][2]
      # usage = usage.replace(stem, '<b>' + stem + '</b>')
      translation = "<b>Translation:</b><br>"
      translation += self.translate(word)

      # meaning = self.meaning(stem)
      definition = look_up.get_definitions()
      locution = look_up.get_locutions()
      # synonymes = look_up.get_synonymes()
      citation = look_up.get_citations()

      definition = "<b>Definition:</b> <br>" + self.to_string(definition, word)
      locution = "<b>Locution:</b> <br>" + self.to_string(locution, word)
      # synonymes = self.to_string(synonymes)
      synonymes = ""
      citation = "<b>Citation:</b> <br>" + self.to_string(citation, word)
      # print(translation, locution, synonymes, citation, definition)

      sound_name = word + '.mp3'
      self.text_to_speech_file(word, "sounds/" + sound_name)
      # ipa = '->   /' + Ipa.convert(stem) + '/' 
      self.add_note_to_anki(word, sound_name, translation,definition, locution, synonymes, citation)
      printProgressBar(i + 1, l, prefix = 'Progress:', suffix = 'Complete', length = 50)
      i+=1

# init class larousse
# l = Larousse("Fromage")

# Print the array containing all defintions of "Fromage"
# print(l.get_definitions())

# Print the array containing all locution of "Fromage"
# print(l.get_locutions())

# Print the array containing all synonymes of "Fromage"
# print(l.get_synonymes())

# Print the array containing all citations of "Fromage"
# print(l.get_citations())

anki = KindleToAnki()
  
# anki.get_data_from_database(path = "./vocab.db")
# anki.get_data_from_database()
anki.create_deck_anki()
anki.generate_note()
anki.export_deck()
print("Added ", len(anki.word_dict)," new words !")
print("Job done, thank you for using our service")


