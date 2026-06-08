
export type ApiEnvelope<T> = {
  success: boolean;
  data?: T;
  message?: string;
  detail?: string;
};

export type StatusData = {
  backend: string;
  model_loaded: boolean;
  model_type: string;
  window_size: number;
  step_size: number;
  input_shape: number[] | number[][];
  feature_dim: number;
  esp32_1_connected: boolean;
  esp32_2_connected: boolean;
  monitoring: boolean;
  latest_prediction?: PredictionData | null;
  live_prediction?: {
    buffer_size: number;
    window_size: number;
    step_size: number;
    samples_since_last_prediction: number;
    samples_needed_for_first_prediction: number;
    samples_needed_for_next_prediction: number;
    ready_for_prediction: boolean;
    buffer_fill_percent: number;
    prediction_progress_percent: number;
    progress_percent: number;
  };
  udp?: {
    received_packets: number;
    accepted_packets: number;
    rejected_packets: number;
    last_packet_seconds_ago: number | null;
    last_valid_packet_seconds_ago: number | null;
    last_sender_ip: string | null;
    last_sender_port: string | null;
    listener_thread_alive: boolean;
    socket_bound: boolean;
  };
};

export type PredictionData = {
  presence: string;
  raw_presence?: string;
  confidence: number;
  probabilities: Record<string, number>;
  timestamp: string;
};

export type AuthDataType = {
  user_id: number;
  email: string;
};
// export type ProfileData = {
//   email: string;
//   full_name?: string;
// }
export type RegisterPayload = {
  email: string;
  password: string;
  confirm_password: string;
  full_name?: string;
};

export type LoginPayload = {
  email: string;
  password: string;
};
export type Metadata = {
  user_id: number;
  email: string;
  full_name: string | null;
  created_at: string; // Assuming it's a string representation of datetime
};
export type LoginData = {
  access_token: string;
  user_id: number;
  email: string;
};

