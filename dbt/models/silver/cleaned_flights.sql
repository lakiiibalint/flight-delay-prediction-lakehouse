SELECT 
    {{ dbt_utils.generate_surrogate_key([
    'Flight_Date', 'Reporting_Airline', 'Flight_Number',
    'Origin_Airport', 'Destination_Airport'
    ]) }} AS Flight_Id,
    Flight_Number,
    Flight_Date,
    Reporting_Airline,
    Origin_Airport,
    Destination_Airport,
    Departure_Delay,
    Is_Flight_Cancelled,
    intDiv(Scheduled_Departure_Time, 100) % 24 AS Hour_Of_Departure
FROM {{ref("staging_flights")}}