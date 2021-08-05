# Kindle-to-Anki
A python script exports vocabulary from Kindle and generates Anki's deck with image, pronunciation and translation 

## Usage
1. Connect kindle by cable
2. Change the path to vocab.db file (Line 160, default : /Volumes/Kindle/system/vocabulary/vocab.db)
3. Change language destination (Line 224, default : vi)
4. pip3 install -r requirements.txt
5. Run python3 export_vocab_kindle.py
6. Import output.apkg to your Anki
