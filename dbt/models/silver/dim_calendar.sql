WITH days AS (
    SELECT DISTINCT Flight_Date
    FROM {{ ref('cleaned_flights') }}
),

holidays AS (
    SELECT holiday_date
    FROM {{ ref('us_holidays') }}
)

SELECT
    Flight_Date,
    minIf(dateDiff('day', Flight_Date, holiday_date), holiday_date >= Flight_Date) AS Days_To_Next_Holiday,
    minIf(dateDiff('day', holiday_date, Flight_Date), holiday_date <= Flight_Date) AS Days_Since_Last_Holiday,
    least(Days_To_Next_Holiday, Days_Since_Last_Holiday) AS Days_To_Nearest_Holiday
FROM days
CROSS JOIN holidays
GROUP BY Flight_Date