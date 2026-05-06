# 음성 비서 프로그램

# Streamlit 패키지 추가
import streamlit as st
# OpenAI 패키지 추가 (STT용 Whisper, GPT 답변용)
import openai
# 파일 삭제를 위한 패키지 추가
import os
# 시간 정보를 위한 패키지 추가
from datetime import datetime
# TTS 패키지 추가 (구글 Text-to-Speech)
from gtts import gTTS
# 음원 파일을 재생하기 위한 패키지 추가
import base64


##### 기능 구현 함수 #####
def STT(audio, apikey):
    """
    음성 → 텍스트 변환 (Speech-to-Text)
    audio: st.audio_input이 반환하는 UploadedFile 객체 (BytesIO 호환)
    """
    # 파일 저장 (UploadedFile은 .getvalue()로 bytes 추출 가능)
    filename = "input.wav"
    with open(filename, "wb") as f:
        f.write(audio.getvalue())

    # OpenAI Whisper 모델로 텍스트 추출
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
    """
    GPT 모델에 프롬프트를 보내고 답변을 받아오는 함수
    prompt: messages 리스트 ([{role, content}, ...])
    """
    client = openai.OpenAI(api_key=apikey)
    response = client.chat.completions.create(
        model=model,
        messages=prompt
    )
    gptResponse = response.choices[0].message.content
    return gptResponse


def TTS(response):
    """
    텍스트 → 음성 변환 후 자동 재생 (Text-to-Speech)
    """
    # gTTS를 활용하여 음성 파일 생성
    filename = "output.mp3"
    tts = gTTS(text=response, lang="ko")
    tts.save(filename)

    # 음원 파일 자동 재생 (HTML audio 태그 + base64 임베딩)
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
        page_title="호의 음성 비서 프로그램",
        layout="wide")

    # 제목
    st.header("호의 음성 비서 프로그램")

    # 구분선
    st.markdown("---")

    # 기본 설명
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
    # chat: 화면에 보여줄 채팅 기록 [(sender, time, message), ...]
    if "chat" not in st.session_state:
        st.session_state["chat"] = []

    # OPENAI_API: 사이드바에서 입력받은 API 키
    if "OPENAI_API" not in st.session_state:
        st.session_state["OPENAI_API"] = ""

    # messages: GPT API에 보낼 대화 컨텍스트 [{role, content}, ...]
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    # check_reset: 초기화 버튼 눌렀을 때 같은 rerun 안에서 STT 재호출 막는 플래그
    if "check_reset" not in st.session_state:
        st.session_state["check_reset"] = False

    # last_audio_hash: 동일한 오디오로 매번 STT 호출되는 것 방지용 해시값
    # (st.audio_input은 위젯이 살아있는 동안 같은 audio 객체를 계속 반환함)
    if "last_audio_hash" not in st.session_state:
        st.session_state["last_audio_hash"] = None

    # 사이드바 생성
    with st.sidebar:
        # OpenAI API 키 입력받기
        st.session_state["OPENAI_API"] = st.text_input(
            label="OPENAI API 키",
            placeholder="Enter Your API Key",
            value="",
            type="password"
        )

        st.markdown("---")

        # GPT 모델 선택
        model = st.radio(label="GPT 모델", options=["gpt-4", "gpt-3.5-turbo"])

        st.markdown("---")

        # 리셋 버튼 생성
        if st.button(label="초기화"):
            # 리셋 코드: 채팅 기록과 컨텍스트 모두 초기화
            st.session_state["chat"] = []
            st.session_state["messages"] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
            st.session_state["check_reset"] = True
            # 다음 녹음을 새로운 것으로 인식시키기 위해 해시도 초기화
            st.session_state["last_audio_hash"] = None

    # 기능 구현 공간
    col1, col2 = st.columns(2)

    with col1:
        # 왼쪽 영역 작성
        st.subheader("질문하기")
        # 음성 녹음 위젯 추가 (예제 3.10)
        # st.audio_input은 Streamlit 1.31+ 네이티브 위젯
        # 반환값: UploadedFile (녹음 안 됐으면 None)
        audio = st.audio_input("클릭하여 녹음하기")

    # 새 오디오인지 판별 (rerun마다 STT 중복 호출 방지)
    new_audio = False
    if audio is not None and not st.session_state["check_reset"]:
        # 오디오 bytes의 해시를 비교해서 이전과 다르면 새 녹음으로 판단
        audio_bytes = audio.getvalue()
        current_hash = hash(audio_bytes)
        if current_hash != st.session_state["last_audio_hash"]:
            new_audio = True
            st.session_state["last_audio_hash"] = current_hash

    # 새 녹음이 들어왔을 때만 STT → GPT 호출
    if new_audio:
        # API 키 가드 (키 없이 OpenAI 호출하면 에러나니까 미리 차단)
        if not st.session_state["OPENAI_API"]:
            st.error("사이드바에 OpenAI API 키를 먼저 입력해주세요.")
            st.stop()

        # 음성 재생 (녹음한 내용 사용자에게 들려주기)
        with col1:
            st.audio(audio)

        # 음원 파일에서 텍스트 추출
        question = STT(audio, st.session_state["OPENAI_API"])

        # 채팅을 시각화하기 위해 질문 내용 저장
        now = datetime.now().strftime("%H:%M")
        st.session_state["chat"].append(("user", now, question))
        # GPT 모델에 넣을 프롬프트를 위해 질문 내용 저장
        st.session_state["messages"].append({"role": "user", "content": question})

        # ChatGPT에게 답변 얻기
        response = ask_gpt(
            st.session_state["messages"],
            model,
            st.session_state["OPENAI_API"]
        )

        # GPT 답변은 "assistant" role로 저장 (OpenAI 스펙 준수)
        st.session_state["messages"].append({"role": "assistant", "content": response})

        # 채팅 시각화를 위한 답변 내용 저장
        now = datetime.now().strftime("%H:%M")
        st.session_state["chat"].append(("bot", now, response))

    with col2:
        # 오른쪽 영역 작성
        st.subheader("질문/답변")

        # 채팅 형식으로 시각화하기 (예제 3.13)
        # 녹음 여부와 무관하게 누적된 채팅 기록은 항상 표시
        for sender, time, message in st.session_state["chat"]:
            if sender == "user":
                # 사용자 말풍선 (왼쪽 정렬, 파란색)
                st.write(
                    f'<div style="display:flex;align-items:center;">'
                    f'<div style="background-color:#007AFF;color:white;border-radius:12px;'
                    f'padding:8px 12px;margin-right:8px;">{message}</div>'
                    f'<div style="font-size:0.8rem;color:gray;">{time}</div></div>',
                    unsafe_allow_html=True
                )
                st.write("")
            else:
                # 봇 말풍선 (오른쪽 정렬, 회색)
                st.write(
                    f'<div style="display:flex;align-items:center;justify-content:flex-end;">'
                    f'<div style="background-color:lightgray;border-radius:12px;'
                    f'padding:8px 12px;margin-left:8px;">{message}</div>'
                    f'<div style="font-size:0.8rem;color:gray;">{time}</div></div>',
                    unsafe_allow_html=True
                )
                st.write("")

        # gTTS를 활용하여 음성 파일 생성 및 재생
        # 새 녹음+답변일 때만 TTS 실행
        if new_audio and len(st.session_state["chat"]) > 0:
            # 가장 최근 봇 답변 찾기
            last_bot_msg = next(
                (m for s, t, m in reversed(st.session_state["chat"]) if s == "bot"),
                None
            )
            if last_bot_msg:
                TTS(last_bot_msg)

    # reset 플래그 해제 (한 번 리셋한 후 다음 녹음부터 다시 처리되도록)
    if st.session_state["check_reset"]:
        st.session_state["check_reset"] = False


if __name__ == "__main__":
    main()


# 실행 명령: streamlit run ch03_voicebot7_commented.py
# 사전 설치: pip install --upgrade streamlit openai gtts



