//+------------------------------------------------------------------+
//|                                                          SVN.mq5 |
//|                                  Copyright 2025, MetaQuotes Ltd. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, MetaQuotes Ltd."
#property link      "https://www.mql5.com"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>
#include <Trade\SymbolInfo.mqh>
#include <Arrays\ArrayDouble.mqh>
#include <Arrays\ArrayInt.mqh>

#include "Config.mqh"
#include "AI_ML_Algorithms.mqh"

// Экспертные параметры
input group "=== AI Configuration ==="
input string   ServerURL = "https://sitvain.pythonanywhere.com/api";  
input string   APIKey = "61c2f3467e03e633d25a9bbc3caf05ed990aa6eaa59d2435601309148e48892f";                       
input bool     EnableLearning = true;                        
input int      DataSendInterval = 60;

input group "=== Trading Parameters ==="
input double   LotSize = 0.01;                                 
input double   MaxRisk = 0.02;                               
input double   StopLoss = 50;                                 
input double   TakeProfit = 100;                               
input int      MagicNumber = 12345;                            

input group "=== AI Learning Parameters ==="
input int      LearningPeriod = 100;                          
input int      PredictionHorizon = 5;                         
input double   LearningRate = 0.01;                           
input int      NeuralLayers = 3;                              

CTrade trade;
CPositionInfo posInfo;
CAccountInfo accInfo;
CSymbolInfo symInfo;
CAIPredictor* aiPredictor = NULL; 


struct MarketData
{
    datetime time;
    double open, high, low, close;
    long volume;
    double indicators[20];  
    int signal;           
    double result;         
};

struct NeuralNetwork
{
    double weights[100][50];   
    double biases[100];        
    double learning_rate;      
    int input_size;           
    int hidden_size;          
    int output_size;        
};

MarketData marketHistory[];
NeuralNetwork aiNetwork;
datetime lastDataSend;
double dailyProfit = 0;
double maxDrawdown = 0;
double currentDrawdown = 0;
int totalTrades = 0;
int winningTrades = 0;

CArrayDouble priceHistory;
CArrayDouble volumeHistory;
CArrayInt signalHistory;

// Trade tracking variables
struct TradeInfo
{
    string id;
    datetime openTime;
    double openPrice;
    double lot;
    int signal;
    bool isActive;
};

TradeInfo activeTrades[10];
int activeTradesCount = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    trade.SetExpertMagicNumber(MagicNumber);
    trade.SetDeviationInPoints(10);
    trade.SetTypeFilling(ORDER_FILLING_FOK);
    
    if(!symInfo.Name(_Symbol))
    {
        Print("Ошибка инициализации символа");
        return INIT_FAILED;
    }
    
    // Initialize AI predictor
    if(aiPredictor != NULL)
    {
        delete aiPredictor;
        aiPredictor = NULL;
    }
    
    aiPredictor = new CAIPredictor(ServerURL, APIKey);
    if(aiPredictor == NULL)
    {
        Print("Ошибка инициализации AI предиктора");
        return INIT_FAILED;
    }
    
    // Test AI connection
    if(aiPredictor.TestConnection())
        Print("AI сервер подключен успешно");
    else
        Print("AI сервер недоступен, используется локальная нейросеть");
    
    InitializeAI();
    LoadAIData();
    
    ArrayResize(marketHistory, LearningPeriod);
    
    // Initialize trade tracking
    for(int i = 0; i < 10; i++)
    {
        activeTrades[i].isActive = false;
        activeTrades[i].id = "";
    }
    activeTradesCount = 0;
    
    lastDataSend = TimeCurrent();
    
    Print("SVN инициализирован успешно");
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    SaveAIData();
    SendDataToServer();
    
    // Cleanup AI predictor
    if(aiPredictor != NULL)
    {
        delete aiPredictor;
        aiPredictor = NULL;
    }
    
    Print("SVN завершен. Причина: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    // Check position status first and update tracking
    CheckPositionStatus();
    
    UpdateMarketData();
    
    int aiSignal = AnalyzeWithAI();
    
    if(!RiskManagement())
        return;
    
    MakeTradingDecision(aiSignal);
    
    if(EnableLearning)
        TrainAI();
    
    // Send data to server periodically
    if(TimeCurrent() - lastDataSend >= DataSendInterval)
    {
        SendDataToServer();
        lastDataSend = TimeCurrent();
    }
}

//+------------------------------------------------------------------+
//| Check and update position status                                |
//+------------------------------------------------------------------+
void CheckPositionStatus()
{
    // Check if any tracked positions have closed
    for(int i = 0; i < activeTradesCount; i++)
    {
        if(activeTrades[i].isActive)
        {
            bool positionExists = false;
            
            // Check if position still exists
            for(int j = 0; j < PositionsTotal(); j++)
            {
                if(posInfo.SelectByIndex(j) && 
                   posInfo.Magic() == MagicNumber &&
                   IntegerToString(posInfo.Ticket()) == activeTrades[i].id)
                {
                    positionExists = true;
                    break;
                }
            }
            
            // If position no longer exists, it was closed
            if(!positionExists)
            {
                // Calculate result based on last known price
                double currentPrice = (activeTrades[i].signal == 1) ? symInfo.Bid() : symInfo.Ask();
                bool isWin = false;
                
                if(activeTrades[i].signal == 1) // BUY
                    isWin = currentPrice > activeTrades[i].openPrice;
                else if(activeTrades[i].signal == -1) // SELL
                    isWin = currentPrice < activeTrades[i].openPrice;
                
                UpdateTradeStatus(activeTrades[i].id, currentPrice, isWin);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Инициализация ИИ системы                                        |
//+------------------------------------------------------------------+
void InitializeAI()
{
    aiNetwork.learning_rate = LearningRate;
    aiNetwork.input_size = 20;      
    aiNetwork.hidden_size = 50;     
    aiNetwork.output_size = 3;      
    
    for(int i = 0; i < aiNetwork.hidden_size; i++)
    {
        for(int j = 0; j < aiNetwork.input_size; j++)
        {
            aiNetwork.weights[i][j] = (MathRand() / 32767.0 - 0.5) * 2.0;
        }
        aiNetwork.biases[i] = (MathRand() / 32767.0 - 0.5) * 2.0;
    }
    
    Print("Нейросеть инициализирована");
}

//+------------------------------------------------------------------+
//| Обновление рыночных данных                                      |
//+------------------------------------------------------------------+
void UpdateMarketData()
{
    static int lastBar = 0;
    int currentBar = Bars(_Symbol, PERIOD_CURRENT) - 1;
    
    if(currentBar == lastBar)
        return;
    
    lastBar = currentBar;
    
    MarketData newData;
    newData.time = iTime(_Symbol, PERIOD_CURRENT, 0);
    newData.open = iOpen(_Symbol, PERIOD_CURRENT, 0);
    newData.high = iHigh(_Symbol, PERIOD_CURRENT, 0);
    newData.low = iLow(_Symbol, PERIOD_CURRENT, 0);
    newData.close = iClose(_Symbol, PERIOD_CURRENT, 0);
    newData.volume = iVolume(_Symbol, PERIOD_CURRENT, 0);
    
    CalculateIndicators(newData);
    
    AddToHistory(newData);
}

//+------------------------------------------------------------------+
//| Расчет технических индикаторов                                  |
//+------------------------------------------------------------------+
void CalculateIndicators(MarketData &data)
{
    // Moving Averages
    data.indicators[0] = iMA(_Symbol, PERIOD_CURRENT, 14, 0, MODE_SMA, PRICE_CLOSE);
    data.indicators[1] = iMA(_Symbol, PERIOD_CURRENT, 50, 0, MODE_SMA, PRICE_CLOSE);
    data.indicators[2] = iMA(_Symbol, PERIOD_CURRENT, 200, 0, MODE_SMA, PRICE_CLOSE);
    
    data.indicators[3] = iRSI(_Symbol, PERIOD_CURRENT, 14, PRICE_CLOSE);
    
    data.indicators[4] = iMACD(_Symbol, PERIOD_CURRENT, 12, 26, 9, PRICE_CLOSE);
    
    data.indicators[5] = iBands(_Symbol, PERIOD_CURRENT, 20, 0, 2.0, PRICE_CLOSE);
    
    data.indicators[6] = iStochastic(_Symbol, PERIOD_CURRENT, 14, 3, 3, MODE_SMA, STO_LOWHIGH);
    
    data.indicators[7] = iADX(_Symbol, PERIOD_CURRENT, 14);
    
    data.indicators[8] = iATR(_Symbol, PERIOD_CURRENT, 14);
    
    data.indicators[9] = iCCI(_Symbol, PERIOD_CURRENT, 14, PRICE_TYPICAL);
    data.indicators[10] = iWPR(_Symbol, PERIOD_CURRENT, 14);
    
    data.indicators[11] = iOBV(_Symbol, PERIOD_CURRENT, PRICE_CLOSE);
    
    data.indicators[12] = (data.close - data.open) / data.open * 100; 
    data.indicators[13] = (data.high - data.low) / data.close * 100;  
    
    MqlDateTime dt;
    TimeToStruct(data.time, dt);
    data.indicators[14] = dt.hour;           
    data.indicators[15] = dt.day_of_week;   
    
    data.indicators[16] = GetMarketSession();
    
    data.indicators[17] = CalculateVolatility(10);
    
    data.indicators[18] = iMomentum(_Symbol, PERIOD_CURRENT, 14, PRICE_CLOSE);
    
    data.indicators[19] = iRoC(_Symbol, PERIOD_CURRENT, 12, PRICE_CLOSE);
}

//+------------------------------------------------------------------+
//| Анализ рынка с помощью ИИ                                       |
//+------------------------------------------------------------------+
int AnalyzeWithAI()
{
    if(ArraySize(marketHistory) < 10)
        return 0;
    
    // Use improved AI predictor if available
    if(aiPredictor != NULL)
    {
        CArrayDouble features;
        if(aiPredictor.PrepareFeatures(features, _Symbol, PERIOD_CURRENT))
        {
            double confidence;
            int serverPrediction = aiPredictor.GetPrediction(features, confidence);
            
            if(confidence > 0.6) // Only trade with high confidence
            {
                Print("AI предсказание: ", serverPrediction, " с уверенностью: ", confidence);
                return serverPrediction;
            }
            else
            {
                Print("Низкая уверенность AI: ", confidence, " - торговля приостановлена");
                return 0;
            }
        }
        else
        {
            Print("Ошибка подготовки features для AI");
        }
    }
    
    // Fallback to local neural network
    double inputs[20];
    int lastIndex = ArraySize(marketHistory) - 1;
    
    if(lastIndex < 0) return 0;
    
    for(int i = 0; i < 20; i++)
    {
        inputs[i] = marketHistory[lastIndex].indicators[i];
        inputs[i] = NormalizeValue(inputs[i], i);
    }
    
    double outputs[3];
    ForwardPropagation(inputs, outputs);
    
    int maxIndex = 0;
    for(int i = 1; i < 3; i++)
    {
        if(outputs[i] > outputs[maxIndex])
            maxIndex = i;
    }
    
    // Add confidence threshold for local prediction
    double confidence = outputs[maxIndex];
    if(confidence < 0.6)
    {
        Print("Низкая уверенность локальной нейросети: ", confidence);
        return 0;
    }
    
    Print("Локальное предсказание AI: ", maxIndex - 1, " с уверенностью: ", confidence);
    return maxIndex - 1;
}

//+------------------------------------------------------------------+
//| Прямое распространение через нейросеть                         |
//+------------------------------------------------------------------+
void ForwardPropagation(double &inputs[], double &outputs[])
{
    double hidden[50];
    
    for(int i = 0; i < aiNetwork.hidden_size; i++)
    {
        hidden[i] = aiNetwork.biases[i];
        for(int j = 0; j < aiNetwork.input_size; j++)
        {
            hidden[i] += inputs[j] * aiNetwork.weights[i][j];
        }
        hidden[i] = Sigmoid(hidden[i]);
    }
    
    for(int i = 0; i < aiNetwork.output_size; i++)
    {
        outputs[i] = 0;
        for(int j = 0; j < aiNetwork.hidden_size; j++)
        {
            outputs[i] += hidden[j] * aiNetwork.weights[aiNetwork.hidden_size + i][j];
        }
        outputs[i] = Sigmoid(outputs[i]);
    }
}

//+------------------------------------------------------------------+
//| Функция активации Sigmoid                                       |
//+------------------------------------------------------------------+
double Sigmoid(double x)
{
    return 1.0 / (1.0 + MathExp(-x));
}

//+------------------------------------------------------------------+
//| Управление рисками                                              |
//+------------------------------------------------------------------+
bool RiskManagement()
{
    double accountBalance = accInfo.Balance();
    double accountEquity = accInfo.Equity();
    
    // Avoid division by zero
    if(accountBalance <= 0)
    {
        Print("Ошибка: Баланс счета некорректен");
        return false;
    }
    
    currentDrawdown = (accountBalance - accountEquity) / accountBalance * 100;
    
    if(currentDrawdown > maxDrawdown)
        maxDrawdown = currentDrawdown;
    
    // Risk control
    if(currentDrawdown > MaxRisk * 100)
    {
        Print("Превышен максимальный риск: ", currentDrawdown, "%. Торговля остановлена.");
        return false;
    }
    
    // Time-based restrictions
    MqlDateTime dt;
    TimeCurrent(dt);
    
    if(dt.hour >= 22 || dt.hour <= 2) 
    {
        Print("Торговля приостановлена: время низкой ликвидности");
        return false;
    }
    
    // Friday evening restriction
    if(dt.day_of_week == 5 && dt.hour >= 20)
    {
        Print("Торговля приостановлена: пятничный вечер");
        return false;
    }
    
    // Spread control
    double spread = symInfo.Spread() * symInfo.Point();
    double avgSpread = CalculateAverageSpread();
    
    if(spread > avgSpread * 2.5)  // More conservative spread limit
    {
        Print("Спред слишком широкий: ", spread, " vs средний: ", avgSpread);
        return false;
    }
    
    // Maximum positions check
    int currentPositions = 0;
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(posInfo.SelectByIndex(i) && posInfo.Magic() == MagicNumber)
            currentPositions++;
    }
    
    if(currentPositions >= MAX_POSITIONS)
    {
        Print("Достигнуто максимальное количество позиций: ", currentPositions);
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Принятие торговых решений                                       |
//+------------------------------------------------------------------+
void MakeTradingDecision(int aiSignal)
{
    bool hasPosition = false;
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(posInfo.SelectByIndex(i) && posInfo.Magic() == MagicNumber)
        {
            hasPosition = true;
            break;
        }
    }
    
    if(hasPosition)
    {
        ManageOpenPositions();
        return;
    }
    
    if(aiSignal == 1)  
    {
        OpenBuyPosition();
    }
    else if(aiSignal == -1) 
    {
        OpenSellPosition();
    }
}

//+------------------------------------------------------------------+
//| Открытие позиции на покупку                                     |
//+------------------------------------------------------------------+
void OpenBuyPosition()
{
    double price = symInfo.Ask();
    double sl = price - StopLoss * symInfo.Point();
    double tp = price + TakeProfit * symInfo.Point();
    
    // Validate price levels
    double minStopLevel = symInfo.StopsLevel() * symInfo.Point();
    if((price - sl) < minStopLevel)
    {
        sl = price - minStopLevel;
        Print("Stop Loss скорректирован до минимального уровня: ", sl);
    }
    if((tp - price) < minStopLevel)
    {
        tp = price + minStopLevel;
        Print("Take Profit скорректирован до минимального уровня: ", tp);
    }
    
    double lotSize = CalculatePositionSize(price - sl);
    
    // Additional lot size validation
    if(lotSize < symInfo.LotsMin())
    {
        Print("Размер лота слишком мал: ", lotSize, ", используется минимальный: ", symInfo.LotsMin());
        lotSize = symInfo.LotsMin();
    }
    
    if(trade.Buy(lotSize, _Symbol, price, sl, tp, "AI Buy Signal"))
    {
        string tradeId = IntegerToString(trade.ResultOrder());
        Print("Открыта позиция BUY: ID=", tradeId, " Лот=", lotSize, " Цена=", price, " SL=", sl, " TP=", tp);
        totalTrades++;
        
        AddTradeTracking(tradeId, price, lotSize, 1);
    }
    else
    {
        Print("Ошибка открытия BUY позиции: ", trade.ResultRetcodeDescription());
    }
}

//+------------------------------------------------------------------+
//| Открытие позиции на продажу                                     |
//+------------------------------------------------------------------+
void OpenSellPosition()
{
    double price = symInfo.Bid();
    double sl = price + StopLoss * symInfo.Point();
    double tp = price - TakeProfit * symInfo.Point();
    
    // Validate price levels
    double minStopLevel = symInfo.StopsLevel() * symInfo.Point();
    if((sl - price) < minStopLevel)
    {
        sl = price + minStopLevel;
        Print("Stop Loss скорректирован до минимального уровня: ", sl);
    }
    if((price - tp) < minStopLevel)
    {
        tp = price - minStopLevel;
        Print("Take Profit скорректирован до минимального уровня: ", tp);
    }
    
    double lotSize = CalculatePositionSize(sl - price);
    
    // Additional lot size validation
    if(lotSize < symInfo.LotsMin())
    {
        Print("Размер лота слишком мал: ", lotSize, ", используется минимальный: ", symInfo.LotsMin());
        lotSize = symInfo.LotsMin();
    }
    
    if(trade.Sell(lotSize, _Symbol, price, sl, tp, "AI Sell Signal"))
    {
        string tradeId = IntegerToString(trade.ResultOrder());
        Print("Открыта позиция SELL: ID=", tradeId, " Лот=", lotSize, " Цена=", price, " SL=", sl, " TP=", tp);
        totalTrades++;
        
        AddTradeTracking(tradeId, price, lotSize, -1);
    }
    else
    {
        Print("Ошибка открытия SELL позиции: ", trade.ResultRetcodeDescription());
    }
}

//+------------------------------------------------------------------+
//| Расчет размера позиции                                          |
//+------------------------------------------------------------------+
double CalculatePositionSize(double riskDistance)
{
    double accountBalance = accInfo.Balance();
    double riskAmount = accountBalance * MaxRisk;
    double tickValue = symInfo.TickValue();
    double tickSize = symInfo.TickSize();
    
    // Safety checks
    if(riskDistance <= 0 || tickSize <= 0 || tickValue <= 0)
    {
        Print("Ошибка в расчете размера позиции: некорректные параметры");
        return symInfo.LotsMin();
    }
    
    double riskInTicks = riskDistance / tickSize;
    double positionSize = riskAmount / (riskInTicks * tickValue);
    
    double minLot = symInfo.LotsMin();
    double maxLot = symInfo.LotsMax();
    double lotStep = symInfo.LotsStep();
    
    // Ensure lot step compliance
    if(lotStep > 0)
        positionSize = MathRound(positionSize / lotStep) * lotStep;
    
    // Apply limits
    positionSize = MathMax(minLot, MathMin(maxLot, positionSize));
    
    // Additional safety: never risk more than specified lot size
    if(LotSize > 0)
        positionSize = MathMin(positionSize, LotSize);
    
    Print("Расчет позиции: риск=", riskDistance, " размер=", positionSize);
    return positionSize;
}

//+------------------------------------------------------------------+
//| Обучение ИИ на новых данных                                     |
//+------------------------------------------------------------------+
void TrainAI()
{
    if(ArraySize(marketHistory) < LearningPeriod)
        return;
    
    for(int i = ArraySize(marketHistory) - LearningPeriod; i < ArraySize(marketHistory) - 1; i++)
    {
        if(marketHistory[i].signal != 0) 
        {
            double inputs[20];
            for(int j = 0; j < 20; j++)
                inputs[j] = NormalizeValue(marketHistory[i].indicators[j], j);
            
            double expectedOutput[3] = {0, 0, 0};
            if(marketHistory[i].result > 0)
                expectedOutput[marketHistory[i].signal + 1] = 1.0;
            else
                expectedOutput[1] = 1.0;  
            
            BackPropagation(inputs, expectedOutput);
        }
    }
}

//+------------------------------------------------------------------+
//| Обратное распространение ошибки                                 |
//+------------------------------------------------------------------+
void BackPropagation(double &inputs[], double &expectedOutput[])
{
    double outputs[3];
    ForwardPropagation(inputs, outputs);
    
    double error[3];
    for(int i = 0; i < 3; i++)
    {
        error[i] = expectedOutput[i] - outputs[i];
    }
    
    for(int i = 0; i < aiNetwork.hidden_size; i++)
    {
        for(int j = 0; j < aiNetwork.input_size; j++)
        {
            double delta = aiNetwork.learning_rate * error[0] * inputs[j];  
            aiNetwork.weights[i][j] += delta;
        }
    }
}

//+------------------------------------------------------------------+
//| Отправка данных на сервер для обучения                          |
//+------------------------------------------------------------------+
void SendDataToServer()
{
    if(!EnableLearning || StringLen(ServerURL) == 0)
        return;
    
    string jsonData = CreateJSONData();
    
    string headers = "Content-Type: application/json\r\n";
    headers += "Authorization: Bearer " + APIKey + "\r\n";
    
    char post[];
    StringToCharArray(jsonData, post, 0, StringLen(jsonData));
    
    char result[];
    string resultHeaders;
    
    // Отправляем данные через WebRequest
    string url = ServerURL + "/api/data";
    int httpResult = WebRequest("POST", url, headers, 5000, post, result, resultHeaders);
    
    if(httpResult == 200)
    {
        Print("Данные успешно отправлены на сервер");
        string response = CharArrayToString(result);
        Print("Ответ сервера: ", response);
    }
    else
    {
        Print("Ошибка отправки данных на сервер. Код: ", httpResult);
        // Сохраняем данные локально для повторной отправки
        FileWrite("ai_data_backup.json", jsonData);
    }
    
    // Также сохраняем для локального анализа
    FileWrite("ai_data.json", jsonData);
}

//+------------------------------------------------------------------+
//| Создание JSON данных для отправки                               |
//+------------------------------------------------------------------+
string CreateJSONData()
{
    string json = "{";
    json += "\"timestamp\":\"" + TimeToString(TimeCurrent()) + "\",";
    json += "\"symbol\":\"" + _Symbol + "\",";
    json += "\"account_id\":\"" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + "\",";
    json += "\"balance\":" + DoubleToString(accInfo.Balance(), 2) + ",";
    json += "\"equity\":" + DoubleToString(accInfo.Equity(), 2) + ",";
    json += "\"daily_profit\":" + DoubleToString(dailyProfit, 2) + ",";
    json += "\"max_drawdown\":" + DoubleToString(maxDrawdown, 2) + ",";
    json += "\"total_trades\":" + IntegerToString(totalTrades) + ",";
    json += "\"winning_trades\":" + IntegerToString(winningTrades) + ",";
    
    json += "\"market_data\":[";
    int dataCount = MathMin(100, ArraySize(marketHistory)); 
    for(int i = ArraySize(marketHistory) - dataCount; i < ArraySize(marketHistory); i++)
    {
        if(i > ArraySize(marketHistory) - dataCount)
            json += ",";
        
        json += "{";
        json += "\"time\":\"" + TimeToString(marketHistory[i].time) + "\",";
        json += "\"open\":" + DoubleToString(marketHistory[i].open, 5) + ",";
        json += "\"high\":" + DoubleToString(marketHistory[i].high, 5) + ",";
        json += "\"low\":" + DoubleToString(marketHistory[i].low, 5) + ",";
        json += "\"close\":" + DoubleToString(marketHistory[i].close, 5) + ",";
        json += "\"volume\":" + IntegerToString(marketHistory[i].volume) + ",";
        json += "\"signal\":" + IntegerToString(marketHistory[i].signal) + ",";
        json += "\"result\":" + DoubleToString(marketHistory[i].result, 2) + ",";
        
        json += "\"indicators\":[";
        for(int j = 0; j < 20; j++)
        {
            if(j > 0) json += ",";
            json += DoubleToString(marketHistory[i].indicators[j], 5);
        }
        json += "]";
        json += "}";
    }
    json += "]";
    
    json += "}";
    return json;
}

//+------------------------------------------------------------------+
//| Отправка результатов сделок на сервер                           |
//+------------------------------------------------------------------+
void SendTradeResultToServer(string tradeId, double profit, bool isWin, int signal)
{
    if(StringLen(ServerURL) == 0)
        return;
    
    string jsonData = "{";
    jsonData += "\"trade_id\":\"" + tradeId + "\",";
    jsonData += "\"profit\":" + DoubleToString(profit, 2) + ",";
    jsonData += "\"is_win\":" + (isWin ? "true" : "false") + ",";
    jsonData += "\"signal\":" + IntegerToString(signal) + ",";
    jsonData += "\"timestamp\":\"" + TimeToString(TimeCurrent()) + "\",";
    jsonData += "\"symbol\":\"" + _Symbol + "\"";
    jsonData += "}";
    
    string headers = "Content-Type: application/json\r\n";
    headers += "Authorization: Bearer " + APIKey + "\r\n";
    
    char post[];
    StringToCharArray(jsonData, post, 0, StringLen(jsonData));
    
    char result[];
    string resultHeaders;
    
    string url = ServerURL + "/api/feedback";
    int httpResult = WebRequest("POST", url, headers, 5000, post, result, resultHeaders);
    
    if(httpResult == 200)
    {
        Print("Результат сделки отправлен на сервер: ", tradeId);
    }
    else
    {
        Print("Ошибка отправки результата сделки. Код: ", httpResult);
    }
}

//+------------------------------------------------------------------+
//| Получить предсказание от AI сервера                             |
//+------------------------------------------------------------------+
int GetAIPrediction()
{
    if(StringLen(ServerURL) == 0 || ArraySize(marketHistory) < 10)
        return 0;
    
    // Подготавливаем данные для отправки
    string jsonData = "{\"features\":[";
    int lastIndex = ArraySize(marketHistory) - 1;
    
    for(int i = 0; i < 20; i++)
    {
        if(i > 0) jsonData += ",";
        double normalizedValue = NormalizeValue(marketHistory[lastIndex].indicators[i], i);
        jsonData += DoubleToString(normalizedValue, 6);
    }
    jsonData += "],\"symbol\":\"" + _Symbol + "\"}";
    
    string headers = "Content-Type: application/json\r\n";
    headers += "Authorization: Bearer " + APIKey + "\r\n";
    
    char post[];
    StringToCharArray(jsonData, post, 0, StringLen(jsonData));
    
    char result[];
    string resultHeaders;
    
    string url = ServerURL + "/api/predict";
    int httpResult = WebRequest("POST", url, headers, 5000, post, result, resultHeaders);
    
    if(httpResult == 200)
    {
        string response = CharArrayToString(result);
        
        // Простой парсинг JSON ответа
        int predStart = StringFind(response, "\"prediction\":");
        if(predStart >= 0)
        {
            string predStr = StringSubstr(response, predStart + 13, 2);
            int prediction = (int)StringToInteger(predStr);
            
            // Преобразуем предсказание в торговый сигнал
            if(prediction == 2) return 1;   // BUY
            else if(prediction == 0) return -1; // SELL
            else return 0; // HOLD
        }
    }
    
    return 0; // Default HOLD
}

//+------------------------------------------------------------------+
//| Вспомогательные функции                                         |
//+------------------------------------------------------------------+

double NormalizeValue(double value, int indicatorIndex)
{
    switch(indicatorIndex)
    {
        case 3: return value / 100.0;  
        case 14: return value / 24.0;  
        case 15: return value / 7.0;   
        default: return MathMin(1.0, MathMax(0.0, (value + 1000) / 2000));  
    }
}

void AddToHistory(MarketData &data)
{
    int size = ArraySize(marketHistory);
    if(size >= LearningPeriod)
    {
        for(int i = 0; i < size - 1; i++)
            marketHistory[i] = marketHistory[i + 1];
        marketHistory[size - 1] = data;
    }
    else
    {
        ArrayResize(marketHistory, size + 1);
        marketHistory[size] = data;
    }
}

int GetMarketSession()
{
    MqlDateTime dt;
    TimeCurrent(dt);
    
    if(dt.hour >= 0 && dt.hour < 8) return 1;     
    else if(dt.hour >= 8 && dt.hour < 16) return 2; 
    else return 3;                                   
}

double CalculateVolatility(int period)
{
    if(period <= 0) return 0;
    
    double sum = 0;
    for(int i = 1; i <= period; i++)
    {
        double high = iHigh(_Symbol, PERIOD_CURRENT, i);
        double low = iLow(_Symbol, PERIOD_CURRENT, i);
        double close = iClose(_Symbol, PERIOD_CURRENT, i);
        sum += (high - low) / close;
    }
    return sum / period * 100;
}

double CalculateAverageSpread()
{
    static double avgSpread = 0;
    static int spreadCount = 0;
    
    double currentSpread = symInfo.Spread() * symInfo.Point();
    avgSpread = (avgSpread * spreadCount + currentSpread) / (spreadCount + 1);
    spreadCount++;
    
    return avgSpread;
}

void ManageOpenPositions()
{
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(posInfo.SelectByIndex(i) && posInfo.Magic() == MagicNumber)
        {
            double currentPrice = (posInfo.PositionType() == POSITION_TYPE_BUY) ? 
                                  symInfo.Bid() : symInfo.Ask();
            
            if(posInfo.PositionType() == POSITION_TYPE_BUY)
            {
                double newSL = currentPrice - StopLoss * symInfo.Point();
                if(newSL > posInfo.StopLoss())
                {
                    trade.PositionModify(posInfo.Ticket(), newSL, posInfo.TakeProfit());
                }
            }
            else
            {
                double newSL = currentPrice + StopLoss * symInfo.Point();
                if(newSL < posInfo.StopLoss())
                {
                    trade.PositionModify(posInfo.Ticket(), newSL, posInfo.TakeProfit());
                }
            }
        }
    }
}

void SaveAIData()
{
    string filename = "ai_weights_" + _Symbol + ".dat";
    int handle = FileOpen(filename, FILE_WRITE | FILE_BIN);
    
    if(handle != INVALID_HANDLE)
    {
        FileWriteStruct(handle, aiNetwork);
        FileClose(handle);
        Print("Данные ИИ сохранены в файл: ", filename);
    }
}

void LoadAIData()
{
    string filename = "ai_weights_" + _Symbol + ".dat";
    int handle = FileOpen(filename, FILE_READ | FILE_BIN);
    
    if(handle != INVALID_HANDLE)
    {
        FileReadStruct(handle, aiNetwork);
        FileClose(handle);
        Print("Данные ИИ загружены из файла: ", filename);
    }
    else
    {
        Print("Файл данных ИИ не найден, используются случайные веса");
    }
}

bool FileWrite(string filename, string data)
{
    int handle = FileOpen(filename, FILE_WRITE | FILE_TXT);
    if(handle != INVALID_HANDLE)
    {
        FileWriteString(handle, data);
        FileClose(handle);
        return true;
    }
    else
    {
        Print("Ошибка открытия файла для записи: ", filename);
        return false;
    }
}

//+------------------------------------------------------------------+
//| Добавить сделку в отслеживание                                  |
//+------------------------------------------------------------------+
void AddTradeTracking(string tradeId, double price, double lot, int signal)
{
    if(activeTradesCount < 10)
    {
        activeTrades[activeTradesCount].id = tradeId;
        activeTrades[activeTradesCount].openTime = TimeCurrent();
        activeTrades[activeTradesCount].openPrice = price;
        activeTrades[activeTradesCount].lot = lot;
        activeTrades[activeTradesCount].signal = signal;
        activeTrades[activeTradesCount].isActive = true;
        activeTradesCount++;
    }
}

//+------------------------------------------------------------------+
//| Обновить статус сделки                                          |
//+------------------------------------------------------------------+
void UpdateTradeStatus(string tradeId, double closePrice, bool isWin)
{
    for(int i = 0; i < activeTradesCount; i++)
    {
        if(activeTrades[i].id == tradeId && activeTrades[i].isActive)
        {
            double profit = 0;
            if(activeTrades[i].signal == 1) // BUY
                profit = (closePrice - activeTrades[i].openPrice) * activeTrades[i].lot * 100000;
            else if(activeTrades[i].signal == -1) // SELL
                profit = (activeTrades[i].openPrice - closePrice) * activeTrades[i].lot * 100000;
            
            // Send feedback using improved AI predictor
            if(aiPredictor != NULL)
            {
                if(!aiPredictor.SendFeedback(tradeId, profit, isWin))
                {
                    Print("Не удалось отправить feedback через AI predictor, используется резервный метод");
                    SendTradeResultToServer(tradeId, profit, isWin, activeTrades[i].signal);
                }
            }
            else
            {
                // Fallback to direct server communication
                SendTradeResultToServer(tradeId, profit, isWin, activeTrades[i].signal);
            }
            
            // Update statistics
            if(isWin) winningTrades++;
            dailyProfit += profit;
            
            // Mark trade as inactive
            activeTrades[i].isActive = false;
            
            Print("Сделка закрыта: ID=", tradeId, " Прибыль=", profit, " Успешная=", isWin);
            break;
        }
    }
}

