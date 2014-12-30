import requests
import json
import time
import dateutil.parser as iso8601
from operator import itemgetter

######## CONFIG ########

# Trade-depth window for calculating price
WINDOW = 250000

# Enable / Disable exchanges from calculation
BTC38_ACTIVE = True
BTER_ACTIVE  = True
YUNBI_ACTIVE = False

########################

def get_new_trades():
    apis = {
            "btc38" : "http://api.btc38.com/v1/trades.php?mk_type=cny&c=bts",
            "bter"  : "http://data.bter.com/api/1/trade/bts_cny",
            "yunbi" : "https://yunbi.com/api/v2/trades.json?market=btsxcny",
        }

    headers = {
                'content-type' : 'application/json',
                'User-Agent'   : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100101 Firefox/22.0'
            }


    all_trades_unsorted = []

    if BTC38_ACTIVE == True:
        print "Getting btc38 data..."
        btc38_result = requests.get(url=apis["btc38"], headers=headers).json()
        # Fix btc38 data
        for trade in btc38_result:
            trade["tid"] = "btc38_" + str(trade["tid"])
        all_trades_unsorted += btc38_result

    if BTER_ACTIVE == True:
        print "Getting bter data..."
        bter_result = requests.get(url=apis["bter"], headers=headers).json()["data"]
        # Fix bter data
        for trade in bter_result:
            trade["date"] = int(trade["date"])
            trade["price"] = float(trade["price"])
            trade["amount"] = float(trade["amount"])
            trade["tid"] = "bter_" + trade["tid"]
        all_trades_unsorted += bter_result

    if YUNBI_ACTIVE == True:
        print "Getting yunbi data..."
        yunbi_result = requests.get(url=apis["yunbi"], headers=headers).json()
        # Fix yunbi data
        for trade in yunbi_result:
            # Time parser does not see timezone (18000)
            # Additionally, Yunbi's server time seems to be off by 9 hours (32400)
            trade["date"] = int(time.mktime(iso8601.parse(trade["created_at"]).timetuple())) - 18000 - 32400
            trade["amount"] = float(trade.pop("volume"))
            trade["price"] = float(trade["price"])
            trade["tid"] = "yunbi_" + str(trade["id"])
        all_trades_unsorted += yunbi_result

    # Merge and sort
    all_trades_sorted = sorted(all_trades_unsorted, key=itemgetter("date"), reverse=True)

    # Prune extra data
    for trade in all_trades_sorted:
        for key in trade.keys():
            if key != 'date' and key != 'amount' and key != 'price' and key != 'tid':
                trade.pop(key, None)

    return all_trades_sorted

def load_saved_trades():
    with open("trades.json", "a+") as saved_trades_file:
        saved_trades_file.seek(0)
        try:
            saved_trades = json.load(saved_trades_file)
            # print "Loaded {} trades from trades.json".format(len(saved_trades))
        except ValueError:
            # print "No trades file found; 'trades.json' created."
            saved_trades = []
        return saved_trades

def merge_trades(saved_trades, new_trades):
    merged = saved_trades
    merged = [x for x in saved_trades if not "partial" in x.keys()]
    add_count = 0
    for trade in new_trades:
        if trade not in saved_trades:
            merged += [trade]
            add_count += 1
    merged_sorted = sorted(merged, key=itemgetter("date"), reverse=True)
    # print "Added {} new trades".format(add_count)
    return merged_sorted

def trim_excess(trades, window=WINDOW):
    trimmed = []
    total = 0
    for trade in trades:
        if total + trade['amount'] < WINDOW:
            total += trade['amount']
            trimmed += [trade]
        else:
            remainder = WINDOW - total
            trade["partial"] = True
            trade["amount"] = remainder
            trimmed += [trade]
            break
    total_removed = len(trades) - len(trimmed)

    trimmed_sorted = sorted(trimmed, key=itemgetter("date"), reverse=True)

    # print "{} trades trimmed".format(total_removed)
    return trimmed_sorted

def save_trades(trades):
    with open("trades.json", "w") as saved_trades_file:
        json.dump(trades, saved_trades_file)
    # print "Saved {} trades to trades.json".format(len(trades))

def get_price(trades):
    running_worth = 0
    running_total = 0
    for trade in trades:
        running_worth += trade["amount"] * trade["price"]
        running_total += trade["amount"]
    return [running_worth,running_total]

def feed_price(totals):
    if totals[1] + .1 >= WINDOW:
        price = totals[0] / totals[1]
        with open('price.json', 'w') as price_file:
            price_file.write('[{}]'.format(price))
        print price
        return price
    else:
        print "Not enough trade volume recorded! {} / {}".format(totals[1],WINDOW)
        return None

def run():
    new_trades = get_new_trades()
    saved_trades = load_saved_trades()
    merged_trades = merge_trades(saved_trades, new_trades)
    trimmed_trades = trim_excess(merged_trades)
    save_trades(trimmed_trades)
    totals = get_price(trimmed_trades)
    feed_price(totals)

while True:
    run()
    time.sleep(10)
