import pandas as pd
import streamlit as st
import requests.auth
from datetime import datetime, timedelta
import pytz
from dotenv import dotenv_values
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import plotly.graph_objects as go

IST = pytz.timezone('Asia/Kolkata')
today_ist = datetime.now(IST)
date_in_string = today_ist.strftime("%d-%m-%Y")
time_in_string = today_ist.strftime("%X")

# Header
st.write(
    '<h1>Fitness Habit Tracker '
    '<img src="https://em-content.zobj.net/source/apple/354/beaming-face-with-smiling-eyes_1f601.png">'
    '</h1>', today_ist.strftime(" %H:%M, %d-%m-%Y"), '✨🌥️<br>', today_ist.strftime("%A"),
    unsafe_allow_html=True
)

# Google Sheet Setup
config = {
    **dotenv_values(".env.secret")
}

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CREDS = ServiceAccountCredentials.from_json_keyfile_name(
    filename="Credentials.json",
    scopes=SCOPE
)

client = gspread.authorize(CREDS)

sheets_workout_tracker = client.open("My_Workouts").worksheet("workouts")
sheets_nutrition_tracker = client.open("My_Workouts").worksheet("nutrition")

# API Setup
NUTRITIONIX_EXERCISE_ENDPOINT = "https://trackapi.nutritionix.com/v2/natural/exercise"
NUTRITIONIX_NUTRITION_ENDPOINT = "https://trackapi.nutritionix.com/v2/natural/nutrients"

X_API_ID = config["API_ID"]
X_APP_KEY = config["APP_KEY"]

user_tab1, user_tab2 = st.tabs(['Workouts', 'Nutrition'])

with user_tab1:
    # workout inputs for streamlit
    st.write(
        '<h4>Workout Tracker 📝</h4><br>', unsafe_allow_html=True
    )
    workout_user = st.text_input(
        label="Tell about Your activity (Workout data)",
        placeholder="Enter here"
    )

    col1, col2, col3 = st.columns(3)

    current_weight = col1.number_input(
        label="Current Weight",
        min_value=30,
        max_value=150,
        value=70,
        step=1
    )

    current_height = col3.number_input(
        label="Current Height",
        min_value=30,
        max_value=300,
        value=180,
        step=1
    )

    current_age = col2.number_input(
        label="Current Age",
        min_value=10,
        max_value=100,
        value=22,
        step=1
    )


    def calc_bmi(weight_kg, height_cm):
        """
        Formula: BMI = weight / (height^2)
        """
        height_m = height_cm / 100
        bmi = weight_kg / (height_m ** 2)
        if bmi < 18.5:
            return "Underweight"
        elif 18.5 <= bmi < 25:
            return "Normal weight"
        elif 25 <= bmi < 30:
            return "Overweight"
        else:
            return "Obese"


    get_bmi = calc_bmi(weight_kg=current_weight, height_cm=current_height)
    st.write('BMI :', get_bmi)

    workout_button = st.button(
        "Load Data",
        type="primary",
        key=1
    )

    if workout_button:

        nutrionix_params = {
            "query": workout_user,
            "gender": "male",
            "weight_kg": current_weight,
            "height_cm": current_height,
            "age": current_age
        }

        nutrionix_headers = {
            "x-app-id": X_API_ID,
            "x-app-key": X_APP_KEY
        }

        response_with_exercise_nutritionix = requests.post(
            NUTRITIONIX_EXERCISE_ENDPOINT,
            json=nutrionix_params,
            headers=nutrionix_headers
        )

        result = response_with_exercise_nutritionix.json()

        for workouts in result["exercises"]:
            working_time = str(workouts["duration_min"])

            sheets_data = {
                "Date": date_in_string,
                "Time": time_in_string,
                "Exercise": workouts["name"].title(),
                "Duration (min)": working_time,
                "Calories": workouts["nf_calories"]
            }

            sheets_workout_tracker.append_row(
                [
                    sheets_data["Date"],
                    sheets_data["Time"],
                    sheets_data["Exercise"],
                    sheets_data["Duration (min)"],
                    sheets_data["Calories"],

                ]
            )

        st.write(f"Your activity💪🏽 :  {result['exercises'][0]['name']}")
        st.write(f"\nTotal calories Burned out❤️‍🔥🔥 : {result['exercises'][0]['nf_calories']}")
        st.write(f"\nData is added in your Gsheet successfully✅")

with user_tab2:
    # nutrition input
    st.write(
        '<h4>Nutrition Tracker 📝</h4><br>', unsafe_allow_html=True
    )

    user_trail_nutrition = st.text_input(
        label="Check Your Nutrition item",
        placeholder="Enter here"
    )

    user_nutrition = st.text_input(
        label="Tell about Your Nutrition (Nutrition data)",
        placeholder="Enter here"
    )

    nutrition_button = st.button(
        "Load Data",
        key=2
    )


    def nutritionix_result(user):
        nutrionix_nutrition_params = {
            "query": user
        }

        nutrionix_nutrition_headers = {
            "x-app-id": X_API_ID,
            "x-app-key": X_APP_KEY
        }

        response_with_exercise_nutritionix = requests.post(
            NUTRITIONIX_NUTRITION_ENDPOINT,
            json=nutrionix_nutrition_params,
            headers=nutrionix_nutrition_headers
        )

        nutritionix = response_with_exercise_nutritionix.json()
        return nutritionix


    # Nutrition Request
    if nutrition_button:
        if user_nutrition:
            result_nutrition = nutritionix_result(user=user_nutrition)
            for nutrition in result_nutrition["foods"]:
                weight_grams = str(nutrition["serving_weight_grams"])

                sheets_data = {
                    "Date": date_in_string,
                    "Time": time_in_string,
                    "Food": nutrition["food_name"].title(),
                    "Quantity (grams)": weight_grams,
                    "Calories": nutrition["nf_calories"],
                    "Proteins (grams)": nutrition["nf_protein"]
                }

                sheets_nutrition_tracker.append_row(
                    [
                        sheets_data["Date"],
                        sheets_data["Time"],
                        sheets_data["Food"],
                        sheets_data["Quantity (grams)"],
                        sheets_data["Calories"],
                        sheets_data["Proteins (grams)"]

                    ]
                )

            st.write(f"Your foods😋 :  {result_nutrition['foods'][0]['food_name']}")
            st.write(f"\nTotal calories ❤️‍🔥🔥 : {result_nutrition['foods'][0]['nf_calories']}")
            st.write(f"\nTotal Protien ❤️‍🔥🔥 : {result_nutrition['foods'][0]['nf_protein']}")
            st.write(f"\nData is added in your Gsheet successfully✅")

        elif user_trail_nutrition:
            result_nutrition = nutritionix_result(user=user_trail_nutrition)
            nutri_data ={
                    'food_name': result_nutrition['foods'][0]['food_name'],
                    'brand_name': result_nutrition['foods'][0]['brand_name'],
                    'serving_qty': result_nutrition['foods'][0]['serving_qty'],
                    'serving_unit': result_nutrition['foods'][0]['serving_unit'],
                    'serving_weight_grams': result_nutrition['foods'][0]['serving_weight_grams'],
                    'nf_calories': result_nutrition['foods'][0]['nf_calories'],
                    'nf_total_fat': result_nutrition['foods'][0]['nf_total_fat'],
                    'nf_saturated_fat': result_nutrition['foods'][0]['nf_saturated_fat'],
                    'nf_cholesterol': result_nutrition['foods'][0]['nf_cholesterol'],
                    'nf_sodium': result_nutrition['foods'][0]['nf_sodium'],
                    'nf_total_carbohydrate': result_nutrition['foods'][0]['nf_total_carbohydrate'],
                    'nf_dietary_fiber': result_nutrition['foods'][0]['nf_dietary_fiber'],
                    'nf_sugars': result_nutrition['foods'][0]['nf_sugars'],
                    'nf_protein': result_nutrition['foods'][0]['nf_protein'],
                    'nf_potassium': result_nutrition['foods'][0]['nf_potassium'],
                    'nf_p': result_nutrition['foods'][0]['nf_p']
                }

            st.write(f"\nYour Total {result_nutrition['foods'][0]['food_name']} Nutrition ❤️‍🔥🔥 : {nutri_data}")
            # print('hi')

# Creating DataFrame
workout_data = sheets_workout_tracker.get()
nutrition_data = sheets_nutrition_tracker.get()

df_workout = pd.DataFrame(data=workout_data[1:], columns=workout_data[0])
df_nutrition = pd.DataFrame(data=nutrition_data[1:], columns=nutrition_data[0])

# Type Caste
df_workout['Date'] = pd.to_datetime(df_workout['Date'], format='%d-%m-%Y', errors='ignore')
df_workout['Time'] = pd.to_datetime(df_workout['Time'], format='%H:%M:%S', errors='ignore')
df_workout['Duration (min)'] = pd.to_numeric(df_workout['Duration (min)'], errors='ignore')
df_workout['Calories'] = pd.to_numeric(df_workout['Calories'], errors='ignore')

df_nutrition['Date'] = pd.to_datetime(df_nutrition['Date'], format='%d-%m-%Y', errors='ignore')
df_nutrition['Time'] = pd.to_datetime(df_nutrition['Time'], format='%H:%M:%S', errors='ignore')
df_nutrition['Quantity (grams)'] = pd.to_numeric(df_nutrition['Quantity (grams)'], errors='ignore')
df_nutrition['Calories'] = pd.to_numeric(df_nutrition['Calories'], errors='ignore')
df_nutrition['Proteins (grams)'] = pd.to_numeric(df_nutrition['Proteins (grams)'], errors='ignore')

st.write(
    '<hr><h4>Data Bases 📅</h4><br>', unsafe_allow_html=True
)
tab1, tab2 = st.tabs(["Workout Data", "Nutrition Data"])
with tab1:
    st.dataframe(df_workout, width=1000)
with tab2:
    st.dataframe(df_nutrition, width=1000)

st.write(
    '<hr><h4>Visualizations 📈📊</h4><br>', unsafe_allow_html=True
)
column1, column2 = st.columns(2)
low_targ_cal = column1.number_input(
    label="Low Range Calories",
    min_value=30,
    max_value=10000,
    value=1500,
    step=100
)

high_targ_cal = column2.number_input(
    label="High Range Target Calories",
    min_value=30,
    max_value=10000,
    value=2000,
    step=100
)

# Get the current date
current_date = datetime.now()

# Subtract 7 days from the current date
seven_days_ago = current_date - timedelta(days=7)


def date_slider_func(ukey):
    first_year = int(df_workout['Date'].dt.year[0])
    first_date = int(df_workout['Date'].dt.day[0])
    first_month = int(df_workout['Date'].dt.month[0])

    start_time = st.slider(
        "Date Range",
        min_value=datetime(day=first_date, month=first_month, year=first_year),
        max_value=datetime(day=current_date.day, month=current_date.month, year=current_date.year),
        value=(datetime(day=seven_days_ago.day, month=seven_days_ago.month, year=seven_days_ago.year),
               datetime(day=current_date.day, month=current_date.month, year=current_date.year)),
        format="DD-MM-Y",
        key=ukey
    )
    return start_time


tab1, tab2, tab3, tab4, tab5 = st.tabs(['Calories Burned vs Intake',
                                        'Calories and Activities',
                                        'Protein & Calories',
                                        'Food Calories',
                                        'Food Proteins',
                                        ]
                                       )
with tab1:
    slider = date_slider_func(ukey=6)
    nutri_df = df_nutrition[(df_nutrition['Date'] <= slider[1]) & (df_nutrition['Date'] >= slider[0])]
    cals_df = df_workout[(df_workout['Date'] <= slider[1]) & (df_workout['Date'] >= slider[0])]

    grp_cals_burn_df = cals_df.groupby(['Date'], as_index=False).agg({'Calories': pd.Series.sum})
    grp_intk_work_cal = nutri_df.groupby(['Date'], as_index=False).agg({'Calories': pd.Series.sum})
    merged_df = pd.merge(grp_cals_burn_df, grp_intk_work_cal, on='Date', how='inner')
    merged_df = merged_df.rename(columns={'Calories_x': 'Calories Burned Out', 'Calories_y': 'Calories Intake'})

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=merged_df.Date,
        y=merged_df['Calories Burned Out'],
        mode='lines',
        name='Calories Burned Out',
        line=dict(color='Orange', width=3),
        yaxis='y'  # Use primary y-axis
    ))

    fig.add_trace(go.Scatter(
        x=merged_df.Date,
        y=merged_df['Calories Intake'],
        mode='lines',
        name='Calories Intake',
        line=dict(color='red', width=3),
        yaxis='y2'
    ))

    # Update layout
    fig.update_layout(
        title='Calories BurnsOut vs Intake',
        xaxis=dict(
            title='Dates',
            tickfont=dict(size=14),
            tickangle=45
        ),
        yaxis=dict(
            title='Calories Burned Out',
            titlefont=dict(color='orange', size=16),
            tickfont=dict(size=14),
        ),
        yaxis2=dict(
            title='Calories Intake',
            titlefont=dict(color='red', size=16),
            tickfont=dict(size=14),
            overlaying='y',
            side='right',

        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        width=1000,
        height=500
        # margin=dict(l=50, r=50, t=80, b=50)  # Adjust margins for better visibility
    )
    fig.add_hrect(y0=low_targ_cal, y1=high_targ_cal, line_width=0, fillcolor="green", opacity=0.2)
    st.plotly_chart(fig)

with tab2:
    slider = date_slider_func(ukey=7)
    # nutri_df = df_nutrition[(df_nutrition['Date'] <= slider[1]) & (df_nutrition['Date'] >= slider[0])]
    cals_df = df_workout[(df_workout['Date'] <= slider[1]) & (df_workout['Date'] >= slider[0])]
    cals_act_scatter = px.bar(
        data_frame=cals_df,
        x='Date',
        y='Calories',
        color='Exercise',
        title='Calories and Activity',
        width=1000,
        height=500

    )
    cals_act_scatter.add_hrect(y0=low_targ_cal, y1=high_targ_cal, line_width=0, fillcolor="green", opacity=0.2)
    st.plotly_chart(cals_act_scatter)

with tab3:
    slider = date_slider_func(ukey=8)
    slider_range = df_nutrition[(df_nutrition['Date'] <= slider[1]) & (df_nutrition['Date'] >= slider[0])]
    cal_prot_df = slider_range.groupby(['Date'], as_index=False).agg({'Calories': pd.Series.sum,
                                                                      'Proteins (grams)': pd.Series.sum})
    # Create figure
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=cal_prot_df.Date,
        y=cal_prot_df.Calories,
        mode='lines',
        name='Calories',
        line=dict(color='Orange', width=3),
        yaxis='y'  # Use primary y-axis
    ))

    fig.add_trace(go.Scatter(
        x=cal_prot_df.Date,
        y=cal_prot_df['Proteins (grams)'],
        mode='lines',
        name='Proteins',
        line=dict(color='red', width=3),
        yaxis='y2'
    ))

    # Update layout
    fig.update_layout(
        title='Calories vs Protein',
        xaxis=dict(
            title='Dates',
            tickfont=dict(size=14),
            tickangle=45
        ),
        yaxis=dict(
            title='Calories',
            titlefont=dict(color='orange', size=16),
            tickfont=dict(size=14),
        ),
        yaxis2=dict(
            title='Proteins (grams)',
            titlefont=dict(color='red', size=16),
            tickfont=dict(size=14),
            overlaying='y',
            side='right',

        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        width=1000,
        height=500
        # margin=dict(l=50, r=50, t=80, b=50)  # Adjust margins for better visibility
    )

    fig.add_hrect(y0=low_targ_cal, y1=high_targ_cal, line_width=0, fillcolor="green", opacity=0.2)
    st.plotly_chart(fig)

with tab4:
    slider = date_slider_func(ukey=9)
    slider_range = df_nutrition[(df_nutrition['Date'] <= slider[1]) & (df_nutrition['Date'] >= slider[0])]
    cal_prot_df = slider_range.groupby(['Date', 'Food'], as_index=False).agg({'Calories': pd.Series.sum,
                                                                              'Proteins (grams)': pd.Series.sum})
    stack_cals = px.bar(
        data_frame=cal_prot_df,
        x=cal_prot_df.Date,
        y=cal_prot_df.Calories,
        color='Food',
        orientation='v',
        title='Food Calories Intake'
    )

    stack_cals.update_layout(
        xaxis_title='Dates',
        yaxis_title='Calories',
        width=1000,
        height=500
    )
    stack_cals.add_hrect(y0=low_targ_cal, y1=high_targ_cal, line_width=0, fillcolor="green", opacity=0.2)
    st.plotly_chart(stack_cals)

with tab5:
    slider = date_slider_func(ukey=10)
    slider_range = df_nutrition[(df_nutrition['Date'] <= slider[1]) & (df_nutrition['Date'] >= slider[0])]
    cal_prot_df = slider_range.groupby(['Date', 'Food'], as_index=False).agg({'Calories': pd.Series.sum,
                                                                              'Proteins (grams)': pd.Series.sum})
    stack_prot = px.bar(
        data_frame=cal_prot_df,
        x='Date',
        y='Proteins (grams)',
        color='Food',
        orientation='v',
        title='Food Proteins Intake',
        width=1000,
        height=500
    )

    stack_prot.add_hline(current_weight*2,line_width=3, line_dash="dash", line_color="green")

    st.plotly_chart(stack_prot)
