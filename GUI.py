from datetime import datetime
import PySimpleGUI as sg
import FileHandler
import threading

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


# Place this function outside the event loop, after the load_exercises_from_ini function
def generate_workout_window(workout_plan, num_sets=2):
    # Exercise layout list that will be included within the scrollable column
    exercise_layout = []

    # Add exercises, sets, and reps inputs to the exercise layout
    for exercise in workout_plan:
        exercise_layout.append([sg.Text(f"{exercise}", size=(20, 1))])
        for i in range(num_sets):
            reps_key = f"{exercise}_Reps_Set{i + 1}"
            weight_key = f"{exercise}_Weight_Set{i + 1}"
            exercise_layout.extend([
                [sg.Text(f"Set {i + 1}:", size=(5, 1)),
                 sg.Input(size=(10, 1), key=reps_key), sg.Text('Reps', size=(4, 1)),
                 sg.Input(size=(10, 1), key=weight_key), sg.Text('lbs', size=(2, 1))]
            ])

    # Scrollable column that contains the exercise layout
    scrollable_column = sg.Column(exercise_layout, scrollable=True, vertical_scroll_only=True, size=(600, 400))

    # Final layout for the window that includes the scrollable column
    final_layout = [
        [sg.Text('Your Workout Plan', font=("Helvetica", 16))],
        [scrollable_column],
        [sg.Button('Finish Workout')]
    ]

    # Create the window with the final layout
    return sg.Window('Workout Session', final_layout, finalize=True, resizable=True)


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


# Create the window
window = sg.Window('AI Workout Buddy', start_layout(), finalize=True)
# Initial muscle group selection based on default workout type
update_muscle_group_selection({'Upper': True, 'Lower': False})

# Event Loop
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Cancel':
        break

    if event in ('Upper', 'Lower','Whole'):
        update_muscle_group_selection(values)

    if event == 'Start Workout':
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
            window = generate_workout_window(workout_plan,numSets)
        else:
            sg.popup(f"{duration} is not enough time for {",".join(selected_muscles)}. Add more time or choose another muscle-group.")

    if event == 'Finish Workout':
        # Collect data from the form
        workout_data_collected = collect_workout_data(values, workout_plan, 3)
        # Iterate over collected workout data and pass to the update_or_create_exercise_file function
        for exercise, data in workout_data_collected.items():
            exercise_data = {'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            weightLifted = 0
            for i in range(1, numSets + 1):
                exercise_data[f'{i} Weight'] = data['Weight'][i - 1] if data['Weight'][i - 1] else 'NaN'
                exercise_data[f'{i} Reps'] = data['Reps'][i - 1] if data['Reps'][i - 1] else 'NaN'
                if data['Weight'][i - 1] and data['Reps'][i - 1]:
                    weightLifted = weightLifted + (int(data['Weight'][i - 1]) * int(data['Reps'][i - 1]))
            # Create individual Exercise File
            FileHandler.update_or_create_exercise_file(exercise, exercise_data,logType=1)
            # Create overall Workout Log File
            workoutData = {}
            workoutData["MuscleGroups"] = selected_muscles
            workoutData["EquipmentUsed"] = equipmentUsed
            workoutData["WeightLifted"] = weightLifted
        FileHandler.update_or_create_exercise_file("WorkoutLog", workoutData, logType=2)
        # Break or continue as needed
        break

window.close()
for csvFile in FileHandler.csvNamesList:
    FileHandler.drawChart(csvFile,logType=1)


