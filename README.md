[README (1).md](https://github.com/user-attachments/files/27545239/README.1.md)
# 🎙️ 호의 음성 비서 프로그램

Streamlit 기반 한국어 음성 비서 앱. 음성 입력 → GPT 답변 → 음성 출력까지 end-to-end로 동작한다.

---

## 🛠️ 기술 스택

| 역할 | 기술 |
|------|------|
| UI 프레임워크 | Streamlit 1.31+ |
| STT (음성 → 텍스트) | OpenAI Whisper (`whisper-1`) |
| 답변 생성 | OpenAI GPT (`gpt-4` / `gpt-3.5-turbo`) |
| TTS (텍스트 → 음성) | Google Translate TTS (`gTTS`) |

---

## 📦 설치

```bash
pip install streamlit openai gtts
```

> Streamlit **1.31 이상** 필요 (`st.audio_input` 위젯 사용)

---

## 🚀 실행

```bash
streamlit run ch03_voicebot6.py
```

---

## ⚙️ 사용 방법

1. 사이드바에 **OpenAI API 키** 입력
2. GPT 모델 선택 (`gpt-4` 또는 `gpt-3.5-turbo`)
3. 왼쪽 패널의 마이크 버튼을 눌러 **녹음**
4. 자동으로 STT → GPT → TTS 순서로 처리됨
5. 오른쪽 패널에서 채팅 기록 확인 + 답변 음성 자동 재생
6. **초기화** 버튼으로 대화 기록 전체 리셋

---

## 📁 프로젝트 구조

```
ch03_voicebot6.py   # 메인 애플리케이션 (단일 파일)
input.wav           # STT 처리 중 임시 생성 (자동 삭제)
output.mp3          # TTS 처리 중 임시 생성 (자동 삭제)
```

---

## 🔑 주요 함수

| 함수 | 설명 |
|------|------|
| `STT(audio, apikey)` | 녹음된 오디오를 Whisper로 텍스트 변환 |
| `ask_gpt(prompt, model, apikey)` | GPT 모델에 대화 컨텍스트 전송 후 답변 반환 |
| `TTS(response)` | gTTS로 텍스트를 음성 변환 후 브라우저 자동 재생 |

---

## ⚠️ 주의사항

- OpenAI API 키가 없으면 STT/GPT 기능 동작 안 함
- GPT 답변은 **25단어 이내 한국어**로 고정되어 있음 (시스템 프롬프트)
- 임시 오디오 파일(`input.wav`, `output.mp3`)은 처리 후 자동 삭제됨
- 동일한 녹음을 반복 처리하지 않도록 해시 기반 중복 방지 로직 포함

---

## 📋 사전 요구사항

- Python 3.8+
- OpenAI API 키 ([platform.openai.com](https://platform.openai.com))
- 인터넷 연결 (Whisper API, GPT API, gTTS 모두 외부 통신 필요)
