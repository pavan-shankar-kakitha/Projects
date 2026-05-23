import streamlit as st

st.set_page_config(page_title="Workout Recommender", page_icon="💪")

st.title("💪 Workout Recommender System")
st.write("Enter your details to get a personalized workout recommendation.")

name = st.text_input("Name")
age = st.number_input("Age", min_value=10, max_value=80, value=20)

gender = st.selectbox(
    "Gender",
    ["Male", "Female"]
)

goal = st.selectbox(
    "Fitness Goal",
    [
        "Weight Loss",
        "Muscle Gain",
        "General Fitness"
    ]
)

if st.button("Get Recommendation"):

    st.subheader(f"Hello {name} 👋")

    if goal == "Weight Loss":
        st.success("Recommended Workout Plan")
        st.write("🏃 Running - 30 mins")
        st.write("🚴 Cycling - 20 mins")
        st.write("🤸 Jump Rope - 15 mins")
        st.write("🧘 Stretching - 10 mins")

    elif goal == "Muscle Gain":
        st.success("Recommended Workout Plan")
        st.write("🏋 Push-ups - 4 sets × 15 reps")
        st.write("🏋 Squats - 4 sets × 20 reps")
        st.write("🏋 Dumbbell Training - 30 mins")
        st.write("🏋 Plank - 3 sets × 60 sec")

    else:
        st.success("Recommended Workout Plan")
        st.write("🚶 Walking - 20 mins")
        st.write("🤸 Bodyweight Exercises - 20 mins")
        st.write("🧘 Yoga - 15 mins")
        st.write("🏃 Light Jogging - 15 mins")

    st.info("Remember to stay hydrated and maintain a balanced diet.")