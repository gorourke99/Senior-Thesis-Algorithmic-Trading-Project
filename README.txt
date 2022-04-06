Jerry O'Rourke

Senior Thesis Project

May 10, 2021

Hi Dr. Coleman,

Contained within this file is my project and a number of datasets. I also included.
The results from my backtesting. I decided to include some instructions about
how to use the bot.

=================
1 - Installation 
=================

The following Python libraries must be installed for the program to work. They can
all be installed using pip by going to the command terminal on Windows and typing
"pip install [library name]."

1. alpaca_trade_api
2. pandas
3. ta


==================
2 - Usage
==================

Upon start up, the program will prompt the user to choose a strategy. It will present
the user with a choice of indicators to use. It is only recommended to say yes or no
to one indicator and ADX. Note that each one will increase the runtime of the program.

It will then ask you if you want to run it in real time mode or in test mode. Note
that real time mode won't display much. Most of the testing in this program was in
backtesting mode.

If you select real time mode, it will request data from the Alpaca servers and display
some information to the terminal. Note that due to not having a premium subscription,
the program makes decisions based on 15 minute old market data. Note that the program
will not try to make trades from 15 minutes after market hours until market close
(9:30 a.m. EST open/9:45 a.m. EST - 4 p.m.).

If you select backtesting mode, it will prompt you to choose a dataset. I recommend
using either the bitcoin or the SPY Daily 5/2/20 - 5/2/21 dataset because these are the 
fasted. Other datasets will take several minutes to run. Sometimes the backtesting
will cause Pandas to put a warning to the terminal. Apparently it does not exactly
like the way I implemented some of my indicators. The backtesting program still
works as intended however.

If you want to test a large dataset, the program runs faster if you simply click on 
the script file and run it in the Windows terminal rather than running it in an
IDE.

Note that for backtesting to function properly, the datasets must be in the same directory
as the program.
