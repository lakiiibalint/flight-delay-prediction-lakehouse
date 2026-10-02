SELECT 
    "Flight_Number",
    "Flight_Date",
    "Reporting_Airline",
    "Origin_Airport",
    "Destination_Airport",
    "Departure_Delay",
    CASE WHEN Departure_Delay >= 15 THEN 1 ELSE 0 END AS Is_Dep_Delay_Greater_Than_15,
    "Hour_Of_Departure"
FROM {{ref("cleaned_flights")}}
WHERE Is_Flight_Cancelled = 0