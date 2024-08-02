import pytest
import sys
import os
from gt7dashboard.gt7communication import GTData
from divide_laps_logic import divide_laps


# def test_divide_laps():
#     old_data = GTData(None)
#     new_data = GTData(None)

#     # 0/0 -> 1/0
#     old_data.current_lap = 0
#     old_data.total_laps = 0
#     new_data.current_lap = 1
#     new_data.total_laps = 0
#     assert divide_laps(old_data, new_data) == True
    
#     # 0/0 -> 1/1
#     old_data.current_lap = 0
#     old_data.total_laps = 0
#     new_data.current_lap = 1
#     new_data.total_laps = 1
#     assert divide_laps(old_data, new_data) == True
    
#     # 0/0 -> 0/1
#     old_data.current_lap = 0
#     old_data.total_laps = 0
#     new_data.current_lap = 0
#     new_data.total_laps = 1
#     assert divide_laps(old_data, new_data) == True
    
#     # 1/1 -> 2/1
#     old_data.current_lap = 1
#     old_data.total_laps = 1
#     new_data.current_lap = 2
#     new_data.total_laps = 1
#     assert divide_laps(old_data, new_data) == True
    
#     # 1/1 -> 1/2
#     old_data.current_lap = 1
#     old_data.total_laps = 1
#     new_data.current_lap = 1
#     new_data.total_laps = 2
#     assert divide_laps(old_data, new_data) == True
    
#     # 1/1 -> 2/2
#     old_data.current_lap = 1
#     old_data.total_laps = 1
#     new_data.current_lap = 2
#     new_data.total_laps = 2
#     assert divide_laps(old_data, new_data) == True
    
#     # 2/2 -> 3/2
#     old_data.current_lap = 2
#     old_data.total_laps = 2
#     new_data.current_lap = 3
#     new_data.total_laps = 2
#     assert divide_laps(old_data, new_data) == True
    
#     # -1/0 -> 0/0
#     old_data.current_lap = -1
#     old_data.total_laps = 0
#     new_data.current_lap = 0
#     new_data.total_laps = 0
#     assert divide_laps(old_data, new_data) == True

#     # 1/1 -> 1/1
#     old_data.current_lap = 1
#     old_data.total_laps = 1
#     new_data.current_lap = 1
#     new_data.total_laps = 1
#     assert divide_laps(old_data, new_data) == False


#     # 0/0 -> 0/0
#     old_data.current_lap = 0
#     old_data.total_laps = 0
#     new_data.current_lap = 0
#     new_data.total_laps = 0
#     assert divide_laps(old_data, new_data) == False

