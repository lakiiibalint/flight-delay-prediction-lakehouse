SELECT
    TRIM("Destination_Airport"),
    "Destination_Airport"
FROM {{ref("staging_flights")}}
WHERE TRIM("Destination_Airport") != "Destination_Airport"
