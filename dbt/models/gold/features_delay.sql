WITH cleaned_flights AS (
    SELECT * FROM {{ ref('cleaned_flights') }}
),

traffic_per_flight AS (
    SELECT
        *,
        count() OVER (PARTITION BY "Origin_Airport", "Flight_Date", "Hour_Of_Departure") AS Departures_In_Hour
    FROM cleaned_flights
),

calendar AS (
    SELECT "Flight_Date", "Days_To_Nearest_Holiday"
    FROM {{ ref('dim_calendar') }}
)

SELECT 
    "Flight_Id",
    "Flight_Number",
    "Flight_Date",
    "Reporting_Airline",
    "Origin_Airport",
    "Destination_Airport",
    "Departure_Delay",
    CASE WHEN Departure_Delay >= 15 THEN 1 ELSE 0 END AS Is_Dep_Delay_Greater_Than_15,
    "Hour_Of_Departure",
    "Weekday_Of_Departure",
    toMonth("Flight_Date") AS "Month_Of_Departure",
    "Departures_In_Hour",
    "Days_To_Nearest_Holiday",
    "Distance_Miles"
FROM traffic_per_flight
LEFT JOIN calendar USING ("Flight_Date")
WHERE Is_Flight_Cancelled = 0