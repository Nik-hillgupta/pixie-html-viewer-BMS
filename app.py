import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd
import base64
import re
from urllib.parse import unquote

st.set_page_config(page_title="BMS HTML Parser", layout="wide")
st.title("📄 BookMyShow HTML Parser")

uploaded_file = st.file_uploader("Upload the HTML (.txt) file exported from BookMyShow", type=["txt", "html"])

@st.cache_data
def parse_bms_html(text):
    soup = BeautifulSoup(text, "html.parser")
    cards = soup.find_all("a", class_=re.compile("sc-.*-11"))

    events = []
    for card in cards:
        try:
            text_blocks = card.find_all("div", class_="sc-7o7nez-0")
            texts = [el.get_text(strip=True) for el in text_blocks if el.get_text(strip=True)]

            promoted = False
            if texts and texts[0].strip().upper() == "PROMOTED":
                promoted = True
                texts = texts[1:]  # remove PROMOTED from list

            name = texts[0] if texts else ""
            venue = texts[-3] if len(texts) >= 3 else ""
            category = texts[-2] if len(texts) >= 2 else ""
            price = texts[-1] if texts else ""

            if not price or not (re.search(r"\u20b9|\d+\s*onwards", price) or "free" in price.lower()):
                price = ""

            img_tag = card.find("img")
            raw_url = img_tag["src"] if img_tag else ""
            decoded_date = ""
            match = re.search(r"ie-([^,]+)", raw_url)
            if match:
                base64_encoded = match.group(1)
                try:
                    decoded_date = base64.b64decode(unquote(base64_encoded)).decode("utf-8")
                except:
                    decoded_date = ""

            link = card.get("href", "")
            if not link.startswith("http"):
                link = "https://in.bookmyshow.com" + link

            events.append({
                "Event Name": name.strip(),
                "Venue": venue.strip(),
                "Category": category.strip(),
                "Price": price.strip(),
                "Date": decoded_date.strip(),
                "Promoted": "Yes" if promoted else "No",
                "Link": link.strip()
            })
        except Exception:
            continue

    return pd.DataFrame(events)

if uploaded_file:
    html = uploaded_file.read().decode("utf-8")
    df = parse_bms_html(html)

    st.success(f"✅ Extracted {len(df)} events.")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV", data=csv, file_name="bms_events.csv", mime="text/csv")