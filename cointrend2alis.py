from pytrends.request import TrendReq
import urllib.request
import re
import json
import time
import datetime
import random
import sys
from warrant.aws_srp import AWSSRP

URL_BINANCE = 'https://api.binance.com/api/v3/exchangeInfo'

SIZE_PRINT_LIMIT = 5
doc_GOOGLE_TRENDS_URL = 'https://trends.google.co.jp/trends/explore?geo=JP&q='

class alisClient:
    URL_SERVER = 'https://alis.to/api/'
    POOL_ID = 'ap-northeast-1_HNT0fUj4J' #ref https://alis.to/yuuki/articles/3dy7jyv8vPBv
    POOL_REGION = 'ap-northeast-1' #ref https://alis.to/yuuki/articles/3dy7jyv8vPBv
    CLIENT_ID = '2gri5iuukve302i4ghclh6p5rg' #ref https://alis.to/yuuki/articles/3dy7jyv8vPBv

    headers = ''

    def Post(self, title, doc):
        url = self.URL_SERVER + '/me/articles/drafts'
        body = {"title":title, "body": doc, "overview": ""}
        json_data = json.dumps(body).encode("utf-8")

        ret = self.__req("POST", url, json_data)
        return ret['article_id']

    def Publish(self, article_id, topic, tags):
        url = self.URL_SERVER + '/me/articles/' + article_id + '/drafts/publish'
        body = {"topic":topic, "tags": tags}
        json_data = json.dumps(body).encode("utf-8")

        self.__req("PUT", url, json_data)

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
            try:
                return json.load(response)
            except:
                return

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
            name = symbol['baseAsset']
            if len(re.findall('UP|DOWN|BEAR|BULL', name)) == 1:
                if len(name) > 4:
                    continue
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

    trends = []
    no_trends = []

    b_symbols = GetBinanceList()
    cnt = 0
    size = len(b_symbols)
    for symbol in b_symbols:
        cnt+=1

        print('WIP ' + str(cnt) + ' / ' + str(size))
        trend = GetGoogleTrend(symbol, t_7days_ago, t_end)
        print(trend)

        if len(trend['rates']) < 1:
            no_trends.append(trend)
            continue
        trends.append(trend)
    trends = sorted(trends, key=lambda x: x['avg'], reverse=True)
    no_trends = sorted(no_trends, key=lambda x: x['symbol'], reverse=False)


    cnt = 0
    doc_rank_trends = ''
    for trend in trends:
        cnt+=1
        if SIZE_PRINT_LIMIT < cnt:
            break

        doc_rank_trends += '<h3>第 ' + str(cnt) + ' 位: ' + trend['symbol']
        doc_rank_trends += '(<a href="' + doc_GOOGLE_TRENDS_URL + trend['symbol'] + '">Googleトレンドで見る</a>)</h3>'
        doc_rank_trends += '<p>期間内最新3つの平均値: ' + str(trend['avg']) + '<br>'
        doc_rank_trends += '期間内最新値: ' + str(trend['last']) + '</p>'

    doc_no_trends = '<p>'
    for no_trend in no_trends:
        doc_no_trends += ' - ' + no_trend['symbol'] + '<br>'
    doc_no_trends += '</p>'

    fmt = '%Y/%m/%d %H時台'
    t_str_st = t_7days_ago.strftime(fmt)
    t_str_et = t_end.strftime(fmt)
    doc = """
<p>こんにちは。hinoshiba の <a href="https://github.com/hinoshiba/cointrend/blob/master/cointrend2alis.py">bot</a>です。</p>
<p>本記事は、BINANCEで利用できる、暗号資産名を、<a href="https://trends.google.co.jp/trends/?geo=JP">Googleトレンド(日本の範囲)</a>で検索し、日本人の興味が上昇している暗号資産名をレポートする記事です。</p>
<h2>本活動を支援してくれる場合</h2>
<p>どの記事でも良いのでAlis投げてください</p>
<h2>注意事項や連絡</h2>
<p> - 本記事を参考にいただくのは自己責任です<br>
 - 暗号資産の通貨名でトレンドを追いかけているので、同音異議語が引っかかる場合があります。(例: <a href="https://ja.wikipedia.org/wiki/ETC">ETC</a> と <a href="https://coinmarketcap.com/ja/currencies/ethereum-classic/">ETC(イーサリアムクラシック)</a>)<br>
 - 値は、0-100です。詳細は、<a href="https://trends.google.co.jp/trends/?geo=JP">Googleトレンド</a>をみてください<br>
 - BINANCE取引所の通貨名一覧を利用しています。<br>     取引がお得になる、<a href="https://www.binance.com/ja/register?ref=XV62ZYI2">BINANCEへ登録(5%の手数料を獲得)</a> リンクを貼り付けておくので、必要な方は利用ください</p>
<h2>注目度上昇ランキング (上位""" + str(SIZE_PRINT_LIMIT) + """つ)</h2>
<p>今回の記事は、 「""" + t_str_st + """から""" + t_str_et + """」を範囲として、<br>日本で上昇した暗号資産名をレポートしています</p>""" + doc_rank_trends + """
<h3>トレンド に値がなかった通貨名</h3>""" + doc_no_trends + """
<h3>今回のレポートは以上です。</h3>
<h2>トレンドには意味があるのか</h2>
<p>本記事の意味に関する文章です。毎回同じ文章なので、不要な人は読み飛ばしてください。</p>
<p>暗号資産の取引も、多数決ゲームと言われることがあるように、世間の注目度を追いかけることも大切です。</p>
<p>その判断材料の1つとして、検索トレンドが利用できるかと思っています。</p>
<p>例えば、2021/04/14 - 2021/04/15 に、IOST が急上昇したイベントがありました。<br> その1週間前までの <a href="https://trends.google.co.jp/trends/explore?date=2021-04-07%202021-04-14&geo=JP&q=IOST">2021/04/07 - 2021/04/14 をGoogleトレンドで検索</a> していただくとわかるように、注目度が上がっていることがわかります。</p>
<p>このことからも、検索トレンドが情報している暗号資産名は、今後動きのある通貨である可能性を判断する材料の1つとして使えることがわかると思います。</p>
<p>上がりそうなトレンドに乗るもよし、まだ注目が集まっていない"トレンドに値がなかった通貨名" に目を光らせておくのもよし。色々な思考材料に使えるのかと、個人的には夢を膨らませています。</p>
    """
    title = "暗号資産トレンド: " + t_str_et + "までの推移"
    ac = alisClient(uname, pwd)
    article_id = ac.Post(title, doc)
    ac.Publish(article_id, 'crypto', ['ビットコイン', 'bitcoin', '仮想通貨', 'トレンド'])
