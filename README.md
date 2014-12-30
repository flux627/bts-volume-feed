# Volume-Aware Price Feed


### What is this?

This is a price feed generator which calculates the average price of BTS exchange pairs based on volume at a per-trade basis, for use by BitShares delegates. The script is capable of sorting trades across multiple exchanges by their execution time, and then taking an average price of the most recent trades in a user-specified BTS amount window.


### Why was this made?

Current price feed implementations use spot prices, which are much more easily manipulated. Futher, they are arbitrarily weighing these exchange's spot prices, based on an average volume over 24 hours. By considering every trade at a set of exchanges, the place the exchange took place becomes irrelevant, and only the trade amount and time become important.


### How is this accomplished?

The script currently supports one current pair (BTS/CNY) on three exchanges (BTC38, Bter, Yunbi). Fortunately, all these exchanges have a public API for listing recent individual trades. Every 10 seconds, this script fetches, formats, combines, and sorts the data by time. It then runs through all the most recent trades, calculating the average price until the user-specified volume window is filled. If the last order pushes the total over this window, this last order is truncated, and the rest of the transactions are not included. The average price is displayed in the terminal, and saved to the `price.json` file. The trades used to calculate this are saved in the `trades.json` file.

If you start the script and on the initial iteration there is not enough volume across the exchanges to fill the volume window, no price feed will be output, and a partial `trades.json` file will be created. Every time new orders are detected, it will add to this file until the window is matched, at which point it will begin generating a price feed.

### Usage?

You can change the config settings at the top of the file, changing the `WINDOW`, as well as disable/enable the exchanges.

After you have changed these settings, you can simply run the script like this:

`$ python price_feed.py`

### Know issues?

* The Yunbi exchange's timestamp is not parsed correctly by the ISO8601 date parser, as it does not factor in the timezone offset. Additionally, it seems that their timestamps are off by 9 hours. For this reason, I have disabled the Yunbi exchange by default until I can confirm that this is indeed correct.
* When you stop running the script, and run it again after much time has passed, it is possible that it will use old trade information until they are pushed out by new orders.
* Queries to the APIs are not done exactly every 10 seconds, it is actually 10s + (time it takes to retrieve all data).


### Future plans?

The current code is only a proof-of-concept to guage interest in this kind of price feed. If there is indeed interest, the next steps are:

* Implement more exchange pairs (need to figure out rate-limiting from exchanges)
* Integration with bitshares RPC