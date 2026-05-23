import joblib

# Load model and vectorizer
model = joblib.load("model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

print("===== Spam Email Detector =====")

while True:
    msg = input("\nEnter Email/SMS Text: ")

    transformed = vectorizer.transform([msg])

    prediction = model.predict(transformed)[0]

    if prediction == 1:
        print("Result: SPAM")
    else:
        print("Result: NOT SPAM")

    choice = input("\nCheck another message? (y/n): ")

    if choice.lower() != "y":
        break