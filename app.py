import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json

# ページ設定
st.set_page_config(
    page_title="12条点検Webアプリ",
    layout="wide",
    initial_sidebar_state="expanded"
)

# セッション状態の初期化
if 'temp_data' not in st.session_state:
    st.session_state.temp_data = {}

# マスターデータの読み込み
def load_deterioration_master():
    try:
        df = pd.read_csv("deterioration_master.csv")
        return df.groupby('部位')['劣化内容'].apply(list).to_dict()
    except FileNotFoundError:
        return {}

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

    # 建物外観セクション
    st.subheader("建物外観")
    crack = st.radio("外壁のひび割れ", ["なし", "小", "中", "大"], key="crack")
    paint = st.radio("塗装状態", ["良好", "劣化", "剥がれ"], key="paint")
    rust = st.radio("鉄部の錆", ["なし", "小", "中", "大"], key="rust")
    
    # 建物内部セクション
    st.subheader("建物内部")
    water_leak = st.radio("雨漏り", ["なし", "あり"], key="water_leak")
    interior_crack = st.radio("内壁のひび割れ", ["なし", "小", "中", "大"], key="interior_crack")
    
    # 劣化内容セクション
    st.subheader("劣化内容")
    deterioration_master = load_deterioration_master()
    
    # 部位ごとの劣化内容選択
    for location_type, deteriorations in deterioration_master.items():
        st.write(f"【{location_type}】")
        selected_deteriorations = st.multiselect(
            f"{location_type}の劣化内容",
            options=deteriorations,
            key=f"deterioration_{location_type}"
        )
        
        # 選択された劣化がある場合、詳細入力を表示
        for det in selected_deteriorations:
            col1, col2 = st.columns(2)
            with col1:
                st.text_input(f"{det}の程度", key=f"degree_{det}")
            with col2:
                st.text_input(f"{det}の場所", key=f"location_{det}")

    # その他の劣化内容
    st.write("【その他の劣化】")
    other_deterioration = st.text_area(
        "上記以外の劣化内容",
        key="other_deterioration"
    )

    # 備考
    comments = st.text_area("備考", key="comments")

    # 写真アップロード
    st.subheader("写真アップロード")
    uploaded_files = st.file_uploader("点検箇所の写真", accept_multiple_files=True)

    # 保存処理
    if st.button("保存", type="primary"):
        if not location or not inspector:
            st.error("現場IDと点検者名は必須です。")
        else:
            # 劣化データの収集
            deterioration_data = {}
            for loc in deterioration_master.keys():
                selected = st.session_state.get(f"deterioration_{loc}", [])
                details = {}
                for det in selected:
                    details[det] = {
                        "程度": st.session_state.get(f"degree_{det}", ""),
                        "場所": st.session_state.get(f"location_{det}", "")
                    }
                deterioration_data[loc] = details

            # 写真の保存
            photo_paths = []
            if uploaded_files:
                for file in uploaded_files:
                    file_path = f"photos/{location}_{date}_{file.name}"
                    os.makedirs("photos", exist_ok=True)
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())
                    photo_paths.append(file_path)

            # 基本データとの結合
            base_data = {
                "点検日": date,
                "現場ID": location,
                "点検者名": inspector,
                "天候": weather,
                "劣化データ": json.dumps(deterioration_data, ensure_ascii=False),
                "その他劣化": other_deterioration,
                "写真": ",".join(photo_paths),
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
