-- ============================================================
-- Colombo Taxi Rides Dataset Schema
-- Adapted for Sri Lanka (City of Colombo)
-- Seasons redefined for tropical Sri Lanka:
--   1 = Dry Season       (Dec, Jan, Feb, Mar)
--   2 = Pre-Monsoon      (Apr, May)
--   3 = SW Monsoon / Wet (Jun, Jul, Aug, Sep)
--   4 = Post-Monsoon     (Oct, Nov)
--
-- Holidays include Sri Lankan public holidays:
--   Poya days (~12/yr), Independence Day, Sinhala/Tamil New Year,
--   May Day, Vesak, Christmas, Deepavali, Eid, etc.
-- ============================================================

CREATE TABLE colombo_taxi_rides (
    id          SERIAL          PRIMARY KEY,

    -- Hourly timestamp; one row per hour
    datetime    TIMESTAMP       NOT NULL,

    -- Season (Sri Lanka tropical calendar)
    -- 1=Dry, 2=Pre-Monsoon, 3=SW Monsoon/Wet, 4=Post-Monsoon
    season      SMALLINT        NOT NULL
                    CHECK (season BETWEEN 1 AND 4),

    -- Hour of the day (0 = midnight, 23 = 11 PM)
    hour        SMALLINT        NOT NULL
                    CHECK (hour BETWEEN 0 AND 23),

    -- Public holiday flag (Sri Lankan calendar)
    -- 0 = Regular day, 1 = Public holiday
    holiday     SMALLINT        NOT NULL
                    CHECK (holiday IN (0, 1)),

    -- Day of week  (0 = Sunday ... 6 = Saturday)
    weekday     SMALLINT        NOT NULL
                    CHECK (weekday BETWEEN 0 AND 6),

    -- Weather situation
    -- 1 = Clear / Partly Cloudy
    -- 2 = Mist + Cloudy
    -- 3 = Light Rain / Drizzle
    -- 4 = Heavy Rain / Thunderstorm
    weathersit  SMALLINT        NOT NULL
                    CHECK (weathersit BETWEEN 1 AND 4),

    -- Temperature in Celsius (Colombo: tropical, 24–36 °C)
    temp        NUMERIC(5, 2)   NOT NULL
                    CHECK (temp BETWEEN 24.0 AND 37.0),

    -- Relative humidity in % (Colombo: 55–97 %)
    humidity    NUMERIC(5, 2)   NOT NULL
                    CHECK (humidity BETWEEN 45.0 AND 98.0),

    -- Wind speed in km/h (Colombo: 3–35 km/h)
    windspeed   NUMERIC(5, 2)   NOT NULL
                    CHECK (windspeed BETWEEN 0.0 AND 40.0),

    -- Total taxi ride bookings in that hour across Colombo
    -- Realistic range for Colombo (PickMe/Uber scale):
    --   Night trough: 80–400  |  Daytime: 600–2000  |  Rush hour: 1800–5000
    ride_count  INTEGER         NOT NULL
                    CHECK (ride_count >= 0)
);

-- Index for time-series queries
CREATE INDEX idx_colombo_taxi_datetime  ON colombo_taxi_rides (datetime);
CREATE INDEX idx_colombo_taxi_season    ON colombo_taxi_rides (season);
CREATE INDEX idx_colombo_taxi_hour      ON colombo_taxi_rides (hour);
