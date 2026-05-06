# 내가 만드는 음성 비서 프로그램

import streamlit as st
import openai
import os
from datetime import datetime
from gtts import gTTS
import base64


##### 기능 구현 함수 #####
def STT(audio, apikey):
    """
    audio: st.audio_input이 반환하는 UploadedFile (BytesIO 호환)
    """
    filename = "input.wav"
    # UploadedFile은 .getvalue()로 bytes 추출 가능
    with open(filename, "wb") as f:
        f.write(audio.getvalue())

    with open(filename, "rb") as audio_file:
        client = openai.OpenAI(api_key=apikey)
        respons = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    os.remove(filename)
    return respons.text


def ask_gpt(prompt, model, apikey):
    client = openai.OpenAI(api_key=apikey)
    response = client.chat.completions.create(
        model=model,
        messages=prompt
    )
    return response.choices[0].message.content


def TTS(response):
    filename = "output.mp3"
    tts = gTTS(text=response, lang="ko")
    tts.save(filename)

    with open(filename, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="True">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)
    os.remove(filename)


##### 메인 함수 #####
def main():
    SYSTEM_PROMPT = (
        "You are a thoughtful assistant. "
        "Respond to all input in 25 words and answer in korea"
    )

    st.set_page_config(page_title="호의 음성 비서 프로그램", layout="wide")
    st.header("호의 음성 비서 프로그램")
    st.markdown("---")

    with st.expander("음성비서 프로그램에 관하여", expanded=True):
        st.write(
            """
        - 음성 비서 프로그램의 UI는 스트림릿을 활용하여 만들었습니다.
        - 녹음은 Streamlit 네이티브 위젯 st.audio_input을 사용합니다 (Streamlit 1.31+).
        - STT(Speech-To-Text)는 OpenAI의 Whisper AI를 활용하였습니다.
        - 답변은 OpenAI의 GPT 모델을 활용하였습니다.
        - TTS(Text-To-Speech)는 구글의 Google Translate TTS를 활용하였습니다.
        """
        )

    # session state 초기화
    if "chat" not in st.session_state:
        st.session_state["chat"] = []
    if "OPENAI_API" not in st.session_state:
        st.session_state["OPENAI_API"] = ""
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
    if "check_reset" not in st.session_state:
        st.session_state["check_reset"] = False
    # 같은 오디오로 중복 STT 방지용 해시
    if "last_audio_hash" not in st.session_state:
        st.session_state["last_audio_hash"] = None

    # 사이드바
    with st.sidebar:
        st.session_state["OPENAI_API"] = st.text_input(
            label="OPENAI API 키",
            placeholder="Enter Your API Key",
            value="",
            type="password"
        )
        st.markdown("---")
        model = st.radio(label="GPT 모델", options=["gpt-4", "gpt-3.5-turbo"])
        st.markdown("---")
        if st.button(label="초기화"):
            st.session_state["chat"] = []
            st.session_state["messages"] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
            st.session_state["check_reset"] = True
            st.session_state["last_audio_hash"] = None

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("질문하기")
        # ✅ 네이티브 녹음 위젯 — 외부 패키지 불필요, ffmpeg 불필요
        audio = st.audio_input("클릭하여 녹음하기")

    # 새 오디오인지 판별 (같은 녹음으로 매번 STT 호출하는 거 방지)
    new_audio = False
    if audio is not None and not st.session_state["check_reset"]:
        audio_bytes = audio.getvalue()
        current_hash = hash(audio_bytes)
        if current_hash != st.session_state["last_audio_hash"]:
            new_audio = True
            st.session_state["last_audio_hash"] = current_hash

    if new_audio:
        if not st.session_state["OPENAI_API"]:
            st.error("사이드바에 OpenAI API 키를 먼저 입력해주세요.")
            st.stop()

        with col1:
            st.audio(audio)

        # STT
        question = STT(audio, st.session_state["OPENAI_API"])
        now = datetime.now().strftime("%H:%M")
        st.session_state["chat"].append(("user", now, question))
        st.session_state["messages"].append({"role": "user", "content": question})

        # GPT 답변
        response = ask_gpt(
            st.session_state["messages"],
            model,
            st.session_state["OPENAI_API"]
        )
        st.session_state["messages"].append({"role": "assistant", "content": response})
        now = datetime.now().strftime("%H:%M")
        st.session_state["chat"].append(("bot", now, response))

    with col2:
        st.subheader("질문/답변")
        # 채팅 시각화 (녹음 여부와 무관하게 항상 표시)
        for sender, time, message in st.session_state["chat"]:
            if sender == "user":
                st.write(
                    f'<div style="display:flex;align-items:center;">'
                    f'<div style="background-color:#007AFF;color:white;border-radius:12px;'
                    f'padding:8px 12px;margin-right:8px;">{message}</div>'
                    f'<div style="font-size:0.8rem;color:gray;">{time}</div></div>',
                    unsafe_allow_html=True
                )
                st.write("")
            else:
                st.write(
                    f'<div style="display:flex;align-items:center;justify-content:flex-end;">'
                    f'<div style="background-color:lightgray;border-radius:12px;'
                    f'padding:8px 12px;margin-left:8px;">{message}</div>'
                    f'<div style="font-size:0.8rem;color:gray;">{time}</div></div>',
                    unsafe_allow_html=True
                )
                st.write("")

        # TTS는 새로운 답변일 때만
        if new_audio and len(st.session_state["chat"]) > 0:
            last_bot_msg = next(
                (m for s, t, m in reversed(st.session_state["chat"]) if s == "bot"),
                None
            )
            if last_bot_msg:
                TTS(last_bot_msg)

    # reset 플래그 해제 (한 번 리셋한 후 다시 받기 위함)
    if st.session_state["check_reset"]:
        st.session_state["check_reset"] = False


if __name__ == "__main__":
    main()


# streamlit run ch03_voicebot6.py
# 사전 요구: pip install --upgrade streamlit openai gtts

