import configparser
import random
import os
from datetime import datetime
import pandas as pd
import math
import matplotlib.pyplot as plt
import numpy as np


def load_exercises_from_ini(ini_file):
    config = configparser.ConfigParser()
    config.read(ini_file)

    exercises_by_equipment = {}
    for section in config.sections():
        if section.endswith('.Info') or "." not in section:  # Also skip sections without a dot
            continue
        equipment, muscle_group = section.split('.', 1)
        equipment = equipment.lower()
        muscle_group = muscle_group.lower()
        if equipment not in exercises_by_equipment:
            exercises_by_equipment[equipment] = {}
        exercises_by_equipment[equipment][muscle_group] = {}
        for sub_muscle, ex_list in config[section].items():
            # Convert each item in ex_list to lowercase
            exercises = [exercise.lower() for exercise in ex_list.split(', ')]
            exercises_by_equipment[equipment][muscle_group][sub_muscle] = exercises
    return exercises_by_equipment


def generate_workout(selected_group, duration, exercises_by_equipment):
    muscle_groups = {
        "arms": ["Biceps", "Triceps"],
        "legs": ["Quads", "Hamstrings", "Calves"],
        "torso": ["Pecs", "Lats", "Traps", "Deltoids", "Abs"],
        "posterior": ["Glutes"]
    }
    selected_muscles = []
    print(f"SG {selected_group}")

    for group in selected_group:
        selected_muscles.extend(muscle_groups.get(group, []))

    random.shuffle(selected_muscles)  # Shuffle the selected muscles for variety

    # Determine the ideal number of sets
    setDuration = 2.75
    idealTotalSets = duration // setDuration
    sets_per_muscle = math.ceil(idealTotalSets / len(selected_muscles))  # Sets per muscle

    # Ensure at least 1 set per muscle and max 5 sets per muscle
    sets_per_muscle = max(1, min(sets_per_muscle, 5))
    print(f" 1 SETS PER MUSCLE {sets_per_muscle}")

    # Estimate total duration and adjust if it exceeds the desired duration
    total_estimated_duration = sets_per_muscle * len(selected_muscles) * duration

    print(f" 2 SETS PER MUSCLE {sets_per_muscle}")

    # Choose the equipment
    # Increase the likelihood of selecting dumbbells, kettlebells, and barbells by 60%
    favored_equipment = ['dumbbell', 'kettlebell', 'barbell']
    equipment_choices = list(exercises_by_equipment.keys())

    # Adjust the list by adding favored equipment more times
    adjusted_equipment_choices = equipment_choices + [eq for eq in equipment_choices if eq in favored_equipment] * 2
    random.shuffle(adjusted_equipment_choices)  # Shuffle the adjusted equipment choices for variety

    workout_plan = []
    equipmentUsed = []
    for muscle in selected_muscles:
        exercise_found = False
        for equipment in adjusted_equipment_choices:
            for muscle_group, sub_muscles in exercises_by_equipment[equipment].items():
                if muscle.lower() in [m.lower() for m in sub_muscles]:
                    exercise = random.choice(exercises_by_equipment[equipment][muscle_group][muscle.lower()])
                    workout_plan.append(exercise)  # Store the exercise and its sets
                    exercise_found = True
                    if equipment not in equipmentUsed:
                        equipmentUsed.append(equipment)
                    break
            if exercise_found:
                break
    return workout_plan, sets_per_muscle, equipmentUsed


csvNamesList = []
def update_or_create_exercise_file(logName, logData,logType,duration=0):
    # Define the directory and file path
    directory = "Exercise Data"
    filename = f"{logName.replace(' ', '_')}.csv"
    file_path = os.path.join(directory, filename)

    # Ensure the directory exists
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Prepare the data for the DataFrame
    data = {
        'Timestamp': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
    }
    # 1 - Standard Exercise
    if logType == 1:
        csvNamesList.append(file_path)
        # Creates 5 sets for headers Weight & Reps
        for i in range(1, 6):
            data[f'{i} Weight'] = [logData.get(f'{i} Weight', 0)]
            data[f'{i} Reps'] = [logData.get(f'{i} Reps', 0)]



    #2 - Overall Workout Data Tracked
    elif logType == 2:
        muscle_groups_str = ", ".join(logData.get("MuscleGroups", []))  # Converts list to string
        equipment_used_str = ", ".join(logData.get("EquipmentUsed", []))  # Converts list to string

        data["MuscleGroups"] = muscle_groups_str
        data["EquipmentUsed"] = equipment_used_str
        data["WeightLifted"] = logData.get("WeightLifted", 0)
        data["Duration"] = duration

    # Convert the dictionary to a DataFrame
    df_new_entry = pd.DataFrame(data)


    # If the file exists, load it and append the new data
    if os.path.exists(file_path):
        df_existing = pd.read_csv(file_path)
        df_updated = pd.concat([df_existing, df_new_entry], ignore_index=True)
    else:
        df_updated = df_new_entry

    # Write the updated or new DataFrame to the file
    df_updated.to_csv(file_path, index=False)



def drawChart(filename, logType):

    # Reading the data
    df = pd.read_csv(filename)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], format='%Y-%m-%d %H:%M:%S')

    if logType == 1:
        # Calculate total weight lifted per session (Weight * Reps for all sets)
        df['Total Weight Lifted'] = sum([df[f'{i} Weight'] * df[f'{i} Reps'] for i in range(1, 6)])

        # Convert Timestamps to datetime objects for plotting
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])

        # Set up the plot layout
        fig = plt.figure(figsize=(20, 6))

        # Set the window title
        fig.canvas.manager.set_window_title(f"{filename}")

        # Plot total weight lifted over time
        plt.subplot(1, 3, 1)
        plt.plot(df['Timestamp'], df['Total Weight Lifted'], marker='o')
        plt.title(f'Total Weight Lifted Over Time')
        plt.xlabel('Date')
        plt.ylabel('Total Weight Lifted')
        plt.xticks(rotation=45)

        # Plot individual bar charts for weight in each set
        plt.subplot(1, 3, 2)
        for i in range(1, 6):
            plt.bar(df['Timestamp'] + pd.to_timedelta((i - 3) * 8, unit='h'), df[f'{i} Weight'], width=0.1,
                    label=f'Set {i} Weight')
        plt.title(f'Weight Used in Each Set')
        plt.xlabel('Date')
        plt.ylabel('Weight (kg)')
        plt.legend()
        plt.xticks(rotation=45)

        # Plot individual bar charts for reps in each set
        plt.subplot(1, 3, 3)
        for i in range(1, 6):
            plt.bar(df['Timestamp'] + pd.to_timedelta((i - 3) * 10, unit='h'), df[f'{i} Reps'], width=0.1,
                    label=f'Set {i} Reps', alpha=0.75)
        plt.title(f'Reps Performed in Each Set')
        plt.xlabel('Date')
        plt.ylabel('Reps')
        plt.legend()
        plt.xticks(rotation=45)

        plt.tight_layout()
        plt.show()




# Assuming your INI file is named 'exercise_config.ini'
exercises_by_equipment = load_exercises_from_ini(r'Settings\exercises.ini')
#selected_muscles = ["Legs", "Posterior"]
#workout, sets = generate_workout(selected_muscles, 30, exercises_by_equipment)
#print("Generated Workout:", workout)
#print("Total Sets:", sets)
