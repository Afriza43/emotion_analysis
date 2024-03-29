# -*- coding: utf-8 -*-
"""Submission_Dicoding_NLP (2).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1jU9-LDTrBW1KaZQzIR93lDP3zKAt8JAD
"""

!pip install unidecode
!pip install contractions

"""## Import Library dan Dataset"""

import pandas as pd
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import tensorflow as tf
from tensorflow.keras.layers import Bidirectional, Dense, Dropout, LSTM, Embedding
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from nltk.tokenize import RegexpTokenizer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer, WordNetLemmatizer
from string import punctuation
from unidecode import unidecode
from nltk.util import ngrams
from contractions import fix
import nltk


df = pd.read_csv('Emotion_classify_Data.csv')

df

category = pd.get_dummies(df.Emotion)
df_baru = pd.concat([df, category], axis=1)
df_baru = df_baru.drop(columns='Emotion')
df_baru

content = df_baru['Comment'].values
label = df_baru[['fear','anger','joy']].values

"""## Split Data"""

from sklearn.model_selection import train_test_split
content_latih, content_test, label_latih, label_test = train_test_split(content, label, test_size=0.2)

"""## Tokenization"""

nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')

# Fungsi Penghilang Stopwords dan Tanda Baca
def preprocess_text(sentence):
    stop_words = set(stopwords.words('english'))

    tokenizer = RegexpTokenizer(r"\w+")
    word_tokens = tokenizer.tokenize(sentence)

    # Stemming using SnowballStemmer (NLTK) for English
    stemmer = SnowballStemmer("english")
    words = [stemmer.stem(word.lower()) for word in word_tokens if word.lower() not in stop_words]

    return ' '.join(words)

# Fungsi Penghilang Blank, Fixer, dan Proses Ekspansi Teks
def remove_blank(text):
    text_data = text.replace("\n", "").replace("\t", "")
    return text_data

def expanding_text(text):
    text_data = fix(text)  # Pastikan ada fungsi fix atau sesuaikan dengan kebutuhan
    return text_data

# Fungsi untuk menangani karakter aksen
def handle_accented_chr(text):
    text_data = unidecode(text)
    return text_data

# Fungsi Pembersihan Teks
def clean_text(text):
    text_data = text.lower()
    tokens = word_tokenize(text_data)
    clean_data = [i for i in tokens if i not in punctuation]
    clean_data = [i for i in clean_data if i.isalpha()]
    clean_data = [i for i in clean_data if len(i) > 1]
    return clean_data

# Fungsi Lematisasi
def lemmatization(text_list):
    final_list = []
    lemmatizer = WordNetLemmatizer()
    for i in text_list:
        w = lemmatizer.lemmatize(i)
        final_list.append(w)
    return " ".join(final_list)

# Menghilangkan stopwords dan tanda baca dari setiap kalimat dalam dataset
content_latih = [preprocess_text(sentence) for sentence in content_latih]
content_test = [preprocess_text(sentence) for sentence in content_test]

# Menghilangkan blank dari setiap kalimat dalam dataset
content_latih = [remove_blank(sentence) for sentence in content_latih]
content_test = [remove_blank(sentence) for sentence in content_test]

# Proses ekspansi teks
content_latih = [expanding_text(sentence) for sentence in content_latih]
content_test = [expanding_text(sentence) for sentence in content_test]

# Menangani karakter aksen
content_latih = [handle_accented_chr(sentence) for sentence in content_latih]
content_test = [handle_accented_chr(sentence) for sentence in content_test]

# Membersihkan teks
content_latih_cleaned = [clean_text(sentence) for sentence in content_latih]
content_test_cleaned = [clean_text(sentence) for sentence in content_test]

# Lematisasi
content_latih_lemmatized = [lemmatization(sentence) for sentence in content_latih_cleaned]
content_test_lemmatized = [lemmatization(sentence) for sentence in content_test_cleaned]

# Tokenizer
tokenizer = Tokenizer(num_words=40000, oov_token='x')
tokenizer.fit_on_texts(content_latih_lemmatized)

# Tokenize dan pad urutan
sekuens_latih = tokenizer.texts_to_sequences(content_latih_lemmatized)
sekuens_test = tokenizer.texts_to_sequences(content_test_lemmatized)

# Padding
maxlen = 20
padded_latih = pad_sequences(sekuens_latih, padding='post', maxlen=maxlen, truncating='post')
padded_test = pad_sequences(sekuens_test, padding='post', maxlen=maxlen, truncating='post')

"""## Pembuatan Model"""

model = tf.keras.Sequential([
    Embedding(input_dim=40000, output_dim=2048, input_length=20),
    Bidirectional(LSTM(2048, return_sequences=True)),
    Bidirectional(LSTM(1024, return_sequences=True)),
    Bidirectional(LSTM(512, return_sequences=True)),
    Bidirectional(LSTM(256, return_sequences=True)),
    Bidirectional(LSTM(128, return_sequences=True)),
    Bidirectional(LSTM(64)),
    Dense(2048, activation='relu'),
    Dropout(0.1),
    Dense(1024, activation='relu'),
    Dense(512, activation='relu'),
    Dense(256, activation='relu'),
    Dense(128, activation='relu'),
    Dense(64, activation='relu'),
    Dense(3, activation='softmax')
])

model.compile(loss='categorical_crossentropy', optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001), metrics=['accuracy'])

"""## Callback"""

class MyCallback(tf.keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs={}):
        accuracy = logs.get('accuracy')
        val_accuracy = logs.get('val_accuracy')

        if accuracy is not None and val_accuracy is not None:
            if accuracy > 0.9 and val_accuracy > 0.90:
                print("\nAkurasi dan val_akurasi sudah lebih dari 90%!")
                self.model.stop_training = True

early_stopping = EarlyStopping(monitor='val_accuracy', patience=7, restore_best_weights=True)

callbacks = [early_stopping, MyCallback(),ModelCheckpoint('best_model.h5', monitor='val_accuracy', save_best_only=True), ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=3, min_lr=1e-6)]

"""## Pelatihan Model"""

num_epochs = 100
history = model.fit(padded_latih, label_latih, epochs=num_epochs,batch_size = 64,
                    validation_data=(padded_test, label_test), verbose=2, callbacks=callbacks)

model.evaluate(padded_latih, label_latih)

model.evaluate(padded_test, label_test)

"""## Plot Loss Training"""

import matplotlib.pyplot as plt

plt.plot(history.history['loss'])
plt.title('Model loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['Train'], loc='upper right')
plt.show()

"""## Plot Akurasi Training"""

plt.plot(history.history['accuracy'])
plt.title('Model accuracy')
plt.ylabel('Accuracy')
plt.xlabel('Epoch')
plt.legend(['Train'], loc='lower right')
plt.show()

"""## Plot Loss Validation"""

plt.plot(history.history['val_loss'])
plt.title('Model loss')
plt.ylabel('Val Loss')
plt.xlabel('Epoch')
plt.legend(['Test'], loc='upper right')
plt.show()

"""## Plot Akurasi Validation"""

plt.plot(history.history['val_accuracy'])
plt.title('Model accuracy')
plt.ylabel('Val Accuracy')
plt.xlabel('Epoch')
plt.legend(['Test'], loc='lower right')
plt.show()
