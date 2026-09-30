WITH raw_flights AS(
    SELECT * FROM s3(minio_bronze, filename='bts_ontime/year=2026/month=07/bts_ontime_2026_07.parquet')
)

SELECT 
    Flight_Number_Reporting_Airline AS Flight_Number,
    toDate(FlightDate) AS Flight_Date,
    Reporting_Airline,
    Origin AS Origin_Airport,
    Dest AS Destination_Airport,
    toFloat32OrNull(DepDelay) AS Departure_Delay,
    toUInt8(toFloat32(Cancelled)) AS Is_Flight_Cancelled,
    toUInt16OrNull(CRSDepTime) AS Scheduled_Departure_Time
FROM raw_flights