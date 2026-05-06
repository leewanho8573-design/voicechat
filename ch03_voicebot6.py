# 음성 비서 프로그램

import streamlit as st
# audiorecorder 패키지 추가
from audiorecorder import audiorecorder
# OpenAI 패키지 추가
import openai
# 파일 삭제를 위한 패키지 추가
import os
# 시간 정보를 위한 패키지 추가
from datetime import datetime
# TTS 패키지 추가
from gtts import gTTS
# 음원 파일을 재생하기 위한 패키지 추가
import base64


##### 기능 구현 함수 #####
def STT(audio, apikey):
    # 파일 저장
    filename = "input.mp3"
    audio.export(filename, format="mp3")

    # [FIX 5] with 문으로 핸들 누수 방지
    with open(filename, "rb") as audio_file:
        client = openai.OpenAI(api_key=apikey)
        respons = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    # 파일 삭제
    os.remove(filename)
    return respons.text


def ask_gpt(prompt, model, apikey):
    client = openai.OpenAI(api_key=apikey)
    response = client.chat.completions.create(
        model=model,
        messages=prompt)
    gptResponse = response.choices[0].message.content
    return gptResponse


def TTS(response):
    # gTTS를 활용하여 음성 파일 생성
    filename = "output.mp3"
    tts = gTTS(text=response, lang="ko")
    tts.save(filename)

    # 음원 파일 자동 재생
    with open(filename, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="True">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)
    # 파일 삭제
    os.remove(filename)


##### 메인 함수 #####
def main():
    # 시스템 프롬프트 상수화 (중복 제거)
    SYSTEM_PROMPT = (
        "You are a thoughtful assistant. "
        "Respond to all input in 25 words and answer in korea"
    )

    # 기본 설정
    st.set_page_config(
        page_title="음성 비서 프로그램",
        layout="wide")

    # 제목
    st.header("음성 비서 프로그램")

    # 구분선
    st.markdown("---")

    # 기본 설명
    with st.expander("음성비서 프로그램에 관하여", expanded=True):
        st.write(
        """
        - 음성 비서 프로그램의 UI는 스트림릿을 활용하여 만들었습니다.
        - STT(Speech-To-Text)는 OpenAI의 Whisper AI를 활용하였습니다.
        - 답변은 OpenAI의 GPT 모델을 활용하였습니다.
        - TTS(Text-To-Speech)는 구글의 Google Translate TTS를 활용하였습니다.
        """
        )

        st.markdown("")

    # session state 초기화 (예제 3.9)
    if "chat" not in st.session_state:
        st.session_state["chat"] = []

    if "OPENAI_API" not in st.session_state:
        st.session_state["OPENAI_API"] = ""

    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    # [FIX 1] 검사 키와 초기화 키를 일치시킴
    # 원본: if "check_audio" not in ... → 매번 check_reset이 False로 덮어써지는 버그
    if "check_reset" not in st.session_state:
        st.session_state["check_reset"] = False

    # 사이드바 생성
    with st.sidebar:
        # Open AI API 키 입력받기
        st.session_state["OPENAI_API"] = st.text_input(
            label="OPENAI API 키",
            placeholder="Enter Your API Key",
            value="",
            type="password")

        st.markdown("---")

        # [FIX 4] 최신 모델로 교체
        # 원본의 gpt-4, gpt-3.5-turbo도 호출은 되지만 비용/성능 면에서 비효율적
        model = st.radio(label="GPT 모델", options=["gpt-4o", "gpt-4o-mini"])

        st.markdown("---")

        # 리셋 버튼 생성
        if st.button(label="초기화"):
            # 리셋 코드
            st.session_state["chat"] = []
            st.session_state["messages"] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
            st.session_state["check_reset"] = True

    # 기능 구현 공간
    col1, col2 = st.columns(2)
    with col1:
        # 왼쪽 영역 작성
        st.subheader("질문하기")
        # 음성 녹음 아이콘 추가 (예제 3.10)
        audio = audiorecorder("클릭하여 녹음하기", "녹음 중...")

        # [FIX 3] duration_seconds 대신 len(audio) 사용 (ms 단위, 0보다 크면 녹음됨)
        if (len(audio) > 0) and (st.session_state["check_reset"] is False):
            # [FIX 6] API 키 가드
            if not st.session_state["OPENAI_API"]:
                st.error("사이드바에 OpenAI API 키를 먼저 입력해주세요.")
                st.stop()

            # 음성 재생
            st.audio(audio.export().read())
            # 음원 파일에서 텍스트 추출 (예제 3.11)
            question = STT(audio, st.session_state["OPENAI_API"])

            # 채팅을 시각화하기 위해 질문 내용 저장
            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"] = st.session_state["chat"] + [("user", now, question)]
            # GPT 모델에 넣을 프롬프트를 위해 질문 내용 저장
            st.session_state["messages"] = st.session_state["messages"] + [
                {"role": "user", "content": question}
            ]

    with col2:
        # 오른쪽 영역 작성
        st.subheader("질문/답변")
        # [FIX 3] duration_seconds 대신 len(audio) 사용
        if (len(audio) > 0) and (st.session_state["check_reset"] is False):
            # ChatGPT에게 답변 얻기 (예제 3.12)
            response = ask_gpt(
                st.session_state["messages"],
                model,
                st.session_state["OPENAI_API"]
            )

            # [FIX 2] GPT 답변은 "assistant" role로 저장 (OpenAI 스펙 준수)
            # 원본: "system" → 대화가 길어질수록 컨텍스트가 깨지는 문제 있음
            st.session_state["messages"] = st.session_state["messages"] + [
                {"role": "assistant", "content": response}
            ]

            # 채팅 시각화를 위한 답변 내용 저장
            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"] = st.session_state["chat"] + [("bot", now, response)]

            # 채팅 형식으로 시각화하기 (예제 3.13)
            for sender, time, message in st.session_state["chat"]:
                if sender == "user":
                    st.write(
                        f'<div style="display:flex;align-items:center;">'
                        f'<div style="background-color:#007AFF;color:white;border-radius:12px;'
                        f'padding:8px 12px;margin-right:8px;">{message}</div>'
                        f'<div style="font-size:0.8rem;color:gray;">{time}</div></div>',
                        unsafe_allow_html=True)
                    st.write("")
                else:
                    st.write(
                        f'<div style="display:flex;align-items:center;justify-content:flex-end;">'
                        f'<div style="background-color:lightgray;border-radius:12px;'
                        f'padding:8px 12px;margin-left:8px;">{message}</div>'
                        f'<div style="font-size:0.8rem;color:gray;">{time}</div></div>',
                        unsafe_allow_html=True)
                    st.write("")

            # gTTS를 활용하여 음성 파일 생성 및 재생 (예제 3.14)
            TTS(response)
        else:
            st.session_state["check_reset"] = False


if __name__ == "__main__":
    main()


# streamlit run ch03_voicebot6.py

