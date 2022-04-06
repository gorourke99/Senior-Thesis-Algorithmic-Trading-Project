# Thesis Bot v7



"""
Note: Some code is based on code in the Github repository of the programmer who made the
API for Alpaca. Other code, particularly code for pandas, was found in from various
programming blogs. Most of it is fairly obvious, routine things. Just to be safe for academic
integrity purposes, I cited them where they occur.

I also had to use code that was written by an Alpaca customer service representative on the
Alpaca forums. This code was to fix a bug with the Alpaca api crashing the program if a user
with a free subscription (like the account this program uses) tries to get data.
It is cited where it occurs. I'll also put it here:

https://forum.alpaca.markets/t/error-python-v2-api-get-bars-end-is-too-late-for-subscription/4966/11

Finally, I kept in some print statements I had for debug purposes because it makes it
clear what the program is doing. I decided it would be helpful for the user.
"""

import alpaca_trade_api
import pandas as pd # This is a typical convention for pandas
import ta
import datetime
import time
from alpaca_trade_api.rest import TimeFrame
import csv
import math
import pytz


#Code API Credentials
apiKey = "PKSKIZ3BCZ0PX721HDDH"
apiSecret = "Vafw1jz3ReKIFRp7avegY90QIdDVfAwXvxng1H0U"
alpacaApiBaseURL = "https://paper-api.alpaca.markets"




class Network:
    """
    This is based on the code found here in the Alpaca trade
    documentation

    https://github.com/alpacahq/alpaca-trade-api-python/blob/master/examples/long-short.py

    """


    def __init__(self):
        self.alpaca = alpaca_trade_api.REST(apiKey, apiSecret, alpacaApiBaseURL, 'v2')

    def cancelOrders(self):
        #From Long-short lines 39-41 (modified)

        orders = self.alpaca.list_orders(status="open")
        for order in orders:
            self.alpaca.cancel_order(order.id)


class MACDADX:
    """
    This receives a pandas dataframe containing a time frame
    and a close price. These two data points are the minimum required
    for the strategy to work.

    MACDADX accepts the dataframe, adds the MACD and ADX indicators to
    it, and then evaluates them in order to generate a trade signal.

    Currently, it only says whether or not you should do a long
    or no trade at all
    """

    def __init__(self):
        pass

    def evaluate(self, df, strategy):

        """
        Strategy indices:
            0 = ADX
            1 = SMA50
            2 = SMA26
            3 = EMA20
            4 = SMA12
        """

        #Add the technical analysis data to the dataframe
        df["MACD"] = ta.trend.macd(df["close"])
        # df["MACD_diff"] = ta.trend.macd(df["close"])
        df["MACD_signal"] = ta.trend.macd_signal(df["close"])

        if strategy[0]:
            df["ADX"] = ta.trend.adx(df["high"], df["low"], df["close"])

        if strategy[1]:
            df["SMA50"] = ta.trend.sma_indicator(df["close"], window=50)

        if strategy[2]:
            df["SMA26"] = ta.trend.sma_indicator(df["close"], window=26)

        if strategy[3]:
            df["EMA20"] = ta.trend.ema_indicator(df["close"], window=20)

        if strategy[4]:
            df["SMA12"] = ta.trend.sma_indicator(df["close"], window=12)


        # This line takes the last candle in the data frame and moves it
        # to a seperate variable. Note: the iloc method is a way of searching
        # the dataframes

        #for the way the MACD is calculated, both the current candle
        # and the previous candle are needed

        previousdataPoint = df.iloc[-2]
        dataPoint = df.iloc[-1]


        #Make sure a trade is not placed on a Nan value
        if math.isnan(dataPoint["close"]) == True:
            print("Attempted NaN Trade")

            return False


        """
        What these these two lines of code do is see if the MACD
        signal line has just crossed over the MACD. This is considered
        a buy signal for MACD.
        """
        #Is the Signal line higher than the MACD Line?
        if dataPoint["MACD_signal"] <= dataPoint["MACD"]:
            return False

        # Did the signal line just cross over?
        if previousdataPoint["MACD_signal"] > previousdataPoint["MACD"]:
            return False


        #  Check if the ADX is enabled, if so, is it above 25?

        if strategy[0]:
            if dataPoint["ADX"] <= 25:
                return False
        

        # Similar code for each of the following indicators
        if strategy[1]:
            if dataPoint["close"] < dataPoint["SMA50"]:
                return False

        if strategy[2]:
            if dataPoint["close"] < dataPoint["SMA26"]:
                return False

        if strategy[3]:
            if dataPoint["close"] < dataPoint["EMA20"]:
                return False

        if strategy[4]:
            if dataPoint["close"] < dataPoint["SMA12"]:
                return False

        return True


    def determineQuantity(self, portfolioCapital, currentPrice, portfolioPercentage=.20, partialBuys=False):

        """
        This method tries to invest 10% of the portfolio's capital into the asset
        in question.

        If it can't, it checks to see if partial buys are allowed. If so, it uses 10% of its
        capital to buy the asset.

        If it cannot even do this, it returns a 0.
        """

        tradeCapital = portfolioCapital * portfolioPercentage

        sharesToBuy = tradeCapital / currentPrice

        if sharesToBuy < 1 and partialBuys:

            return 0

        else:

            return math.floor(sharesToBuy) #Cuts off percentages






class simulatedTrade():
    """
    This object simulates a trade for the backtesting program.

    """


    def __init__(self, entryPrice, quantity, stopLoss, takeProfit, side="Long"):
        self.entryPrice = entryPrice
        self.quantity = quantity
        self.stopLoss = stopLoss
        self.takeProfit = takeProfit
        self.side = side



    def evaluate(self, currentPrice):

        """
        This function evaluates whether or not a simulated trade has triggered
        its stop loss/take profit. Note that for the realtime, this logic is
        handled by Alpaca.

        I have support for short positions here, though this version of the bot
        does not use short positions.
        """

        #If the position is a long
        if self.side == "Long":
            if currentPrice <= self.stopLoss or currentPrice >= self.takeProfit:

                return True

            else:

                return False

        #If the position is a short
        else:
            if currentPrice >= self.stopLoss or currentPrice <= self.takeProfit:

                return True

            else:

                return False


    def close(self, currentPrice):
        self.currentPrice = currentPrice

        #If the position is long
        if self.side == "Long":
            self.profitLoss = (self.currentPrice * self.quantity) - (self.entryPrice * self.quantity)

        #If the position is short
        else:
            self.profitLoss = (self.entryPrice * self.quantity) - (self.currentPrice * self.quantity)


    def setExitPrice(self, exitPrice):
        self.exitPrice = exitPrice
        



class Controller:

    def importData(self, file):
        # import market data from a CSV
        # From here:
        # https://careerkarma.com/blog/python-csv-module/

        with open(file, "r") as f:

            contents = csv.reader(f)

            openPrice = []
            high = []
            low = []
            close = []


            for i in contents:
                #print("i: ", i)
                openPrice.append(i[1])
                high.append(i[2])
                low.append(i[3])
                close.append(i[4])

            # Add an index. This is because the index is
            # easier to work with than the timestamps in most
            # CSV files
            length = len(high) + 1
            index = range(1, length)


            # This method of creating a dictionary and using it to
            # populate a pandas data frame is found here:
            # https://datatofish.com/create-pandas-dataframe/

            priceData = {
            'index' : length,
            'open' : openPrice,
            'high' : high,
            'low' : low,
            'close' : close
            }

            marketData = pd.DataFrame(priceData, columns=['index', 'open', 'high', 'low', 'close'])
            marketData = marketData[1:]

            marketData.dropna(inplace=True)


            marketData = marketData.astype(float)
            #This code found here: https://datatofish.com/convert-string-to-float-dataframe/

            return marketData








    def backTest(self, file, strategy):

        # Start the strategy object (Network is superfluous here)
        self.MACD = MACDADX()

        #Statistics for Paper Trading
        #start with $1,000,000 of capital.
        currentCapital = 1000000
        startingCapital = 1000000
        profitLoss = 0
        profitLossPercentage = 0
        trades = []

        #Get market data
        marketData = self.importData(file)

        #print(marketData.iloc[1:20])

        """
        Real time list that simulates the data the bot has access to at any given moment.
        It functionally works like a queue, scrolling through the marketData dataframe.
        """
        beginWindow = 1
        endWindow = 31
        iterations = 1


        realTimeData = marketData.iloc[beginWindow:endWindow]

        position = None



        while endWindow <= len(marketData) - 1:

            # Debug Print Statements
            print("Candle #", iterations)

            realTimeData = marketData.iloc[beginWindow:endWindow]
            currentPrice = realTimeData.iloc[(len(realTimeData)-1)][4] # Get the close price of the last candle

            # Debug Print Statements
            print("Current Price: ", currentPrice)


            # Check if there are open positions
            # if true, check if the stoploss or takeprofit has been met
            # if true, close the position and record it in the trades list
            if position != None:

                print("Position open this candle")

                sell = position.evaluate(currentPrice)

                if sell == True:

                    print("Position Closed")

                    position.close(currentPrice)
                    trades.append(position)

                    #Change Current Capital
                    currentCapital += position.profitLoss

                    position = None


            #Evaluate opening a new position
            else:

                openPosition = self.MACD.evaluate(realTimeData, strategy)

                if openPosition == True:

                    print("Position Opened")

                    """
                    stopLoss = currentPrice * .95
                    takeProfit = currentPrice * 1.05
                    """

                    #Default stoploss and take profit is 5% in either direction
                    stopLoss, takeProfit = self.getTakeProfitAndStopLoss(currentPrice)

                    #calculate the amount of shares to buy
                    quantity = self.MACD.determineQuantity(currentCapital, currentPrice)

                    if quantity == 0:
                        print("------------")
                        print("Bot ran out of money")
                        print("------------")
                        break

                    position = simulatedTrade(currentPrice, quantity, stopLoss, takeProfit)



            #Extra spacing
            print()

            beginWindow += 1
            endWindow += 1
            iterations += 1





        #Calculate profit/loss and winrate
        wins = 0
        losses = 0

        for x in trades:
            profitLoss += x.profitLoss

            # Winrate is a wins / total amount of trades.

            if x.profitLoss > 0:
                wins += 1

            else:
                losses += 1



        #Calculate Profit/Loss percentage and winrate
        profitLossPercentage = ((currentCapital / startingCapital) * 100) - 100
        winRate = wins / len(trades)


        #Print Results
        print("===========================")
        print("Back Test Results")
        print("===========================")



        print("Starting Capital: ", startingCapital)
        print("Current Capital: ", currentCapital)

        print("\nTrades: ", len(trades))

        print("\nTotal Profit/Loss: $", profitLoss)

        print("\nWin Rate: ", winRate)


        print("Profic/Loss Percentage: ", profitLossPercentage, "%")



    def getTakeProfitAndStopLoss(self, currentPrice, profitPercentage = .05, stopLossPercentage = .05):
        stopLoss = currentPrice * (1 - stopLossPercentage)
        takeProfit = currentPrice * profitPercentage

        return stopLoss, takeProfit


    def checkMarketOpen(self):

        """
        This code comes from the Alpaca API documentation
        for how to check whether the market is open. I modified
        it slightly for my program.

        See lines 86-95

        Source: https://github.com/alpacahq/alpaca-trade-api-python/blob/master/examples/long-short.py
        """

        isOpen = self.API.alpaca.get_clock().is_open

        print("isOpen: ", isOpen)

        if isOpen == False:

            clock = self.API.alpaca.get_clock()
            openingTime = clock.next_open.replace(tzinfo=datetime.timezone.utc).timestamp()
            currTime = clock.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
            timeToOpen = int((openingTime - currTime) / 60)
            print(str(timeToOpen) + " minutes til market open.")
            return False

        else:

            """
            Make sure it is 15 minutes after close (I did 16 just to be safe).
            Though the Alpaca representative's code did not contain this, my understanding
            of how Alpaca works has me pretty sure that the program would crash if you ran it between
            9:30 a.m. EST (Market open) and 9:45 am. The reason being is that there wouldn't be
            15 minutes of data to work with yet.
        
            If the market is open, check to see if its past 9:45 EST.
            """

            time = datetime.datetime.now()

            hour = time.hour
            minute = time.minute

            if int(hour) == 9 and int(minute) <= 45: #

                print("Market is open but its still too early to get")
                print("data for the program's Alpaca subscription.")

                return False


            return True





    def run(self, strategy):
        # Start Network and Strategy Objects
        self.API = Network()
        self.MACD = MACDADX()

        # Cancel all open orders
        self.API.cancelOrders()





        while True:


            #Make sure the market is open
            if self.checkMarketOpen() == False:

                print("Waiting 60 seconds.")
                time.sleep(60)
                continue

            marketData = self.buildDataStructure()


            # Check for orders. if there are, wait for them to be filled
            # Orders for this bot should be filled immediately. This is just in case.
            orders = self.API.alpaca.list_orders(status="open")
            positions = self.API.alpaca.list_positions()

            if len(orders) > 0:
                time.sleep(60)
                continue

            #Check for open positions. If there's an open position, wait for it to be closed
            elif len(positions) > 0:
                time.sleep(60)
                continue

            #If no positions are open
            else:

                #See if it should make a new trade
                evaluation = self.MACD.evaluate(marketData, strategy)
                print("Evaluation: ", evaluation)

                if evaluation == True:

                    currentPrice = marketData.iloc[-1]
                    stopLoss, takeProfit = self.getTakeProfitAndStopLoss(currentPrice)

                    #Note: Double check that this line actually works
                    accountBalance = self.API.get_account()


                    quantity = self.MACD.determineQuantity(accountBalance, currentPrice)


                    #submit order to API
                    self.API.alpaca.submit_order(
                        symbol='SPY',
                        side='buy',
                        type='market',
                        qty=str(quantity),
                        time_in_force='day',
                        order_class='bracket',
                        take_profit=dict(
                            limit_price=str(takeProfit),
                        ),
                        stop_loss=dict(
                            stop_price=str(stopLoss),
                            limit_price=str(stopLoss),
                        )
                    )

            time.sleep(60)






    def buildDataStructure(self):

        """
        Originally, I got an error. Apparently my Alpaca subscription does not
        allow the last 15 minutes of data. I Googled the problem and found a
        post from someone with my exact problem. Alpaca support forums.

        The this is the code I originally had:

        d = datetime.date.today()

        dataFrame = self.API.alpaca.get_bars("SPY", TimeFrame.Minute, d.isoformat(), d.isoformat(), limit=100, adjustment="raw").df

        The following code is copied almost verbatim from what was given by an Alpaca
        customer service representative. I implemented this at 6:00 on 5/10/21, after
        the market closed. This code gives an error, but I think that its because
        the market is closed. I added extra code so that this function only
        runs if the market is open.

        source: https://forum.alpaca.markets/t/error-python-v2-api-get-bars-end-is-too-late-for-subscription/4966/5

        """

        # Set a constant for UTC timezone
        UTC = pytz.timezone('UTC')

        # Get the current time, 15minutes, and 1 hour ago
        time_now = datetime.datetime.now(tz=UTC)
        time_15_min_ago = time_now - datetime.timedelta(minutes=15)
        time_1_hr_ago = time_now - datetime.timedelta(hours=1)

        # Get data from previous hour
        # If using the Free plan, the latest one can fetch is 15 minutes ago
        dataFrame = self.API.alpaca.get_bars('SPY', TimeFrame.Minute,
                               start=time_1_hr_ago.isoformat(),
                               end=time_15_min_ago.isoformat(),
                               adjustment='raw'
                               ).df



        return dataFrame





def main():
    controller = Controller()


    while True:

        print("===========================")
        print("Welcome to the Trading Bot")
        print("===========================")

        print("Select a Strategy")
        print("The strategy will automatically use MACD")

        choice = input("Use ADX (Y/N)?")
        if choice == "y" or choice == "Y":
            adx = True
        else:
            adx = False

        choice = input("Use 50 period SMA (Y/N)?")
        if choice == "y" or choice == "Y":
            sma50 = True
        else:
            sma50 = False

        choice = input("Use 26 period SMA (Y/N)?")
        if choice == "y" or choice == "Y":
            sma26 = True
        else:
            sma26 = False

        choice = input("Use 12 period SMA (Y/N)?")
        if choice == "y" or choice == "Y":
            sma12 = True
        else:
            sma12 = False

        choice = input("Use 20 period EMA (Y/N)?")
        if choice == "y" or choice == "Y":
            ema20 = True
        else:
            ema20 = False

        strategy = [adx, sma50, sma26, ema20, sma12]


        print("\nSelect a Mode")
        print("1 - Realtime with Alpaca")
        print("2 - Backtest")
        print("Q - Quit")

        selection = input("Choice: ")

        if selection == "1":
            controller.run(strategy)

        elif selection == "2":

            # This is the menu to select a dataset

            print("Select a Dataset")
            print("1 - Bitcoin Minute Candles")
            print("2 - AUD/USD Minute Candles 5/2/20 - 5/2/21")
            print("3 - EUR/USD Minute Candles 5/2/20 - 5/2/21")
            print("4 - SPY Daily 5/2/01 - 5/2/21")
            print("5 - SPY Daily 5/2/11 - 5/2/21")
            print("6 - SPY Daily 5/2/20 - 5/2/21")
            print("7 - SPY Minute 5/2/20 - 5/2/21")
            print("8 - TSLA Minute 5/2/20 - 5/2/21\n")

            choice = input("Please input a a choice: ")

            if choice == "1": file = "Dataset Bitcoin Excerpt One-Minute.csv"
            elif choice == "2": file = "Dataset AUD-USD 5.2.20 - 5.2.21 Minute.csv"
            elif choice == "3": file = "Dataset EUR-USD 5.2.20 - 5.2.21 Minute.csv"
            elif choice == "4": file = "Dataset SPY 5.2.01-5.2.21 Daily.csv"
            elif choice == "5": file = "Dataset SPY 5.2.11-5.2.21 Daily.csv"
            elif choice == "6": file = "Dataset SPY 5.2.20-5.2.21 Daily.csv"
            elif choice == "7": file = "Dataset SPY 5.2.20-5.2.21 Minute.csv"
            elif choice == "8": file = "Dataset TSLA 5.2.20-5.2.21 Minute.csv"






            # The timing function was taken from here
            # https://www.geeksforgeeks.org/python-measure-time-taken-by-program-to-execute/
            begin = time.time()
            controller.backTest(file, strategy)
            end = time.time()
            runTime = end - begin

            print("Backtest Run Time: ", runTime, "seconds.")

        elif selection == "Q" or selection == "q":
            break

        else:
            print("Error, Invalid Input")



if __name__ == "__main__":
    main()