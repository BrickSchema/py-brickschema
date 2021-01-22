# CSV-Jinja2

Converts the following data to a brick model:

|VAV name|temperature sensor|temperature setpoint   |has_reheat              |sensors     |setpoints  |
|--------|------------------|-----------------------|------------------------|------------|-----------|
|A       |          A_ts    |                   A_sp|                   false|          4 |          3|
|B       |          B_ts    |                   B_sp|                   true |           5|          3|

- Creates 4 Temperature_Sensors and 3 Temperature_Setpoints as points to VAV A
- Creates 5 Temperature_Sensors and 3 Temperature_Setpoints as points to RVAV B

```sh
brickify sheet.csv --output bldg.ttl --input-type csv --config template.yml
```

**OR**

```sh
brickify sheet.csv --output bldg.ttl --input-type csv --config template.json
```