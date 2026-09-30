{{config (severity = 'warn')}}
SELECT
     "Departure_Delay"
FROM
    {{ref('staging_flights')}}
WHERE "Departure_Delay" < -90


