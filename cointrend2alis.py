from pytrends.request import TrendReq
import urllib.request
import json
import time
import datetime
import random
import sys
from warrant.aws_srp import AWSSRP

URL_BINANCE = 'https://api.binance.com/api/v3/exchangeInfo'

SIZE_PRINT_LIMIT = 5
doc_GOOGLE_TRENDS_URL = 'https://trends.google.co.jp/trends/explore?geo=JP&q='

DEBUG_LIMIT = 10

class alisClient:
    URL_SERVER = 'https://alis.to/api/'
    POOL_ID = 'ap-northeast-1_HNT0fUj4J'
    POOL_REGION = 'ap-northeast-1'
    CLIENT_ID = '2gri5iuukve302i4ghclh6p5rg'

    headers = ''

    def Post(self, title, doc, tag):
        url = self.URL_SERVER + '/me/articles/drafts'
        body = {"title":title, "body": doc, "overview": tag}
        json_data = json.dumps(body).encode("utf-8")

        ret = self.__req("POST", url, json_data)
        return ret['article_id']

    def Publish(article_id):
        url = self.URL_SERVER + '/me/articles/' + article_id + '/drafts/publish'
        self.__req("PUT", url)

    def __init__(self, user, pwd):
        self.__auth(user, pwd)

    def __auth(self, user, pwd):
        aws = AWSSRP(username=user, password=pwd, pool_id=self.POOL_ID, client_id=self.CLIENT_ID, pool_region=self.POOL_REGION)
        id_token = aws.authenticate_user()['AuthenticationResult']['IdToken']
        self.headers = {'Authorization': id_token}


    def __req(self, method, url, data):
        time.sleep(1)
        request = urllib.request.Request(url, data=data, method=method, headers=self.headers)
        with urllib.request.urlopen(request) as response:
            return json.load(response)

def die(msg):
    print(msg, file=sys.stderr)
    exit(1)

def GetGoogleTrend(word, st, et):
    fmt = '%Y-%m-%dT%H'
    wait = 1
    tf_start = st.strftime(fmt)
    tf_end = et.strftime(fmt)

    pytrend = TrendReq(hl='ja-jp',tz=540)
    kw_list = [symbol]
    pytrend.build_payload(kw_list=kw_list, timeframe=tf_start + ' ' + tf_end, geo="JP")
    df = pytrend.interest_over_time()

    v_len = len(df.values)
    if v_len < 1:
        time.sleep(wait)
        return {'symbol':symbol, 'rates':[], 'sum':0, 'avg':0, 'last':0}

    rates = [df.values[v_len - 1], df.values[v_len - 2], df.values[v_len - 3]]
    v_sum = 0
    v_last = 0
    for rate in rates:
        v_sum += rate[0]
        v_last = rate[0]

    time.sleep(wait)
    return {'symbol':symbol, 'rates':rates, 'sum':v_sum, 'avg':v_sum / len(rates), 'last':v_last}

def GetBinanceList():
    symbols = []
    try:
        res = urllib.request.urlopen(URL_BINANCE)
        data = json.loads(res.read().decode('utf-8'))

        ret_symbols = data['symbols']
        for symbol in ret_symbols:
            symbols.append(symbol['baseAsset'])
    except urllib.error.HTTPError as e:
        print('HTTPError: ', e, file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print('JSONDecodeError: ', e, file=sys.stderr)
        return []
    return sorted(list(set(symbols)))


if __name__ == '__main__':
    if len(sys.argv) < 3:
        die("usage: python3 cointrend2alis.py <your email> <your password>")
    uname = sys.argv[1]
    pwd = sys.argv[2]


    t_end = datetime.datetime.now() - datetime.timedelta(hours=10)
    t_7days_ago = t_end - datetime.timedelta(days=7)

    """
    trends = []
    no_trends = []
    cnt = 0
    for symbol in GetBinanceList():
        if cnt > DEBUG_LIMIT:
            break
        cnt++

        trend = GetGoogleTrend(symbol, t_7days_ago, t_end)
        if len(trend['rates']) < 1:
            no_trends.append(trend)
            continue
        trends.append(trend)
    trends = sorted(trends, key=lambda x: x['avg'], reverse=True)
    no_trends = sorted(no_trends, key=lambda x: x['symbol'], reverse=False)



    cnt = 0
    for trend in trends:
        if SIZE_PRINT_LIMIT < cnt:
            break
        cnt+=1
        print('symbol: ' + trend['symbol'])
        print('url: ' + doc_GOOGLE_TRENDS_URL + trend['symbol'])
        print('avg: ' + str(trend['avg']))

    print("no trend:" + str(no_trends))
    """
    fmt = '%Y/%m/%d %H時台'
    t_str_st = t_7days_ago.strftime(fmt)
    t_str_et = t_end.strftime(fmt)
    doc = """
<p>こんにちは。hinoshiba の <a href="https://github.com/hinoshiba/cointrend">bot</a>です。</p>
<p>本記事は、BINANCEで利用できる、暗号資産名を、<a href="https://trends.google.co.jp/trends/?geo=JP">Googleトレンド(日本の範囲)</a>で検索し、日本人の興味が上昇している暗号資産名をレポートする記事です。</p>
<p>今回の記事では、""" + t_str_st + """から""" + t_str_et + """の間に日本で上昇した暗号資産名をレポートしています</p>
<h2>ランキング (上位5つ)</h2>
<h2>トレンド に乗っていない通貨名</h2>
<h2>トレンドには意味があるのか。</h2>
<p>暗号資産の取引も、多数決ゲームと言われることがあるように、世間の注目度を追いかけることも大切です。</p>
<p>その判断材料の1つとして、検索トレンドが利用できるかと思っています。</p>
<p>1例を出すと、2021/04/14 に、IOST が急上昇したイベントがありました。<br> その1週間前である 2021/04/06 - 2021/04/13 をGoogleトレンドで検索していただくとわかるように、注目度が上がっています。</p>
<p>このことから、検索トレンドが情報している暗号資産名は、今後動きのある通貨である可能性を判断する材料の1つとして使えることがわかると思います。</p>
<h2>本活動を支援してくれる場合</h2>
<p>どの記事でも良いのでAlis投げてください</p>
<h2>注意事項や連絡</h2>
<p> - 本記事を参考にいただくのは自己責任です</p>
<p> - BINANCE取引所から一覧を取得しています。対象通貨を活用する場合、<a href="https://www.binance.com/ja/register?ref=XV62ZYI2">BINANCEへ登録し 5%の手数料を獲得</a>をしてみてください</p>
    """
    ac = alisClient(uname, pwd)
    article_id = ac.Post("test", doc, "")
    print(article_id)
    #ac.Publish(article_id)


