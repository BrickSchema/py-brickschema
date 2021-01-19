# This map stores lowercase Haystack tags on the left and maps them to their
# Brick equivalents on the right. Those marked 'todo' will need some future
# work
tagmap = {
    "active": ["real"],  # 'real' == 'active' for power
    "ahu": ["AHU"],
    "apparent": ["power"],  # todo
    "airhandlingequip": ["AHU"],
    "airterminalunit": ["terminal", "unit"],
    "avg": ["average"],
    "atmospheric": ["pressure"],  # todo
    "barometric": ["pressure"],  # todo
    "chillermechanismtype": ["chiller"],  # todo
    "condenserlooptype": ["condenser"],  # todo
    "cmd": ["command"],
    "co": ["CO"],
    "co2": ["CO2"],
    "cooling": ["cool"],
    "coolingcoil": ["cool", "coil", "equip"],
    "coolingonly": ["cool"],
    "coolingtower": ["cool", "tower", "equip"],
    "delta": ["differential"],
    "device": ["equip"],
    "economizing": ["economizer"],
    "elec": ["electrical"],
    "elecheat": ["heat"],
    "equip": ["equipment"],
    "evaporator": ["evaporative"],  # todo
    "fcu": ["FCU"],
    "freq": ["frequency"],
    "fueloil": ["fuel", "oil"],
    "fueloilheating": ["heat"],  # todo
    "fumehood": ["fume", "hood"],
    "heatexchanger": ["heat", "exchanger", "equip"],
    "heatpump": ["heat", "exchanger", "equip"],
    "heatwheel": ["heat", "wheel"],
    "heating": ["heat"],
    "heatingcoil": ["heat", "coil", "equip"],
    "hvac": ["HVAC"],
    "lighting": ["lighting", "equip"],
    "lights": ["lighting"],
    "lightsgroup": ["lighting"],
    "luminous": ["luminance"],  # todo
    "meterscopetype": ["meter", "equip"],
    "mixing": ["mixed"],
    "naturalgas": ["natural", "gas"],
    "occ": ["occupied"],
    "precipitation": ["rain"],
    "rtu": ["RTU"],
    "roof": ["rooftop"],
    "rooftop": ["rooftop"],
    "rotaryscrew": ["compressor"],
    "sitemeter": ["meter", "equip"],
    "sp": ["setpoint"],
    "state": ["status"],
    "steamheating": ["heat"],  # todo
    "submeter": ["meter", "equip"],
    "temp": ["temperature"],
    "unocc": ["unoccupied"],
    "variableairvolume": ["vav"],
    "vav": ["VAV"],
    "volt": ["voltage"],
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
