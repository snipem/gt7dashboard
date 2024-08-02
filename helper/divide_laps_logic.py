

    # 0/0 - 
    # 0/1 - Antes de começar
    # 1/0 - Menu
    # 1/1 - Correndo

    # Salvar 
    # 1/1 - 0/1
    # 1/1 - 1/0

    # Não salvar
    # 1/0 - 0/1
    # 0/1 - 1/1

from gt7dashboard.gt7helper import load_laps_from_json
from gt7dashboard.gt7lap import Lap
from gt7dashboard.gt7data import GTData

def divide_laps(old_data: GTData, new_data: GTData):
    if old_data.current_lap != new_data.current_lap or old_data.total_laps != new_data.total_laps:
        print(f"new lap = {old_data.current_lap}/{old_data.total_laps} -> {new_data.current_lap}/{new_data.total_laps}")
        return True
    
    if old_data.total_laps == new_data.total_laps and old_data.current_lap == new_data.current_lap:
        return False
    
def should_save_lap(old_data: GTData, new_data: GTData, lap : Lap  ):

    if old_data.current_lap <= 0 :
        print(f"Lap not saved because old_data.current_lap = {old_data.current_lap}")
        return False
    
    if old_data.in_race != 1 and not lap.is_replay:
        print(f"Lap not saved because old_data.in_race = {old_data.in_race} or lap.is_replay = {lap.is_replay}")
        return False

    if lap.lap_live_time < 5:
        print(f"Lap not saved because lap.lap_live_time = {lap.lap_live_time}")
        return False
    
    if len(lap.data_speed) <= 0:
        print(f"Lap not saved because len(lap.data_speed) = {len(lap.data_speed)}")
        return False

    print(f"Lap saved")
    return True

def equalizer_lap(reference_lap: Lap, current_lap:Lap):
    when_to_cut = 0
    start_position = {
        "x": round(reference_lap.data_position_x[0],3),
        "y": round(reference_lap.data_position_y[0],3),
        "z": round(reference_lap.data_position_z[0],3)
    }
    print(f"Start position: {start_position}")
    print(f"Reference data size: {len(reference_lap.data_position_x)} lap_ticks: {reference_lap.lap_ticks} is_replay: {reference_lap.is_replay}")
    print(f"Current data size: {len(current_lap.data_position_x)} lap_ticks: {current_lap.lap_ticks} is_replay: {current_lap.is_replay}")

    # check what lap is shorter
    range_lap = min(len(reference_lap.data_position_x), len(current_lap.data_position_x))

    for i in range(range_lap):

        if round(current_lap.data_position_x[i],3) == start_position["x"]:
            when_to_cut = i
            print(f"Equalizing position x from tick {i} to {current_lap.lap_ticks}")
        if round(current_lap.data_position_y[i],3) == start_position["y"]:
            when_to_cut = i
            print(f"Equalizing position y from tick {i} to {current_lap.lap_ticks}")
        if round(current_lap.data_position_z[i],3) == start_position["z"]: 
            when_to_cut = i
            print(f"Equalizing position z from tick {i} to {current_lap.lap_ticks}")

    print(f"Cutting lap at tick {when_to_cut}")

    current_lap.data_position_x = current_lap.data_position_x[when_to_cut:]
    current_lap.data_position_y = current_lap.data_position_y[when_to_cut:]
    current_lap.data_position_z = current_lap.data_position_z[when_to_cut:]

    current_lap.data_throttle = current_lap.data_throttle[when_to_cut:]
    current_lap.data_braking = current_lap.data_braking[when_to_cut:]
    current_lap.data_coasting = current_lap.data_coasting[when_to_cut:]
    current_lap.data_speed = current_lap.data_speed[when_to_cut:]
    current_lap.data_time = current_lap.data_time[when_to_cut:]
    current_lap.data_rpm = current_lap.data_rpm[when_to_cut:]
    current_lap.data_gear = current_lap.data_gear[when_to_cut:]
    current_lap.data_tires = current_lap.data_tires[when_to_cut:]

    current_lap.data_boost = current_lap.data_boost[when_to_cut:] 
    current_lap.data_rotation_yaw = current_lap.data_rotation_yaw[when_to_cut:]
    current_lap.data_absolute_yaw_rate_per_second = current_lap.data_absolute_yaw_rate_per_second[when_to_cut:]

    return current_lap
     

# laps = load_laps_from_json("data/2024-08-01_10_10_03_GT-R_NISMO_GT3_13.json")
# equalizer_lap(laps[1], laps[0])