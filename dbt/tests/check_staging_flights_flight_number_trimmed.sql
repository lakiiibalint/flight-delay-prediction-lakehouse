{{config (severity = 'warn')}}

SELECT 
    TRIM("Flight_Number"),
    "Flight_Number"
FROM {{ref("staging_flights")}}
WHERE TRIM("Flight_Number") != "Flight_Number"
