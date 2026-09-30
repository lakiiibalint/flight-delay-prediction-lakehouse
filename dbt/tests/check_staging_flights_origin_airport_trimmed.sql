SELECT
    TRIM("Origin_Airport"),
    "Origin_Airport"
FROM {{ref("staging_flights")}}
WHERE TRIM("Origin_Airport") != "Origin_Airport"
