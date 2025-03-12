from datetime import datetime
import PySimpleGUI as sg
import FileHandler
import os
import pandas as pd
import time
import re

timer_running = False
elapsed_secs = 0
total_calories = 0
workout_started = False

def start_layout():
    # Define the layout of the window
    layout = [
        [sg.Text('Choose your workout type:')],
        [sg.Radio('Upper Body', "WORKOUT_TYPE", default=True, key='Upper', enable_events=True),
         sg.Radio('Lower Body', "WORKOUT_TYPE", key='Lower', enable_events=True),
         sg.Radio('Whole Body', "WORKOUT_TYPE", key='Whole', enable_events=True)],
        [sg.Text('Select workout duration:')],
        [sg.Combo([f"{x * 10} minutes" for x in range(1, 13)], default_value='10 minutes', key='Duration')],
        [sg.Text('Choose your program:')],
        [sg.Radio('Strength', "PROGRAM", default=True, key='Strength'),
         sg.Radio('BodyBuilding', "PROGRAM", key='BodyBuilding'), sg.Radio('Hybrid', "PROGRAM", key='Hybrid')],
        [sg.Text('Muscle Groups:')],
        [sg.Checkbox('Arms', key='Arms'), sg.Checkbox('Torso', key='Torso')],
        [sg.Checkbox('Legs', key='Legs'), sg.Checkbox('Posterior', key='Posterior')],
        [sg.Button('Start Workout'), sg.Button('Cancel')]
    ]
    return layout


# Function to update muscle group checkboxes based on the workout type selection
def update_muscle_group_selection(values):

    muscle_groups = ['Arms', 'Torso', 'Legs', 'Posterior']
    upper_body_groups = ['Arms', 'Torso']
    lower_body_groups = ['Legs', 'Posterior']
    whole_body_groups = ['Legs','Posterior','Arms','Torso']
    if values['Upper']:
        for muscle in muscle_groups:
            window[muscle].update(disabled=muscle not in upper_body_groups, value=muscle in upper_body_groups)
    elif values['Lower']:
        for muscle in muscle_groups:
            window[muscle].update(disabled=muscle not in lower_body_groups, value=muscle in lower_body_groups)
    elif values['Whole']:
        for muscle in muscle_groups:
            window[muscle].update(disabled=muscle not in whole_body_groups, value=muscle in whole_body_groups)


def generate_workout_window(workout_plan, duration, num_sets=2):
    # Define the directory where exercise data is stored
    exercise_data_directory = "Exercise Data"

    # Exercise layout list that will be included within the scrollable column

    # Layout for the main workout window
    exercise_layout = []

    # Loop through each exercise in the workout plan
    for exercise in workout_plan:
        # Convert exercise name to filename
        exercise_file = os.path.join(exercise_data_directory, f"{exercise.replace(' ', '_').lower()}.csv")

        # Check if file exists and read the last row
        if os.path.exists(exercise_file):
            df = pd.read_csv(exercise_file)
            last_session = df.iloc[-1]
        else:
            last_session = None  # Handle case where there is no previous data

        exercise_layout.append([sg.Text(f"{exercise}", size=(20, 1))])

        # Add inputs for sets and reps, with adjacent text displaying last session data
        for i in range(num_sets):
            reps_key = f"{exercise}_Reps_Set{i + 1}"
            weight_key = f"{exercise}_Weight_Set{i + 1}"
            previous_reps = last_session[f'{i + 1} Reps'] if last_session is not None else 'N/A'
            previous_weight = last_session[f'{i + 1} Weight'] if last_session is not None else 'N/A'
            calories_key =  f"{exercise}_Calories_Set{i + 1}"

            exercise_layout.extend([
                [sg.Text(f"Set {i + 1}:", size=(5, 1)),
                 sg.Input(size=(10, 1), key=reps_key), sg.Text('Reps', size=(4, 1)),
                 sg.Text(f"Last: {previous_reps}", size=(8, 1), text_color='pink'),
                 sg.Input(size=(10, 1), key=weight_key), sg.Text('lbs', size=(2, 1)),
                 sg.Text(f"Last: {previous_weight} lbs", size=(12, 1), text_color='pink'),
                 sg.Text(f" 0 Cals",key = calories_key, size=(12, 1), text_color='pink')]
            ])

    # Scrollable column that contains the exercise layout
    scrollable_column = sg.Column(exercise_layout, scrollable=True, vertical_scroll_only=True, size=(600, 400))

    # Final layout for the window that includes the scrollable column
    final_layout = [
        [sg.Text('Your Workout Plan', font=("Helvetica", 16))],
        [sg.Text(f"Total Calories Burned: 0 cals", key="-TOTAL_CALS-", text_color='pink')],
        [sg.Text(f"Planned Duration: {duration}", text_color='red', font=('Helvetica', 16))],
        [sg.Text('00:00', size=(10, 1), font=('Helvetica', 24), justification='center', key='-TIMER-')],
        [sg.Button("Start Timer"),sg.Button("Pause Timer")],
        [scrollable_column],
        [sg.Button('Finish Workout')]
    ]

    # Create the window with the final layout
    return final_layout

# Called at end to process data in input fields
def collect_workout_data(values, workout_plan, num_sets):
    workout_data = {}
    for exercise in workout_plan:
        exercise_data = {'Reps': [], 'Weight': []}
        for set_num in range(num_sets):
            reps_key = f"{exercise}_Reps_Set{set_num + 1}"
            weight_key = f"{exercise}_Weight_Set{set_num + 1}"
            reps = values.get(reps_key, None)
            weight = values.get(weight_key, None)

            # Convert empty strings to None
            reps = None if reps == '' else reps
            weight = None if weight == '' else weight

            exercise_data['Reps'].append(reps)
            exercise_data['Weight'].append(weight)

        workout_data[exercise] = exercise_data
    return workout_data

# Update Calories as Input fields are filled out
def update_calories_burned(values, workout_plan, num_sets):
    caloric_data = {}
    global total_calories
    total_calories = 0
    for exercise in workout_plan:
        exercise_data = {'Set': [], 'Calories': []}
        for set_num in range(num_sets):
            reps_key = f"{exercise}_Reps_Set{set_num + 1}"
            weight_key = f"{exercise}_Weight_Set{set_num + 1}"
            reps = values.get(reps_key, None)
            weight = values.get(weight_key, None)

            # Convert empty strings to None
            reps = None if reps == '' else reps
            weight = None if weight == '' else weight

            if (reps is None) or (weight is None):
                weight_moved = 0
                reps = 0
                weight = 0
            else:
                reps = float(remove_non_numeric(reps))
                weight = float(remove_non_numeric(weight))
                weight_moved = reps * weight

            # Determine Calories Burned per set
            caloric_multiplier = 0
            if reps <= 5:
                caloric_multiplier = 0.10
            if reps > 5:
                caloric_multiplier = 0.075
            if reps >= 10:
                caloric_multiplier = 0.05

            calories = int(weight_moved * caloric_multiplier)
            total_calories = total_calories + calories
            cal_key = f"{exercise}_Calories_Set{set_num + 1}"

            window[cal_key].update(f"{calories} Cals")
            window["-TOTAL_CALS-"].update(f"Total Calories Burned: {total_calories} Cals")

        caloric_data[exercise] = exercise_data

    return caloric_data

def remove_non_numeric(text):
    return re.sub(r'[^0-9.]', '', text)  # Keeps only digits and decimal points

# Create the window
window = sg.Window('AI Workout Buddy', start_layout(), finalize=True)
# Initial muscle group selection based on default workout type
update_muscle_group_selection({'Upper': True, 'Lower': False})

# Event Loop
while True:
    event, values = window.read(timeout=100)
    if event == sg.WIN_CLOSED or event == 'Cancel':
        break

    if event in ('Upper', 'Lower','Whole'):
        update_muscle_group_selection(values)

    if event == 'Start Workout':
        workout_started = True
        workout_type = 'Upper Body' if values['Upper'] else 'Lower Body'
        program = 'Strength' if values['Strength'] else 'BodyBuilding' if values['BodyBuilding'] else 'Hybrid'
        duration = values['Duration']
        selected_muscles = [muscle.lower() for muscle in ['Arms', 'Torso', 'Legs', 'Posterior'] if values[muscle]]
        sg.popup(
            f"You've selected a {workout_type} workout, {program} program for {duration}. Muscle groups to target: {', '.join(selected_muscles)}.")
        workout_plan, numSets, equipmentUsed = FileHandler.generate_workout(selected_muscles, int(values['Duration'].split()[0]), FileHandler.exercises_by_equipment)
        print(workout_plan)
        if len(workout_plan)>0:
            window.close()
            wo_layout = generate_workout_window(workout_plan,duration, numSets)
            window = sg.Window('Workout Session', wo_layout, finalize=True, resizable=True,)

        else:
            sg.popup(f"{duration} is not enough time for {",".join(selected_muscles)}. Add more time or choose another muscle-group.")

    if event == 'Start Timer':
        timer_running = True
        # Get the current time and extract the second
        last_time = datetime.now()
        last_second = last_time.second

    elif event == 'Pause Timer':
        timer_running = False
    if event == 'Finish Workout':
        timer_running = False
        weightLifted = 0
        # Collect data from the form
        workout_data_collected = collect_workout_data(values, workout_plan, numSets)
        # Iterate over collected workout data and pass to the update_or_create_exercise_file function
        for exercise, data in workout_data_collected.items():
            exercise_data = {'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

            for i in range(1, numSets+1):  # Assuming 5 sets per exercise
                weight = 0  # Default value
                reps = 0  # Default value

                # Check if the current set's data is available and update accordingly
                if i - 1 < len(data['Weight']):
                    weight = data['Weight'][i - 1] if data['Weight'][i - 1] else 0

                    # Clean up any invalid int/float characters here, in case user enters string
                    try:
                        float(weight)
                    except:
                        weight = 0

                if i - 1 < len(data['Reps']):
                    # Clean up any invalid int/float characters here, in case user enters string
                    try:
                        float(reps)
                    except:
                        reps = 0
                    reps = data['Reps'][i - 1] if data['Reps'][i - 1] else 0
                    weightLifted = weightLifted + int(float(weight))*int(float(reps))

                # Store the data
                exercise_data[f'{i} Weight'] = weight
                exercise_data[f'{i} Reps'] = reps

            # Create individual Exercise File
            FileHandler.update_or_create_exercise_file(exercise, exercise_data,logType=1)
            # Create overall Workout Log File
            workoutData = {}
            workoutData["MuscleGroups"] = selected_muscles
            workoutData["EquipmentUsed"] = equipmentUsed
            workoutData["WeightLifted"] = weightLifted
        FileHandler.update_or_create_exercise_file("WorkoutLog", workoutData, logType=2, duration = duration)
        # Break or continue as needed
        break

    # Update the timer if running
    if timer_running:
        current_time = datetime.now()
        current_second = current_time.second
        if last_second != current_second:
            elapsed_secs = elapsed_secs+1
            last_second = current_second
            window['-TIMER-'].update(f"{int(elapsed_secs // 60):02}:{int(elapsed_secs % 60):02}")

    if workout_started:
        update_calories_burned(values, workout_plan, numSets)




window.close()
for csvFile in FileHandler.csvNamesList:
    FileHandler.drawChart(csvFile,logType=1)

sg.popup("Workout Complete!", f"You burned {total_calories} kcal!", title="Workout Summary")



