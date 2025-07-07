# Streamlitアプリ：Amazon / 楽天 / Yahoo おむつ価格比較（単価ハイライト・3サイト統合・商品画像付き）

import streamlit as st
import requests
from bs4 import BeautifulSoup
import re

BRANDS = ["パンパース", "メリーズ", "グーン", "ムーニー", "GENKI", "ネピア"]

def calculate_price_per_unit(price, quantity):
    try:
        return round(price / quantity, 2)
    except ZeroDivisionError:
        return None

def detect_type(title):
    if "パンツ" in title:
        return "パンツ"
    elif "テープ" in title:
        return "テープ"
    else:
        return "不明"

def detect_brand(title):
    for brand in BRANDS:
        if brand.lower() in title.lower():
            return brand
    return "その他"

def extract_amazon_url(item):
    tag = item.select_one("a.a-link-normal.s-no-outline")
    return "https://www.amazon.co.jp" + tag["href"] if tag else ""

def extract_generic_url(item):
    tag = item.find("a", href=True)
    return tag["href"] if tag else ""

def extract_amazon_image(item):
    img = item.select_one("img.s-image")
    return img.get("src") if img else ""

def extract_generic_image(item):
    img = item.find("img")
    return img.get("src") if img else ""

def fetch_amazon(keyword):
    url = f"https://www.amazon.co.jp/s?k={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    results = []
    for item in soup.select("div.s-result-item"):
        title_tag = item.select_one("h2")
        price_tag = item.select_one("span.a-price-whole")
        if not title_tag or not price_tag:
            continue
        try:
            price = int(price_tag.text.replace(",", ""))
            title = title_tag.text.strip()
            match = re.search(r"(\d{2,3})枚", title)
            if not match:
                continue
            quantity = int(match.group(1))
            unit_price = calculate_price_per_unit(price, quantity)
            results.append({
                "site": "Amazon",
                "title": title,
                "price": price,
                "quantity": quantity,
                "unit_price": unit_price,
                "type": detect_type(title),
                "brand": detect_brand(title),
                "url": extract_amazon_url(item),
                "image": extract_amazon_image(item)
            })
        except:
            continue
    return results

def fetch_rakuten(keyword):
    url = f"https://search.rakuten.co.jp/search/mall/{keyword}/"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    results = []
    for item in soup.select("div.searchresultitem, div.dui-card"):
        title_tag = item.select_one("h2") or item.select_one(".title")
        price_tag = item.select_one("span.price") or item.select_one("span.medium")
        if not title_tag or not price_tag:
            continue
        try:
            title = title_tag.text.strip()
            price = int(re.sub(r"[^0-9]", "", price_tag.text))
            match = re.search(r"(\d{2,3})枚", title)
            if not match:
                continue
            quantity = int(match.group(1))
            unit_price = calculate_price_per_unit(price, quantity)
            results.append({
                "site": "楽天",
                "title": title,
                "price": price,
                "quantity": quantity,
                "unit_price": unit_price,
                "type": detect_type(title),
                "brand": detect_brand(title),
                "url": extract_generic_url(item),
                "image": extract_generic_image(item)
            })
        except:
            continue
    return results

def fetch_yahoo(keyword):
    url = f"https://shopping.yahoo.co.jp/search?p={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    results = []
    for item in soup.select(".SearchResults__items > div"):
        title_tag = item.select_one("a")
        price_tag = item.select_one("._Price__value")
        if not title_tag or not price_tag:
            continue
        try:
            title = title_tag.text.strip()
            price = int(re.sub(r"[^0-9]", "", price_tag.text))
            match = re.search(r"(\d{2,3})枚", title)
            if not match:
                continue
            quantity = int(match.group(1))
            unit_price = calculate_price_per_unit(price, quantity)
            results.append({
                "site": "Yahoo",
                "title": title,
                "price": price,
                "quantity": quantity,
                "unit_price": unit_price,
                "type": detect_type(title),
                "brand": detect_brand(title),
                "url": extract_generic_url(item),
                "image": extract_generic_image(item)
            })
        except:
            continue
    return results

# Streamlit UI
st.set_page_config(layout="wide")
st.title("おむつ価格比較：Amazon / 楽天 / Yahoo")

col1, col2, col3 = st.columns(3)
size = col1.selectbox("サイズ", ["新生児", "Sサイズ", "Mサイズ", "Lサイズ"])
type_filter = col2.radio("タイプ", ["すべて", "テープ", "パンツ"])
brand_filter = col3.selectbox("ブランド", ["すべて"] + BRANDS + ["その他"])

search_kw = f"おむつ {size}"
st.info(f"🔍 検索キーワード: {search_kw}")

with st.spinner("データ取得中..."):
    results = fetch_amazon(search_kw) + fetch_rakuten(search_kw) + fetch_yahoo(search_kw)

if type_filter != "すべて":
    results = [r for r in results if r["type"] == type_filter]
if brand_filter != "すべて":
    results = [r for r in results if r["brand"] == brand_filter]

if results:
    min_price = min(r["unit_price"] for r in results)
else:
    min_price = None

st.subheader("📋 結果一覧（単価順）")
results = sorted(results, key=lambda x: x["unit_price"])

for r in results:
    is_cheapest = (r["unit_price"] == min_price)
    st.markdown(f"### {'💡' if is_cheapest else ''} {r['title']}")
    cols = st.columns([1, 3])
    if r.get("image"):
        cols[0].image(r["image"], use_column_width=True)
    cols[1].markdown(f"- 🛍 サイト: {r['site']}  | ブランド: {r['brand']} | 種類: {r['type']}")
    cols[1].markdown(f"- 📦 {r['quantity']}枚 / 💰 {r['price']}円 → 🧮 {r['unit_price']}円/枚")
    if r["url"]:
        cols[1].markdown(f"[🔗 商品ページ]({r['url']})")
    st.markdown("---")

if not results:
    st.warning("条件に合う商品が見つかりませんでした。検索キーワードを見直してください。")
