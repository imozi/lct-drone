export type RegionsResponse = {
  id: string;
  name: string;
  code: string;
  okato: string;
  status: string;
  utc: string;
  timezone: string;
  area: number;
};

export type StatisticsResponse = {
  all_regions_quarterly: {
    [keyof: string]: {
      region_id: string;
      avg_duration_minutes: number;
      avg_flights_per_day: number;
      flight_density: number;
      flights_count: number;
      median_duration_minutes: number;
      total_duration_hours: number;
      zero_flight_days: number;
      region_code: string;
      region_name: string;
    }[];
  };
  overall_statistics: {
    average_activity_index: number;
    total_flights_count: number;
    avg_flights_per_month: number;
    overall_flight_density: number;
    total_duration_hours: number;
    avg_duration_minutes: number;
    median_duration_minutes: number;
  };

  monthly_statistics: {
    month: string;
    flights_count: number;
    flight_density: number;
    total_duration_hours: number;
    avg_duration_minutes: number;
    median_duration_minutes: number;
  }[];

  regional_monthly_statistics: {
    [keyof: string]: {
      monthly_data: {
        month: string;
        flights_count: number;
        flight_density: number;
        total_duration_hours: number;
        avg_duration_minutes: number;
      }[];
      region_code: string;
      region_name: string;
      region_id: string;
    };
  };

  top_10_regions_overall: {
    region_id: string;
    region_name: string;
    region_code: string;
    flights_count: number;
    flight_density: number;
    total_duration_hours: number;
    avg_duration_minutes: number;
    median_duration_minutes: number;
    activity_index: number;
  }[];
};

export type RegionsGeneralResponse = {
  year: number;
  total_regions: number;
  regional_statistics: {
    rating: number;
    region_id: string;
    region_name: string;
    region_code: string;
    year: number;
    activity_index: number;
    flights_count: number;
    flight_density: number;
    avg_flights_per_day: number;
    total_duration_hours: number;
    avg_duration_minutes: number;
    median_duration_minutes: number;
    zero_flight_days: number;
    time_distribution: {
      morning_flights: number;
      day_flights: number;
      evening_flights: number;
    };
  }[];
};

export type UploadResponse = {
  success: boolean;
  message: string;
  loading_time_minutes: number;
  total_flight_plans: number;
  successfully_loaded: number;
  validation_failures: number;
  loading_status: string;
};
