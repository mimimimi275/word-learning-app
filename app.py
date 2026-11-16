import streamlit as st
import sqlite3
import csv
from datetime import datetime, timedelta
from core.sm2 import calculate_next_review
from core.ai_generator import generate_passage
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("LLM_API_KEY")
DB_PATH = "data/word_db.sqlite"
CSV_PATH = "data/cet6_words.csv"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS words
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, word TEXT, pos TEXT, definition TEXT, next_review DATE, interval INTEGER, ease FLOAT, stage INTEGER, learned_date DATE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS passages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, word_list TEXT, content TEXT, trans TEXT, create_time DATE)''')
    conn.commit()
    conn.close()

def import_words():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            c.execute("SELECT * FROM words WHERE word=?", (row["word"],))
            if not c.fetchone():
                c.execute("INSERT INTO words (word, pos, definition, next_review, interval, ease, stage) VALUES (?,?,?, ?,0,2.5,0)",
                          (row["word"], row["pos"], row["definition"], datetime.now().date().isoformat()))
    conn.commit()
    conn.close()

def get_new_words(count=20):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM words WHERE learned_date IS NULL LIMIT ?", (count,))
    res = c.fetchall()
    conn.close()
    return res

def get_review_words():
    today = datetime.now().date().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM words WHERE next_review <= ? AND learned_date IS NOT NULL", (today,))
    res = c.fetchall()
    conn.close()
    return res

def update_word(word_id, quality):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT interval, ease, stage FROM words WHERE id=?", (word_id,))
    interval, ease, stage = c.fetchone()
    next_review, new_interval, new_ease, new_stage = calculate_next_review(quality, interval, ease, stage)
    c.execute('''UPDATE words SET next_review=?, interval=?, ease=?, stage=?, learned_date=COALESCE(learned_date, ?) WHERE id=?''',
              (next_review, new_interval, new_ease, new_stage, datetime.now().date().isoformat(), word_id))
    conn.commit()
    conn.close()

def save_passage(word_list, content, trans):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO passages (word_list, content, trans, create_time) VALUES (?,?,?,?)",
              (",".join(word_list), content, trans, datetime.now().date().isoformat()))
    conn.commit()
    conn.close()

init_db()
st.set_page_config(page_title="六级背词", layout="wide")
st.title("六级单词｜词入短文背诵")
new_count = st.sidebar.slider("每日新词数量", 5, 50, 20)
page = st.sidebar.radio("页面", ["背单词", "生成短文", "历史短文"])

if page == "背单词":
    tab1, tab2 = st.tabs(["复习旧词", "学习新词"])
    with tab1:
        review_list = get_review_words()
        if len(review_list) == 0:
            st.info("今日没有需要复习的单词")
        else:
            w = review_list[0]
            st.subheader(w[1])
            st.write(f"{w[2]}｜{w[3]}")
            col1,col2,col3 = st.columns(3)
            with col1:
                if st.button("❌ 不认识"):
                    update_word(w[0], 0)
                    st.rerun()
            with col2:
                if st.button("🤔 模糊"):
                    update_word(w[0], 2)
                    st.rerun()
            with col3:
                if st.button("✅ 认识"):
                    update_word(w[0], 3)
                    st.rerun()
            st.stop()
    with tab2:
        new_list = get_new_words(new_count)
        if len(new_list) == 0:
            st.info("新词已经学完啦")
        else:
            w = new_list[0]
            st.subheader(w[1])
            st.write(f"{w[2]}｜{w[3]}")
            col1,col2,col3 = st.columns(3)
            with col1:
                if st.button("❌ 不认识"):
                    update_word(w[0], 0)
                    st.rerun()
            with col2:
                if st.button("🤔 模糊"):
                    update_word(w[0], 2)
                    st.rerun()
            with col3:
                if st.button("✅ 认识"):
                    update_word(w[0], 3)
                    st.rerun()
            st.stop()

if page == "生成短文":
    st.subheader("用今日新词生成六级阅读短文")
    today_words = get_new_words(new_count)
    word_text_list = [i[1] for i in today_words]
    st.write("今日新词：", " ".join(word_text_list))
    if st.button("生成短文（需要API Key）"):
        if not API_KEY:
            st.error("请在.env配置LLM_API_KEY")
        else:
            eng, chn = generate_passage(word_text_list, API_KEY)
            st.markdown("### 英文短文（目标词高亮）")
            st.markdown(eng)
            st.markdown("### 中文翻译")
            st.write(chn)
            save_passage(word_text_list, eng, chn)

if page == "历史短文":
    conn = sqlite3.connect(DB_PATH)
    data = conn.execute("SELECT * FROM passages ORDER BY id DESC").fetchall()
    conn.close()
    for item in data:
        with st.expander(f"{item[4]} 单词：{item[1]}"):
            st.markdown(item[2])
            st.write(item[3])
