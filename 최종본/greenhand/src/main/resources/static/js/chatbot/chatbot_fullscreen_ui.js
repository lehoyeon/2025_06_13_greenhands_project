// js/chatbot/chatbot_fullscreen_ui.js

document.addEventListener('DOMContentLoaded', () => {
    console.log("[Fullscreen Chatbot UI Init] DOMContentLoaded 이벤트 발생.");

    // 네비게이션 바 링크 활성화 (이 페이지는 'chatbot.html' 이므로 해당 링크에 active 클래스 부여)
    const currentPath = window.location.pathname.split('/').pop();
    const navLinks = document.querySelectorAll('.nav-bar a');
    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href').split('/').pop();
        if (linkPath === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    // 챗봇 관련 주요 DOM 요소 가져오기
    // 이 페이지에서는 챗봇 모달 컨테이너가 없고, 챗봇 자체가 메인 콘텐츠입니다.
    const chatHistory = document.getElementById('chat-history'); // 실제 메시지가 표시되는 DOM 요소
    const chatInput = document.getElementById('chat-input');
    const sendChatMessageButton = document.getElementById('send-chat-message');
    const uploadImageButton = document.getElementById('upload-image-button');
    const imageUploadInput = document.getElementById('image-upload-input');
    const showHistoryButton = document.getElementById('show-history-button');
    const historyModal = document.getElementById('history-modal'); // 이전 질문 내역 모달
    const historyList = document.getElementById('history-list'); // 이전 질문 내역 리스트
    const initialGreeting = document.getElementById('initial-chatbot-greeting');

    // 초기 챗봇 환영 메시지의 시간 설정
    // getCurrentTime() 함수는 chatbot_core.js 에 정의되어 있습니다.
    if (document.querySelector('.current-time')) {
        document.querySelector('.current-time').textContent = getCurrentTime();
    }

    // 페이지 로드 시 세션 스토리지에서 이전 대화 기록 불러오기
    // loadChatHistoryFromSessionStorage() 함수는 chatbot_core.js 에 정의되어 있습니다.
    loadChatHistoryFromSessionStorage();
    // 기록 로드 후 화면에 렌더링
    renderChatHistory();


    // 챗봇 아이콘, 모달 컨테이너, 닫기 버튼, 내비게이션 링크 관련 로직은 이 페이지에서 제거됩니다.
    // 이 페이지 자체가 전체 화면 챗봇이므로 플로팅 UI 제어가 필요 없습니다.


    // '전송' 버튼 및 채팅 입력 필드 이벤트 리스너 바인딩
    // sendMessage() 함수는 chatbot_core.js 에 정의되어 있습니다.
    if (sendChatMessageButton && chatInput) {
        sendChatMessageButton.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                sendMessage();
                e.preventDefault(); // Enter 키 입력 시 줄 바꿈 방지
            }
        });
        console.log("[Fullscreen Chatbot UI Init] '전송' 버튼 및 채팅 입력 필드 이벤트 리스너 바인딩 완료.");
    } else {
        console.error("[Fullscreen Chatbot UI Init] '전송' 버튼 또는 채팅 입력 필드를 찾을 수 없습니다.");
    }

    // 이미지 업로드 이벤트 리스너
    // selectedImageFile 및 addMessageToChat() 함수는 chatbot_core.js 에 정의되어 있습니다.
    if (uploadImageButton && imageUploadInput) {
        console.log("[Fullscreen Chatbot UI Init] 이미지 업로드 버튼과 파일 입력 필드를 찾았습니다.");
        uploadImageButton.addEventListener('click', () => {
            console.log("[Fullscreen Chatbot Event] '사진 추가' 버튼 클릭됨. 숨겨진 input[type=file] 클릭 시도.");
            imageUploadInput.click();
        });

        imageUploadInput.addEventListener('change', (event) => {
            const files = event.target.files;
            if (files && files.length > 0) {
                selectedImageFile = files[0]; // 전역 변수 업데이트
                console.log("[Fullscreen Chatbot Event] 파일 선택됨:", selectedImageFile.name);

                // 파일 선택 즉시 사용자에게 미리보기와 안내 메시지 표시 (저장은 sendMessage에서)
                addMessageToChat('user', '이미지가 선택되었습니다. 메시지를 입력하고 전송해주세요.', true, selectedImageFile);

            } else {
                selectedImageFile = null;
                console.log("[Fullscreen Chatbot Event] 파일 선택이 취소되거나 파일이 선택되지 않았습니다.");
            }
        });
    } else {
        console.warn("[Fullscreen Chatbot UI Init] 경고: 'uploadImageButton' 또는 'imageUploadInput' 요소를 찾을 수 없습니다. HTML ID를 확인해주세요.");
    }

    // 이전 질문 내역 버튼 이벤트 리스너 바인딩
    // showHistoryModal() 함수는 chatbot_core.js 에 정의되어 있습니다.
    if (showHistoryButton) {
        showHistoryButton.addEventListener('click', showHistoryModal);
        console.log("[Fullscreen Chatbot UI Init] '이전 질문 내역 확인' 버튼 이벤트 리스너 바인딩 완료.");
    } else {
        console.warn("[Fullscreen Chatbot UI Init] 경고: 'show-history-button' 요소를 찾을 수 없습니다.");
    }

    // 사용자 닉네임 및 USER_ID 로드 함수 호출
    // loadUserNicknameForChatbot() 함수는 chatbot_core.js 에 정의되어 있습니다.
    loadUserNicknameForChatbot();


    // 모달 외부 클릭 시 닫기 (이 페이지에서는 이전 질문 내역 모달만 해당)
    window.onclick = function(event) {
        const modal = document.getElementById('history-modal');
        if (modal && event.target === modal) {
            modal.style.display = "none";
            console.log("[History Modal] 모달 외부 클릭으로 히스토리 모달 닫힘.");
        }
        // 챗봇 모달 (floating) 관련 로직은 이 파일에서는 처리하지 않습니다.
    }
});