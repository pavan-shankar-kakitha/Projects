import streamlit as st
import joblib

model = joblib.load("model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

st.set_page_config(page_title="Spam Email Detector")

st.title("📧 Spam Email Detector")
st.write("Enter an email or SMS message below and click Predict.")

message = st.text_area("Message")

if st.button("Predict"):
    if message.strip() == "":
        st.warning("Please enter a message.")
    else:
        transformed = vectorizer.transform([message])
        prediction = model.predict(transformed)[0]

        probability = model.predict_proba(transformed)[0]
        confidence = max(probability) * 100

        if prediction == 1:
            st.error("🚨 SPAM Message")
        else:
            st.success("✅ NOT SPAM Message")

        st.write(f"Confidence: {confidence:.2f}%")