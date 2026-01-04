import streamlit as st
import google.generativeai as genai
import json
import os
import streamlit.components.v1 as components

# --- 設定 ---
# ページ設定
st.set_page_config(
    page_title="謝罪の王様 AI",
    page_icon="🙇",
    layout="centered",
menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "### 謝罪の王様 AI" 
    })
# st.secretsを利用し、環境変数から安全に取得する
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except KeyError:
    st.error("APIキーが設定されていません。StreamlitのSettings > Secretsで設定してください。")

# --- 定数・データ ---
# 【重要】以下の ad_html と url の中身を、ご自身のAmazonアソシエイトの広告コードと短縮URLに書き換えてください。
GIFT_RECOMMENDATIONS = {
    "High": [
        {
            "item": "【虎屋】小形羊羹 10本入",
            "desc": "【AI分析】この羊羹の持つ独特の『重さ』は、あなたが感じている責任の重さを物理的に相手に伝えるための装置です。言葉以上の説得力を持ちます。",
            "url": "https://amzn.to/YOUR_SHORT_URL",
            "ad_html": '<!-- 【虎屋】羊羹のAmazon広告HTMLコードをここに貼り付け -->'
        },
        {
            "item": "【千疋屋総本店】季節のフルーツ詰合",
            "desc": "【AI分析】最高級の果物が持つ『旬』の時間は、失われた信頼の回復の難しさと、だからこそ丁寧に向き合う誠意を表現します。",
            "url": "https://amzn.to/YOUR_SHORT_URL",
            "ad_html": '<!-- 【千疋屋】フルーツのAmazon広告HTMLコードをここに貼り付け -->'
        },
        {
            "item": "【松坂牛】カタログギフト券",
            "desc": "【AI分析】相手に『選ばせる』という行為を委ねることで、相手の意思を最大限に尊重する絶対的な敬意を示します。",
            "url": "https://amzn.to/YOUR_SHORT_URL",
            "ad_html": '<!-- 【松坂牛】カタログギフトのAmazon広告HTMLコードをここに貼り付け -->'
        }
    ],
    "Mid": [
        {
            "item": "【ヨックモック】シガール 30本入り",
            "desc": "【AI分析】個包装で分け合う前提のお菓子は、『個人的な問題で組織全体に迷惑をかけた』状況を円滑に収めるツールです。",
            "url": "https://amzn.to/YOUR_SHORT_URL",
            "ad_html": '<!-- 【ヨックモック】シガールのAmazon広告HTMLコードをここに貼り付け -->'
        },
        {
            "item": "【クラブハリエ】バームクーヘン",
            "desc": "【AI分析】幾重にも重なる年輪は、過ちを一度きりとせず、改善を『重ねていく』という決意の表明です。",
            "url": "https://amzn.to/YOUR_SHORT_URL",
            "ad_html": '<!-- 【クラブハリエ】バームクーヘンのAmazon広告HTMLコードをここに貼り付け -->'
        },
        {
            "item": "【銀座あけぼの】味の民藝",
            "desc": "【AI分析】米菓の持つ『伝統』と『格式』は、あなたの謝罪がその場しのぎでなく、常識に基づいていることを代弁します。",
            "url": "https://amzn.to/YOUR_SHORT_URL",
            "ad_html": '<!-- 【銀座あけぼの】味の民藝のAmazon広告HTMLコードをここに貼り付け -->'
        }
    ],
    "Low": [
        {
            "item": "【スターバックス】オリガミ コーヒーギフト",
            "desc": "【AI分析】一杯ずつ淹れる『手間』と『香り』が、相手のために心と時間を使った、というささやかな敬意を伝えます。",
            "url": "https://amzn.to/YOUR_SHORT_URL",
            "ad_html": '<!-- 【スターバックス】ギフトのAmazon広告HTMLコードをここに貼り付け -->'
        },
        {
            "item": "【ゴディバ】クッキー アソートメント",
            "desc": "【AI分析】誰もが知る高級ブランドの『名前』を借りることで、小さな謝罪でも相手を軽んじていない、という明確なメッセージになります。",
            "url": "https://amzn.to/YOUR_SHORT_URL",
            "ad_html": '<!-- 【ゴディバ】クッキーのAmazon広告HTMLコードをここに貼り付け -->'
        },
        {
            "item": "【今治タオル】ハンカチ",
            "desc": "【AI分析】涙や汗を拭うハンカチ本来の『機能』に、『清算』や『水に流す』という日本的な意味を乗せる選択です。",
            "url": "https://amzn.to/YOUR_SHORT_URL",
            "ad_html": '<!-- 【今治タオル】ハンカチのAmazon広告HTMLコードをここに貼り付け -->'
        }
    ]
}

# --- 関数 ---
def get_best_gift(score):
    """深刻度スコアに応じた最適な商品を返す"""
    # スコアが高いほど高単価なギフトを上位に
    if score >= 80:
        return GIFT_RECOMMENDATIONS["High"][0] # 虎屋など
    elif score >= 50:
        return GIFT_RECOMMENDATIONS["Mid"][0]  # ヨックモックなど
    else:
        return GIFT_RECOMMENDATIONS["Low"][0]  # スタバなど

def generate_apology(target_name, my_title, content, cause, prevention, user_stance, audience):
    """Gemini APIを呼び出して謝罪文と分析データを生成する"""
    
    # 立場に応じたペルソナ設定
    stance_personas = {
        "真面目な新人": "あなたは入社1年目の真面目な新人です。謙虚さと真摯な姿勢を重視し、丁寧すぎるくらいの言葉遣いを心がけています。学びたいという意欲が伝わるように表現します。",
        "ベテラン中堅": "あなたは経験豊富な中堅社員です。冷静沈着で、事実を客観的に伝えつつも、責任感のある態度を示します。感情的にならず、解決志向のアプローチを重視します。",
        "管理職": "あなたは管理職として、チーム全体の責任を負う立場です。部下のミスも自分の責任として受け止め、組織的な再発防止策を提案します。大局的な視点から対応します。",
        "部下を守る立場": "あなたは部下を守る立場の上司です。部下のミスを自分の指導不足として受け止め、部下の成長機会と捉えます。部下を過度に責めず、チームとしての改善を提案します。",
        "個人的なミス": "あなたは個人的なミスを犯した状況です。過度に深刻になりすぎず、誠実さと前向きな姿勢で対応します。相手に気を使わせない配慮も示します。"
    }
    
    persona = stance_personas.get(user_stance, stance_personas["真面目な新人"])
    
    prompt = f"""
    {persona}
    
    以下のユーザー入力に基づき、謝罪文の作成と状況分析を行ってください。
    
    # ユーザー入力
    - 謝罪の対象: {audience}
    - 相手: {target_name}
    - 自分の役職: {my_title}
    - ユーザーの立場: {user_stance}
    - ミスの内容（本音含む）: {content}
    - 原因: {cause}
    - 再発防止策: {prevention}

    # 指示
    1. **状況の深刻度分析**: 入力内容から、事態の深刻度を「0（軽微）〜100（致命的）」の数値で判定し、その理由を簡潔に述べてください。
    2. **メール作成**: {user_stance}の立場と、謝罪の対象が「{audience}」であることを強く意識したトーンで、相手に送る誠実なメール文面を作成してください。社外向けはより丁寧で形式的に、社内向けは簡潔かつ具体的にするなど、明確な差をつけてください。
    3. **始末書作成**: 社内規定を意識した正式な始末書を作成してください。
    4. **マナー解説（言い訳排除のポイント）**: ユーザーの入力（特にミスの内容や原因）を、どのように「大人の言葉」に変換したか、どの部分の「言い訳」を排除したか、{user_stance}の視点と「{audience}」という対象者を考慮して解説してください。

    # 出力形式 (JSON)
    必ず以下のJSON形式のみで出力してください。Markdownのcode blockは不要です。
    {{
        "severity_score": 0から100の数値（整数）,
        "severity_reason": "深刻度の理由",
        "email_text": "メール本文",
        "shimatsusho_text": "始末書本文",
        "manner_explanation": "マナー解説と変換ポイント"
    }}
    """

    model = genai.GenerativeModel('gemini-2.5-flash')
    # JSONモードを強制するための設定（プロンプトでも指示しているが念のため）
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    return json.loads(response.text)

def add_copy_button(text_to_copy, button_text="クリップボードにコピー"):

    """クリップボードにコピーするボタンを追加する"""

    # ユニークなIDを生成（同一セッションで複数ボタンを配置するため）

    import uuid

    button_id = str(uuid.uuid4())

    

    # HTMLとJavaScriptを組み合わせる

    components.html(f"""

        <script>

        function copyToClipboard_{button_id}() {{

            const text = `{text_to_copy.replace("`", "\\`")}`;

            navigator.clipboard.writeText(text).then(function() {{

                const button = document.getElementById('copyBtn_{button_id}');

                button.innerText = 'コピーしました！';

                setTimeout(() => {{ button.innerText = '{button_text}'; }}, 2000);

            }}, function(err) {{

                console.error('Could not copy text: ', err);

            }});

        }}

        </script>

        <button id="copyBtn_{button_id}" onclick="copyToClipboard_{button_id}()">{button_text}</button>

    """, height=50)





# --- UI構築 ---



st.title("🙇 謝罪の王様 AI")

st.markdown("##### 言い訳を「誠意」に変換。ビジネス危機管理ツール")



# 安心設計の明示

st.info("🔒 **安心設計**: 入力されたデータはサーバーに保存されず、AI生成後に即座に破棄されます。")



# 入力フォーム

with st.form("apology_form", enter_to_submit=False):

    col1, col2 = st.columns(2)

    with col1:

        target_name = st.text_input("謝る相手（例：営業部 佐藤部長）")

        my_title = st.text_input("自分の役職（例：営業一課 係長）")

    with col2:

        # B2B/B2Cの切り替え

        audience = st.selectbox(

            "謝罪の対象",

            ["社外（顧客向け）", "社内向け"],

            help="相手が社外の顧客か、社内の人間かを選択してください。マナーや表現が変わります。"

        )

        # ユーザーの立場選択

        user_stance = st.selectbox(

            "あなたの立場・スタイル",

            ["真面目な新人", "ベテラン中堅", "管理職", "部下を守る立場", "個人的なミス"],

            help="謝罪のトーンや表現をあなたの立場に合わせて調整します"

        )

    

    content = st.text_area("ミスの内容・状況（「実は相手が悪い」等の本音も書いてOK）", height=100)

    cause = st.text_input("原因（例：確認不足、連携ミス）")

    prevention = st.text_input("再発防止策（例：ダブルチェックの徹底）")

    

    submitted = st.form_submit_button("謝罪文を生成する", use_container_width=True)



# 生成処理

if submitted:

    if not api_key or api_key == "YOUR_API_KEY_HERE":

        st.error("APIキーが設定されていません。")

    elif not content:

        st.warning("ミスの内容を入力してください。")

    else:

        with st.spinner("AIが状況を分析し、最適な言葉を選んでいます..."):

            try:

                result = generate_apology(target_name, my_title, content, cause, prevention, user_stance, audience)

                

                # --- 結果表示 ---

                

                # 1. 深刻度分析とマナー解説

                st.subheader("🔍 状況分析とマナー解説")

                

                # 深刻度スコア表示

                score = result.get("severity_score", 50)

                if score >= 80:

                    severity_key = "High"

                elif score >= 50:

                    severity_key = "Mid"

                else:

                    severity_key = "Low"

                

                st.metric(label="深刻度スコア", value=f"{score} / 100")

                st.caption(result.get("severity_reason"))

                

                # マナー解説（言い訳排除ポイント）

                with st.expander("💡 なぜこの表現になったのか？（プロの視点）", expanded=True):

                    st.write(result.get("manner_explanation"))



                st.divider()



                # 2. 生成されたドキュメント

                st.subheader("📝 生成された謝罪文")

                tab1, tab2 = st.tabs(["メール文面", "始末書"])

                

                with tab1:

                    email_text = result.get("email_text", "")

                    st.code(email_text, language="text")

                    add_copy_button(email_text)

                    

                with tab2:

                    shimatsusho_text = result.get("shimatsusho_text", "")

                    st.code(shimatsusho_text, language="text")

                    add_copy_button(shimatsusho_text)

                

                st.divider()



                # 3. マネタイズ（お詫びの品レコメンド）

                st.subheader("🎁 推奨されるお詫びの品")

                rec_gift = get_best_gift(score)

                st.warning(f"今回のケース（深刻度: {severity_key}）では、手ぶらでの訪問はリスクがあります。")

                

                st.markdown(f"**推奨:** {rec_gift['item']}")

                st.info(rec_gift['desc']) # 理由を強調表示



                # HTMLバナーを表示（画像もリンクもここに含まれる）

                if "ad_html" in rec_gift and rec_gift["ad_html"].strip().startswith('<iframe'):

                    components.html(rec_gift["ad_html"], height=260)

                else:

                    st.warning("現在、商品バナーが設定されていません。")



            except Exception as e:

                st.error(f"エラーが発生しました: {e}")



st.divider()

st.markdown("""

<div style="font-size: 0.8em; color: gray; text-align: center;">

    免責事項: 本ツールが生成した文章は、AIによって作成された参考情報です。生成された内容の正確性、完全性、適切性を保証するものではありません。本ツールの使用によって生じたいかなる損害やトラブルについても、開発者は一切の責任を負いません。最終的な判断と責任は、使用者自身にあります。

</div>

""", unsafe_allow_html=True)
