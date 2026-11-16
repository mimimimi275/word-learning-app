from openai import OpenAI

def generate_passage(word_list, api_key):
    words_str = ",".join(word_list)
    prompt = f"""
你是六级阅读出题老师，写一篇120-180词英文短文，六级难度，主题贴近大学生热点。
必须自然用上全部单词：{words_str}
每个目标单词用**单词**标记高亮。
输出格式：
英文短文
---
中文翻译
不要童话风格，句子地道。生成后检查，不能漏掉任何一个单词。
"""
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role":"user", "content":prompt}],
        temperature=0.6
    )
    res = resp.choices[0].message.content
    eng, chn = res.split("---")
    return eng.strip(), chn.strip()
