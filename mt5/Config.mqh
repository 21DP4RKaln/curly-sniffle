//+------------------------------------------------------------------+
//|                                                       Config.mqh |
//|                        Configuration file for AI Trading Bot     |
//|                                        Enhanced with more options |
//+------------------------------------------------------------------+

#ifndef CONFIG_MQH
#define CONFIG_MQH

#define HTTP_TIMEOUT 5000
#define MAX_RETRY_ATTEMPTS 3

#define MAX_POSITIONS 10
#define MIN_LOT_SIZE 0.01
#define MAX_LOT_SIZE 10.0

#define FEATURE_COUNT 20
#define PREDICTION_CLASSES 3  

#define ENDPOINT_PREDICT "/predict"
#define ENDPOINT_FEEDBACK "/feedback"
#define ENDPOINT_REGISTER "/register_user"
#define ENDPOINT_HEALTH "/health"

#define CANDLES_HISTORY 100
#define INDICATORS_COUNT 10

#define TRADING_START_HOUR 3
#define TRADING_END_HOUR 22

#define MAX_SPREAD_MULTIPLIER 2.5
#define MIN_CONFIDENCE_THRESHOLD 0.6

#define AI_WEIGHTS_FILE_PREFIX "ai_weights_"
#define AI_DATA_BACKUP_FILE "ai_data_backup.json"
#define TRAINING_DATA_FILE "training_data.json"

#endif
