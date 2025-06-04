import streamlit as st
import joblib
import re
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

ps = PorterStemmer()
stop_words = set(stopwords.words('english'))



def preprocess(text):
    text = text.lower()
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'\W', ' ', text)
    text = re.sub(r'\w*\d\w*', '', text)
    text = re.sub(r'\n+', ' ', text)
    text = text.split()
    text=[ps.stem(word) for word in text if word not in stop_words]
    text = ' '.join(text)

    return text




vectorizer = joblib.load('data/vectorizer.joblib')
model = joblib.load('data/model.joblib')


st.title("Fake News Detector")

news = st.text_area("Enter the news text below:")


if st.button("Predict"):
    if news.strip():
        processed_news = preprocess(news)
        transform_input = vectorizer.transform([processed_news])
        prediction = model.predict(transform_input)

        if prediction[0] == 1:
            st.success("Real News")
        else:
            st.error("Fake News")
    else:
        st.warning("Please enter some news text.")


