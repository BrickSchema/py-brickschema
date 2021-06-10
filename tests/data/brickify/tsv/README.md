# TSV

Converts the following data to a brick model:

|VAV name|temperature sensor|temperature setpoint|has_reheat|
|--------|------------------|--------------------|----------|
|A       | A_ts             | A_sp               | false    |
|B       | B_ts             | B_sp               | true     |


```sh
brickify sheet.tsv --output bldg.ttl --input-type tsv --config template.yml
```

**OR**

```sh
brickify sheet.tsv --output bldg.ttl --input-type tsv --config template.json
```