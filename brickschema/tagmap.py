# haystack -> brick
# TODO: add 'equip' tag when obvious?
tagmap = {
    "active": "real",  # 'real' == 'active' for power
    "ahu": "ahu",
    "apparent": "power",  # todo
    "airhandlingequip": "ahu",
    "airterminalunit": ["terminal", "unit"],
    "avg": "average",
    "atmospheric": "pressure",  # todo
    "barometric": "pressure",  # todo
    "chillermechanismtype": "chiller",  # todo
    "condenserlooptype": "condenser",  # todo
    "cmd": "command",
    "cooling": "cool",
    "coolingcoil": ["cool", "coil", "equip"],
    "coolingonly": ["cool"],
    "coolingtower": ["cool", "tower", "equip"],
    "delta": "differential",
    "device": "equip",
    "economizing": "economizer",
    "elec": "electrical",
    "elecheat": "heat",
    "equip": "equipment",
    "evaporator": "evaporative",  # todo
    "freq": "frequency",
    "fueloil": ["fuel", "oil"],
    "fueloilheating": "heat",  # todo
    "fumehood": ["fume", "hood"],
    "heatexchanger": ["heat", "exchanger", "equip"],
    "heatpump": ["heat", "exchanger", "equip"],
    "heatwheel": ["heat", "wheel"],
    "heating": "heat",
    "heatingcoil": ["heat", "coil", "equip"],
    "lighting": ["lighting", "equip"],
    "lights": "lighting",
    "luminous": "luminance",  # todo
    "meterscopetype": ["meter", "equip"],
    "mixing": "mixed",
    "naturalgas": ["natural", "gas"],
    "occ": "occupied",
    "precipitation": "rain",
    "temp": "temperature",
    "rtu": "rtu",
    "roof": "rooftop",
    "rotaryscrew": "compressor",
    "sitemeter": ["meter", "equip"],
    "sp": "setpoint",
    "state": "status",
    "steamheating": "heat",  # todo
    "submeter": ["meter", "equip"],
    "temp": "temperature",
    "unocc": "unoccupied",
    "variableairvolume": "vav",
    "volt": "voltage",
}


"""
# get values for:


ahuZoneDeliveryType AHU
airCooling Air
airVolumeAdjustabilityType Air
chilledBeam Chilled
chilledBeamZone Chilled
chilledWaterCooling Chilled
chillerMechanismType Chiller
condenserClosedLoop Condenser
condenserCooling Condenser
condenserLoopType Condenser
condenserOpenLoop Condenser
diverting Direction
"""


"""
TODOs:
airQuality Air
cav CRAC
cloudage Close
co CO2
daytime Damper
doas Domestic
dualDuct Duration
escalator Elevator
flux Fluid
heatPump Heat
imbalance Luminance
intensity Integral
irradiance Radiance
magnitude Manual
mau Makeup
pf PV
phenomenon -> substance
plant
pm10 Pump
pm25 Pump
tvoc Touchpanel
radiantEquip Radiance
radiator Radiance
refrig Reader
substance Suction
thd Head
unitVent Unit
"""

"""
refs

controls Control
"""
