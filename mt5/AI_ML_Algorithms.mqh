//+------------------------------------------------------------------+
//|                                      AI_ML_Algorithms.mqh  |
//|                        AI and Machine Learning Helper Functions   |
//|                                       Fixed for MT5 Compatibility |
//+------------------------------------------------------------------+

#ifndef AI_ML_ALGORITHMS_MQH
#define AI_ML_ALGORITHMS_MQH

// Include Config first to get constants
#include "Config.mqh"

//+------------------------------------------------------------------+
//| Simple dynamic array class for doubles                          |
//+------------------------------------------------------------------+
class CArrayDouble
{
private:
    double m_data[];
    int m_size;
    
public:
    CArrayDouble() { m_size = 0; ArrayResize(m_data, 0); }
    ~CArrayDouble() {}
    
    void Clear() { 
        ArrayResize(m_data, 0); 
        m_size = 0; 
    }
    
    bool Add(double value) { 
        ArrayResize(m_data, m_size + 1); 
        m_data[m_size] = value; 
        m_size++; 
        return true; 
    }
    
    double At(int index) { 
        return (index >= 0 && index < m_size) ? m_data[index] : 0.0; 
    }
    
    int Total() { 
        return m_size; 
    }
    
    double GetAt(int index) { 
        return (index >= 0 && index < m_size) ? m_data[index] : 0.0; 
    }
};

//+------------------------------------------------------------------+
//| AI Predictor Class with improved error handling                 |
//+------------------------------------------------------------------+
class CAIPredictor
{
private:
    string m_serverUrl;
    string m_apiKey;
    bool m_isConnected;
    datetime m_lastConnectionCheck;
    
    // Helper methods
    bool ValidateServerConnection();
    string ParseJsonValue(string json, string key);
    bool IsValidFeatureSet(CArrayDouble &features);
    
public:
    CAIPredictor(string serverUrl, string apiKey);
    ~CAIPredictor();
    
    // Main methods
    int GetPrediction(CArrayDouble &features, double &confidence);
    bool SendFeedback(string tradeId, double profit, bool isSuccessful);
    bool PrepareFeatures(CArrayDouble &features, string symbol, ENUM_TIMEFRAMES timeframe);
    bool SendTrainingData(CArrayDouble &features, int signal, double result);
    
    // Status methods
    bool IsConnected() { return m_isConnected; }
    string GetServerUrl() { return m_serverUrl; }
    bool TestConnection();
};

//+------------------------------------------------------------------+
//| Constructor                                                      |
//+------------------------------------------------------------------+
CAIPredictor::CAIPredictor(string serverUrl, string apiKey)
{
    m_serverUrl = serverUrl;
    m_apiKey = apiKey;
    m_isConnected = false;
    m_lastConnectionCheck = 0;
    
    // Test initial connection
    TestConnection();
}

//+------------------------------------------------------------------+
//| Destructor                                                      |
//+------------------------------------------------------------------+
CAIPredictor::~CAIPredictor()
{
    // Cleanup if needed
}

//+------------------------------------------------------------------+
//| Test server connection                                           |
//+------------------------------------------------------------------+
bool CAIPredictor::TestConnection()
{
    if(StringLen(m_serverUrl) == 0 || StringLen(m_apiKey) == 0)
    {
        m_isConnected = false;
        return false;
    }
    
    // Simple ping test
    string headers = "Content-Type: application/json\r\nAuthorization: Bearer " + m_apiKey + "\r\n";
    string jsonData = "{\"test\":\"ping\"}";
    
    char post[], result[];
    StringToCharArray(jsonData, post);
    
    string url = m_serverUrl + "/health";
    int res = WebRequest("GET", url, headers, HTTP_TIMEOUT, post, result, headers);
    
    m_isConnected = (res == 200);
    m_lastConnectionCheck = TimeCurrent();
    
    return m_isConnected;
}

//+------------------------------------------------------------------+
//| Get AI prediction with improved error handling                  |
//+------------------------------------------------------------------+
int CAIPredictor::GetPrediction(CArrayDouble &features, double &confidence)
{
    confidence = 0.0;
    
    // Validate inputs
    if(!IsValidFeatureSet(features))
    {
        Print("Error: Invalid feature set for prediction");
        return 0;
    }
    
    // Check connection
    if(!m_isConnected || (TimeCurrent() - m_lastConnectionCheck) > 300) // 5 minutes
    {
        if(!TestConnection())
        {
            Print("Warning: Server connection failed, using default prediction");
            return 0;
        }
    }
    
    string headers = "Content-Type: application/json\r\nAuthorization: Bearer " + m_apiKey + "\r\n";
    string jsonData = "{\"features\":[";
    
    // Build features array
    for(int i = 0; i < features.Total(); i++)
    {
        jsonData += DoubleToString(features.At(i), 6);
        if(i < features.Total() - 1) jsonData += ",";
    }
    jsonData += "]}";
    
    char post[], result[];
    StringToCharArray(jsonData, post);
    
    string url = m_serverUrl + ENDPOINT_PREDICT;
    int res = WebRequest("POST", url, headers, HTTP_TIMEOUT, post, result, headers);
    
    if(res == 200)
    {
        string response = CharArrayToString(result);
        
        // Parse JSON response safely
        string predStr = ParseJsonValue(response, "prediction");
        string confStr = ParseJsonValue(response, "confidence");
        
        if(StringLen(predStr) > 0 && StringLen(confStr) > 0)
        {
            confidence = StringToDouble(confStr);
            int prediction = (int)StringToInteger(predStr);
            
            // Validate prediction range
            if(prediction >= -1 && prediction <= 1 && confidence >= 0.0 && confidence <= 1.0)
            {
                return prediction;
            }
        }
    }
    else
    {
        Print("Server request failed with code: ", res);
        m_isConnected = false;
    }
    
    return 0; // Default HOLD
}

//+------------------------------------------------------------------+
//| Send feedback with improved error handling                      |
//+------------------------------------------------------------------+
bool CAIPredictor::SendFeedback(string tradeId, double profit, bool isSuccessful)
{
    if(!m_isConnected)
        return false;
        
    string headers = "Content-Type: application/json\r\nAuthorization: Bearer " + m_apiKey + "\r\n";
    string jsonData = StringFormat("{\"trade_id\":\"%s\",\"profit\":%.2f,\"successful\":%s,\"timestamp\":\"%s\"}", 
                                  tradeId, profit, isSuccessful ? "true" : "false", TimeToString(TimeCurrent()));
    
    char post[], result[];
    StringToCharArray(jsonData, post);
    
    string url = m_serverUrl + ENDPOINT_FEEDBACK;
    int res = WebRequest("POST", url, headers, HTTP_TIMEOUT, post, result, headers);
    
    if(res != 200)
    {
        Print("Failed to send feedback. Status code: ", res);
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Prepare technical indicators as features - Enhanced             |
//+------------------------------------------------------------------+
bool CAIPredictor::PrepareFeatures(CArrayDouble &features, string symbol, ENUM_TIMEFRAMES timeframe)
{
    features.Clear();
    
    // Get market data with error checking
    double close[], high[], low[], open[], volume[];
    
    if(CopyClose(symbol, timeframe, 0, 50, close) < 50) 
    {
        Print("Error: Insufficient close price data");
        return false;
    }
    if(CopyHigh(symbol, timeframe, 0, 50, high) < 50) 
    {
        Print("Error: Insufficient high price data");
        return false;
    }
    if(CopyLow(symbol, timeframe, 0, 50, low) < 50) 
    {
        Print("Error: Insufficient low price data");
        return false;
    }
    if(CopyOpen(symbol, timeframe, 0, 50, open) < 50) 
    {
        Print("Error: Insufficient open price data");
        return false;
    }
    if(CopyTickVolume(symbol, timeframe, 0, 50, volume) < 50) 
    {
        Print("Error: Insufficient volume data");
        return false;
    }
    
    // Basic price features with safety checks
    double currentClose = close[ArraySize(close) - 1];
    double prevClose = close[ArraySize(close) - 2];
    
    if(prevClose > 0)
    {
        features.Add(currentClose); // Current price
        features.Add((currentClose - prevClose) / prevClose); // Price change %
    }
    else
    {
        features.Add(currentClose);
        features.Add(0.0);
    }
    
    // Volatility
    double currentHigh = high[ArraySize(high) - 1];
    double currentLow = low[ArraySize(low) - 1];
    if(currentClose > 0)
        features.Add((currentHigh - currentLow) / currentClose);
    else
        features.Add(0.0);
    
    // Technical indicators with handle management
    int rsiHandle = iRSI(symbol, timeframe, 14, PRICE_CLOSE);
    if(rsiHandle != INVALID_HANDLE)
    {
        double rsi[];
        if(CopyBuffer(rsiHandle, 0, 0, 1, rsi) > 0)
            features.Add(rsi[0] / 100.0); // Normalize to 0-1
        else
            features.Add(0.5);
        IndicatorRelease(rsiHandle);
    }
    else
        features.Add(0.5);
    
    // MACD
    int macdHandle = iMACD(symbol, timeframe, 12, 26, 9, PRICE_CLOSE);
    if(macdHandle != INVALID_HANDLE)
    {
        double macd[], signal[];
        if(CopyBuffer(macdHandle, 0, 0, 1, macd) > 0 && CopyBuffer(macdHandle, 1, 0, 1, signal) > 0)
        {
            features.Add(macd[0]);
            features.Add(signal[0]);
            features.Add(macd[0] - signal[0]);
        }
        else
        {
            features.Add(0.0);
            features.Add(0.0);
            features.Add(0.0);
        }
        IndicatorRelease(macdHandle);
    }
    else
    {
        features.Add(0.0);
        features.Add(0.0);
        features.Add(0.0);
    }
    
    // Moving Averages
    int ma20Handle = iMA(symbol, timeframe, 20, 0, MODE_SMA, PRICE_CLOSE);
    if(ma20Handle != INVALID_HANDLE)
    {
        double ma20[];
        if(CopyBuffer(ma20Handle, 0, 0, 1, ma20) > 0 && ma20[0] > 0)
            features.Add((currentClose - ma20[0]) / ma20[0]);
        else
            features.Add(0.0);
        IndicatorRelease(ma20Handle);
    }
    else
        features.Add(0.0);
    
    int ma50Handle = iMA(symbol, timeframe, 50, 0, MODE_SMA, PRICE_CLOSE);
    if(ma50Handle != INVALID_HANDLE)
    {
        double ma50[];
        if(CopyBuffer(ma50Handle, 0, 0, 1, ma50) > 0 && ma50[0] > 0)
            features.Add((currentClose - ma50[0]) / ma50[0]);
        else
            features.Add(0.0);
        IndicatorRelease(ma50Handle);
    }
    else
        features.Add(0.0);
    
    // Bollinger Bands
    int bbHandle = iBands(symbol, timeframe, 20, 0, 2.0, PRICE_CLOSE);
    if(bbHandle != INVALID_HANDLE)
    {
        double bbUpper[], bbLower[], bbMiddle[];
        if(CopyBuffer(bbHandle, 0, 0, 1, bbMiddle) > 0 && 
           CopyBuffer(bbHandle, 1, 0, 1, bbUpper) > 0 && 
           CopyBuffer(bbHandle, 2, 0, 1, bbLower) > 0)
        {
            double bbWidth = bbUpper[0] - bbLower[0];
            if(bbWidth > 0)
            {
                features.Add((currentClose - bbLower[0]) / bbWidth); // BB Position
                features.Add(bbWidth / bbMiddle[0]); // BB Width
            }
            else
            {
                features.Add(0.5);
                features.Add(0.1);
            }
        }
        else
        {
            features.Add(0.5);
            features.Add(0.1);
        }
        IndicatorRelease(bbHandle);
    }
    else
    {
        features.Add(0.5);
        features.Add(0.1);
    }
    
    // ATR
    int atrHandle = iATR(symbol, timeframe, 14);
    if(atrHandle != INVALID_HANDLE)
    {
        double atr[];
        if(CopyBuffer(atrHandle, 0, 0, 1, atr) > 0 && currentClose > 0)
            features.Add(atr[0] / currentClose);
        else
            features.Add(0.01);
        IndicatorRelease(atrHandle);
    }
    else
        features.Add(0.01);
    
    // Volume analysis
    if(ArraySize(volume) >= 5)
    {
        double avgVolume = 0;
        for(int i = ArraySize(volume) - 5; i < ArraySize(volume) - 1; i++)
            avgVolume += volume[i];
        avgVolume /= 4.0;
        
        if(avgVolume > 0)
            features.Add(volume[ArraySize(volume) - 1] / avgVolume);
        else
            features.Add(1.0);
    }
    else
        features.Add(1.0);
    
    // Time-based features
    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);
    features.Add((double)dt.hour / 24.0);
    features.Add((double)dt.day_of_week / 7.0);
    
    // Momentum
    if(ArraySize(close) >= 10)
    {
        double momentum5 = (currentClose - close[ArraySize(close) - 6]) / close[ArraySize(close) - 6];
        double momentum10 = (currentClose - close[ArraySize(close) - 11]) / close[ArraySize(close) - 11];
        features.Add(momentum5);
        features.Add(momentum10);
    }
    else
    {
        features.Add(0.0);
        features.Add(0.0);
    }
    
    // Support/Resistance
    double highest = high[0];
    double lowest = low[0];
    for(int i = 1; i < MathMin(20, ArraySize(high)); i++)
    {
        if(high[i] > highest) highest = high[i];
        if(low[i] < lowest) lowest = low[i];
    }
    
    if(highest > lowest)
    {
        features.Add((currentClose - lowest) / (highest - lowest));
        features.Add((highest - lowest) / currentClose);
    }
    else
    {
        features.Add(0.5);
        features.Add(0.1);
    }
    
    return features.Total() >= FEATURE_COUNT;
}

//+------------------------------------------------------------------+
//| Send training data with validation                              |
//+------------------------------------------------------------------+
bool CAIPredictor::SendTrainingData(CArrayDouble &features, int signal, double result)
{
    if(!m_isConnected || !IsValidFeatureSet(features))
        return false;
    
    string headers = "Content-Type: application/json\r\nAuthorization: Bearer " + m_apiKey + "\r\n";
    string jsonData = "{\"features\":[";
    
    for(int i = 0; i < features.Total(); i++)
    {
        jsonData += DoubleToString(features.At(i), 6);
        if(i < features.Total() - 1) jsonData += ",";
    }
    
    jsonData += StringFormat("],\"signal\":%d,\"result\":%.2f,\"timestamp\":\"%s\"}", 
                           signal, result, TimeToString(TimeCurrent()));
    
    char post[], result_data[];
    StringToCharArray(jsonData, post);
    
    string url = m_serverUrl + "/training_data";
    int res = WebRequest("POST", url, headers, HTTP_TIMEOUT, post, result_data, headers);
    
    return res == 200;
}

//+------------------------------------------------------------------+
//| Helper: Validate feature set                                    |
//+------------------------------------------------------------------+
bool CAIPredictor::IsValidFeatureSet(CArrayDouble &features)
{
    if(features.Total() < FEATURE_COUNT)
        return false;
    
    // Check for NaN or infinite values
    for(int i = 0; i < features.Total(); i++)
    {
        double val = features.At(i);
        if(val != val || val == EMPTY_VALUE) // NaN check
            return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Helper: Simple JSON value parser                                |
//+------------------------------------------------------------------+
string CAIPredictor::ParseJsonValue(string json, string key)
{
    string searchKey = "\"" + key + "\":";
    int start = StringFind(json, searchKey);
    if(start < 0) return "";
    
    start += StringLen(searchKey);
    
    // Skip whitespace and quotes
    while(start < StringLen(json) && (StringGetCharacter(json, start) == ' ' || StringGetCharacter(json, start) == '"'))
        start++;
    
    int end = start;
    while(end < StringLen(json) && 
          StringGetCharacter(json, end) != ',' && 
          StringGetCharacter(json, end) != '}' && 
          StringGetCharacter(json, end) != '"')
        end++;
    
    if(end <= start) return "";
    
    return StringSubstr(json, start, end - start);
}

#endif 
