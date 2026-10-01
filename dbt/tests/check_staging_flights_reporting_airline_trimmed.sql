{{config (severity = 'warn')}}

SELECT
    TRIM(Reporting_Airline),
    "Reporting_Airline"
FROM {{ref("staging_flights")}}
WHERE TRIM("Reporting_Airline") != "Reporting_Airline"
