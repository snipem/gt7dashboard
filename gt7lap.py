class Lap:
    def __init__(self):
        self.RemainingFuel = -1
        self.DataTires = []
        self.PositionsX = []
        self.PositionsY = []
        self.PositionsZ = []
        self.Title = ""
        self.LapTicks = 1
        self.LapTime = 0
        self.Number = 0
        self.ThrottleAndBrakesTicks = 0
        self.NoThrottleNoBrakeTicks = 0
        self.FullBrakeTicks = 0
        self.FullThrottleTicks = 0
        self.TiresOverheatedTicks = 0
        self.TiresSpinningTicks = 0
        self.DataThrottle = []
        self.DataBraking = []
        self.DataSpeed = []
        self.FuelAtStart = 0
        self.Magic0x94=[]
        self.Magic0x98=[]
        self.Magic0x9C=[]
        self.Magic0xA0=[]
