SELECT
    COUNT(*),
    Flight_Number,
    Flight_Date,
    Reporting_Airline,
    Origin_Airport,
    Destination_Airport
FROM {{ref('staging_flights')}}
GROUP BY 
    Flight_Number,
    Flight_Date,
    Reporting_Airline,
    Origin_Airport,
    Destination_Airport
HAVING COUNT(*) > 1
