import gt7helper


class Lap:
    def __init__(self):
        # Nice title for lap
        self.title = ""
        # Number of all lap ticks
        self.lap_ticks = 1
        # Lap time after crossing the finish line
        self.lap_finish_time = 0
        # Live time during a live lap
        self.lap_live_time = 0
        self.number = 0
        # Aggregated number of instances where condition is true
        self.throttle_and_brake_ticks = 0
        self.no_throttle_and_no_brake_ticks = 0
        self.full_brake_ticks = 0
        self.full_throttle_ticks = 0
        self.tires_overheated_ticks = 0
        self.tires_spinning_ticks = 0
        # Data points with value for every tick
        self.data_throttle = []
        self.data_braking = []
        self.data_coasting = []
        self.data_speed = []
        self.data_time = []
        self.data_rpm = []
        self.data_tires = []
        # Positions on x,y,z
        self.data_position_x = []
        self.data_position_y = []
        self.data_position_z = []
        # Fuel
        self.fuel_at_start = 0
        self.fuel_at_end = -1
        self.fuel_consumed = -1
        # Car
        self.car_id = 0

    def __str__(self):
        return "\n %s, %2d, %1.f, %4d, %4d, %4d" % (
            self.title,
            self.number,
            self.fuel_at_end,
            self.full_throttle_ticks,
            self.full_brake_ticks,
            self.no_throttle_and_no_brake_ticks,
        )

    def format(self):
        return "Lap %2d, %s (%d Ticks)" % (
            self.number,
            self.title,
            len(self.data_speed),
        )

    def get_speed_peaks_and_valleys(self):
        (
            peak_speed_data_x,
            peak_speed_data_y,
            valley_speed_data_x,
            valley_speed_data_y,
        ) = gt7helper.get_speed_peaks_and_valleys(self)

        return (
            peak_speed_data_x,
            peak_speed_data_y,
            valley_speed_data_x,
            valley_speed_data_y,
        )

    def car_name(self):
        gt7helper.get_car_name_for_car_id(self.car_id)
