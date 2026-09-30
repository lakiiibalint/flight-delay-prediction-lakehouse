SELECT 
    Flight_Number,
    Flight_Date,
    Reporting_Airline,
    Origin_Airport,
    Destination_Airport,
    Departure_Delay,
    Is_Flight_Cancelled,
    intDiv(Scheduled_Departure_Time, 100) AS Hour_Of_Departure
FROM {{ref("staging_flights")}}