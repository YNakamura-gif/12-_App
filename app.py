import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

# ページ設定
st.set_page_config(
    page_title="12条点検 Web アプリ",
    layout="wide",
    initial_sidebar_state="expanded"
)

# セッション状態の初期化
if 'temp_data' not in st.session_state:
    st.session_state.temp_data = {}

# マスターデータの読み込み
def load_deterioration_master():
    try:
        df = pd.read_csv("deterioration_master.csv", encoding="shift_jis")  # エンコーディングを指定
        return df
    except FileNotFoundError:
        st.error("deterioration_master.csv ファイルが見つかりません。")
        return pd.DataFrame()
    except UnicodeDecodeError:
        st.error("CSVファイルのエンコーディングが正しくありません。")
        return pd.DataFrame()
    except KeyError:
        st.error("CSVファイルに必要な列がありません。")
        return pd.DataFrame()

# アプリケーションのヘッダー
st.title("12条点検 Web アプリ")
st.write("このアプリは点検データを入力し、CSV出力するためのシステムです。")

# タブ作成
tab1, tab2 = st.tabs(["点検入力", "データ閲覧"])

with tab1:
    # 基本情報セクション
    st.subheader("基本情報")
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("点検日", key="date")
        inspector = st.text_input("点検者名", key="inspector")
    with col2:
        location = st.text_input("現場ID", key="location")
        weather = st.selectbox("天候", ["晴れ", "曇り", "雨"], key="weather")

    # 劣化内容セクション
    st.subheader("劣化内容")
    deterioration_master = load_deterioration_master()
    
    if not deterioration_master.empty:
        parts = deterioration_master['部位'].unique()
        deteriorations = deterioration_master['劣化内容'].unique()

        # 1から100までの番号を用意
        for i in range(1, 101):
            st.write(f"【劣化 {i}】")
            col1, col2 = st.columns(2)
            with col1:
                part = st.selectbox(f"部位 {i}", options=parts, key=f"part_{i}")
            with col2:
                deterioration = st.selectbox(f"劣化名 {i}", options=deteriorations, key=f"deterioration_{i}")

    # 備考
    comments = st.text_area("備考", key="comments")

    # 保存処理
    if st.button("保存", type="primary"):
        if not location or not inspector:
            st.error("現場IDと点検者名は必須です。")
        else:
            # 劣化データの収集
            deterioration_data = {}
            for i in range(1, 101):
                part = st.session_state.get(f"part_{i}", "")
                deterioration = st.session_state.get(f"deterioration_{i}", "")
                if part and deterioration:
                    deterioration_data[f"劣化 {i}"] = {
                        "部位": part,
                        "劣化名": deterioration
                    }

            # 基本データとの結合
            base_data = {
                "点検日": date,
                "現場ID": location,
                "点検者名": inspector,
                "天候": weather,
                "劣化データ": json.dumps(deterioration_data, ensure_ascii=False),
                "備考": comments
            }
            
            df = pd.DataFrame([base_data])
            
            # CSVファイルの保存
            csv_path = "data/inspection_data.csv"
            os.makedirs("data", exist_ok=True)
            
            if not os.path.exists(csv_path):
                df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            else:
                df.to_csv(csv_path, mode="a", index=False, header=False, encoding="utf-8-sig")
            
            st.success("データを保存しました！")

with tab2:
    st.subheader("保存済みデータ")
    try:
        saved_data = pd.read_csv("data/inspection_data.csv", encoding="utf-8-sig")
        
        # 検索フィルター
        col1, col2 = st.columns(2)
        with col1:
            search_date = st.date_input("日付で検索", key="search_date")
        with col2:
            search_location = st.text_input("現場IDで検索", key="search_location")
        
        # フィルタリング
        if search_location or search_date:
            filtered_data = saved_data[
                (saved_data["点検日"].astype(str).str.contains(str(search_date))) &
                (saved_data["現場ID"].str.contains(search_location, na=False))
            ]
            st.dataframe(filtered_data)
        else:
            st.dataframe(saved_data)
        
        # CSVダウンロード
        st.download_button(
            "CSVをダウンロード",
            saved_data.to_csv(index=False, encoding="utf-8-sig"),
            "点検データ.csv",
            "text/csv"
        )
    except FileNotFoundError:
        st.info("保存されたデータはありません。")

st.write("Hello World!")
