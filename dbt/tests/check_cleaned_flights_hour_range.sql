SELECT
 *
FROM {{ref("cleaned_flights")}}
WHERE "Hour_Of_Departure" > 23 