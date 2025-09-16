 # Save this as odin_backend.py

import pandas as pd
import io
import random
import json
from datetime import datetime, timedelta

# --- Data Processing Layer Functions ---

def parse_tle_line(line1, line2):
    try:
        inclination = float(line2[8:16])
        raan = float(line2[17:25])
        eccentricity = float("." + line2[26:33])
        arg_perigee = float(line2[34:42])
        mean_anomaly = float(line2[43:51])
        mean_motion = float(line2[52:63])
        rev_number = int(line2[63:68])
    except (ValueError, IndexError):
        return None
    return {
        "inclination": inclination,
        "raan": raan,
        "eccentricity": eccentricity,
        "arg_perigee": arg_perigee,
        "mean_anomaly": mean_anomaly,
        "mean_motion": mean_motion,
        "rev_number": rev_number
    }

def calculate_safety_score(kp_index):
    return 1.0 - (kp_index / 10.0)

def run_data_processing():
    print("Starting data processing...")
    
    raw_tle_data = """sat_name,norad_cat_id,epoch,,,,,tle_line1,tle_line2,raw_json
2025-09-16T12:00:00,ODIN-1,99999,,,,,1 99999U 16123A   25259.50000000  .00000100  00000+0  10000-4 0  9999,2 99999  51.6433 133.4567 0002111 204.5678 304.5678 15.441234567890,{}
2025-09-16T12:01:00,ODIN-2,99998,,,,,1 99998U 16124B   25259.50000000  .00000100  00000+0  10000-4 0  9998,2 99998  65.1234 185.1234 0005555 123.9876 234.9876 16.123456789012,{}
"""
    df_raw_tle = pd.read_csv(io.StringIO(raw_tle_data), header=None, skiprows=1)
    df_raw_tle.columns = ['epoch', 'sat_name', 'norad_cat_id', 'col_1', 'col_2', 'col_3', 'col_4', 'tle_line1', 'tle_line2', 'raw_json']

    swpc_data = """datetime,kp_index,solar_flare_class,cme_speed
2012-01-01T00:00:00,2.33,M1.5,500
2012-01-01T01:00:00,4.67,C3.2,700
2012-01-01T02:00:00,1.23,C1.2,400
2012-01-01T03:00:00,7.12,X1.1,1000
"""
    df_swpc = pd.read_csv(io.StringIO(swpc_data))
    df_swpc['datetime'] = pd.to_datetime(df_swpc['datetime'])
    
    processed_data = []
    for index, row in df_raw_tle.iterrows():
        parsed_elements = parse_tle_line(row['tle_line1'], row['tle_line2'])
        if parsed_elements is None:
            continue
        
        current_datetime = pd.to_datetime(row['epoch'])
        matching_swpc_data = df_swpc[df_swpc['datetime'] == current_datetime]
        
        if not matching_swpc_data.empty:
            kp_index = matching_swpc_data['kp_index'].iloc[0]
            safety_score = calculate_safety_score(kp_index)
        else:
            safety_score = 1.0
        
        processed_data.append({
            "sat_name": row['sat_name'],
            "norad_cat_id": row['norad_cat_id'],
            "epoch": row['epoch'],
            **parsed_elements,
            "safety_score": safety_score
        })

    df_processed = pd.DataFrame(processed_data)
    df_processed.to_csv("processed_data.csv", index=False)
    
    hazards = generate_random_hazards_data()
    
    return {
        "processed_data_csv": df_processed,
        "hazards": hazards
    }

# --- Decision Intelligence Layer Functions ---

def generate_random_hazards_data():
    hazards = []
    num_hazards = random.randint(2, 5)
    for i in range(num_hazards):
        x = random.uniform(50000, 300000)
        y = random.uniform(-100000, 100000)
        z = random.uniform(-100000, 100000)
        
        kp_index = round(random.uniform(0.0, 9.0), 2)
        
        hazards.append({
            "id": f"hazard_{i+1}",
            "type": random.choice(["solar_flare", "geomagnetic_storm", "orbital_debris"]),
            "severity": random.choice(["low", "medium", "high"]),
            "position": {"x": x, "y": y, "z": z},
            "kp_index": kp_index
        })
    return hazards

def generate_alternate_trajectory(hazards):
    path_coordinates = []
    num_points = 20
    
    hazard_y_sum = sum(h['position']['y'] for h in hazards)
    hazard_z_sum = sum(h['position']['z'] for h in hazards)
    
    if hazard_y_sum > 0:
        base_y_direction = -1
    else:
        base_y_direction = 1
        
    if hazard_z_sum > 0:
        base_z_direction = -1
    else:
        base_z_direction = 1

    for i in range(num_points):
        x = i * (384400 / num_points)
        y = base_y_direction * random.uniform(50000, 150000)
        z = base_z_direction * random.uniform(50000, 150000)
        path_coordinates.append({"x": x, "y": y, "z": z})
        
    alt_trajectories = []
    alt_trajectories.append({
        "id": "alt_traj_1",
        "delta_v_cost": round(random.uniform(0.1, 0.4), 2),
        "time_increase_hours": round(random.uniform(2.0, 5.0), 2),
        "safety_score": round(random.uniform(0.8, 1.0), 2),
        "justification": "Avoided hazards with a maneuver.",
        "path_coordinates": path_coordinates
    })
    return alt_trajectories

def select_best_trajectory(trajectories):
    return sorted(trajectories, key=lambda x: (x['safety_score'], -x['delta_v_cost']), reverse=True)[0]

def run_decision_engine(processed_data):
    print("\nReading processed hazard and maneuver data...")
    df = processed_data['processed_data_csv']
    hazards = processed_data['hazards']

    print(f"\nDetecting {len(hazards)} hazards and generating alternate trajectories...")
    alternate_paths = generate_alternate_trajectory(hazards)
    
    print("\nEvaluating trade-offs and selecting the best path...")
    best_path = select_best_trajectory(alternate_paths)
    
    decision_log = {
        "status": "reroute_required",
        "original_path_params": df.iloc[0].to_dict(),
        "hazards": hazards,
        "chosen_trajectory": best_path
    }
    
    with open('decision_log.json', 'w') as f:
        json.dump(decision_log, f, indent=4)
    
    print("\nDecision log created successfully!")
    print(f"Chosen Trajectory ID: {best_path['id']}")
    
    return decision_log

# --- Mission Control Layer Functions ---

def run_mission_control(decision_log):
    print("Reading decision log from internal memory...")
    
    chosen_traj = decision_log['chosen_trajectory']
    
    print("\nDecision received. Preparing command sequence...")
    
    print("\n----- Human-Readable Explanation -----")
    num_hazards = len(decision_log['hazards'])
    print(f"Detected {num_hazards} total hazards, including:")
    for hazard in decision_log['hazards']:
        print(f" - {hazard['type']} ({hazard['severity']}) at coordinates ({hazard['position']['x']:.2f}, {hazard['position']['y']:.2f}, {hazard['position']['z']:.2f})")
    
    print(f"Reroute initiated. The selected path ({chosen_traj['id']}) provides the highest safety score.")
    print(f"This maneuver will require an additional {chosen_traj['delta_v_cost']} km/s of fuel and increase mission time by {chosen_traj['time_increase_hours']} hours.")
    print("--------------------------------------")
    
    print("\nGenerating simulated command sequence...")
    print(">>> THRUSTER_FIRE_SEQUENCE_INITIATE(x, y, z)")
    print(">>> ADJUST_HEADING(5.2, 1.8, -3.4)")
    print(">>> NAV_SYSTEM_UPDATE_PATH(new_trajectory_params)")
    print(">>> MISSION_CONTROL_LOG_UPDATE(reroute_executed)")
    print("\nCommand sequence prepared for uplink.")

# --- Master Pipeline Function ---

def run_full_pipeline():
    processed_data = run_data_processing()
    decision_log = run_decision_engine(processed_data)
    run_mission_control(decision_log)
    
    return decision_log

if __name__ == "__main__":
    run_full_pipeline()



