// js/chatbot/floating_chatbot.js

// chatbot_core.js에 정의된 전역 변수 및 함수를 사용합니다.
// (USER_ID, selectedImageFile, chatHistoryArray, getCurrentTime, scrollToBottom,
// loadChatHistoryFromSessionStorage, renderChatHistory, addMessageAndSave,
// addMessageToChat, sendMessage, showHistoryModal, closeHistoryModal, loadUserNicknameForChatbot)

document.addEventListener('DOMContentLoaded', () => {
    console.log("[Floating Chatbot UI Init] DOMContentLoaded 이벤트 발생.");

    // 챗봇 아이콘 및 모달 관련 요소 (main.html 등에 존재하는 요소)
    const chatbotFloatingIcon = document.getElementById('chatbotFloatingIcon');
    const chatbotModalContainer = document.getElementById('chatbotModalContainer');
    const closeChatbotModal = document.getElementById('closeChatbotModal');
    // main.html의 챗봇 상담 링크는 이제 chatbot.html로 직접 이동하므로,
    // 여기서 chatbotNavLink 변수를 정의하고 클릭 이벤트를 추가할 필요가 없습니다.
    // 만약 main.html의 내비게이션 링크가 모달을 열도록 하려면 이 주석을 제거하고 로직을 활성화합니다.
    const chatbotNavLink = document.getElementById('chatbotNavLink');

    // 모달 내부의 DOM 요소들 (모달이 열렸을 때 접근 가능하도록 변수 선언은 여기에 둠)
    const chatHistory = document.getElementById('chat-history');
    const chatInput = document.getElementById('chat-input');
    const sendChatMessageButton = document.getElementById('send-chat-message');
    const uploadImageButton = document.getElementById('upload-image-button');
    const imageUploadInput = document.getElementById('image-upload-input');
    const showHistoryButton = document.getElementById('show-history-button');
    // initialGreeting 요소는 챗봇 모달 내부에 있으며, loadUserNicknameForChatbot에서 업데이트하므로 여기서 다시 가져올 필요 없습니다.

    // ----------------------------------------------------
    // 초기화 로직
    // ----------------------------------------------------
    // 이 파일이 로드되는 페이지는 chatbot.html이 아니므로, 초기화 시 챗봇 모달이 숨겨져 있어야 합니다.
    if (chatbotModalContainer) {
        chatbotModalContainer.classList.remove('active'); // active 클래스 제거 (CSS에 의해 display: none)
        // chatbotModalContainer.style.display = 'none'; // CSS가 제대로 작동한다면 이 줄은 필요 없음.
                                                         // 혹시 모를 충돌을 대비해 남겨둘 수는 있으나, 보통 classList 제어로 충분.
        console.log("[Floating Chatbot UI Init] 챗봇 모달 컨테이너 초기 숨김 처리 완료.");
    }
    // 플로팅 아이콘은 기본적으로 보여야 합니다.
    if (chatbotFloatingIcon) {
        chatbotFloatingIcon.style.display = 'block'; // CSS에서 기본 display: block;이 아니면 명시적으로 지정
        console.log("[Floating Chatbot UI Init] 챗봇 플로팅 아이콘 초기 표시 처리 완료.");
    }

    // 초기 챗봇 환영 메시지의 시간 설정
    // 이 시간 설정은 initial-chatbot-greeting 요소 내부에 있으므로, 해당 요소가 DOM에 존재하는지 먼저 확인해야 합니다.
    // 챗봇 모달이 display: none 상태이므로, 이 시점에는 .current-time 요소가 존재하지 않을 수 있습니다.
    // 이 부분은 챗봇 모달이 열릴 때 (active 될 때) 수행하는 것이 더 안전합니다.
    // if (document.querySelector('.current-time')) {
    //     document.querySelector('.current-time').textContent = getCurrentTime();
    // }

    // 페이지 로드 시 세션 스토리지에서 이전 대화 기록 불러오기 (chatbot_core.js 함수 사용)
    loadChatHistoryFromSessionStorage();
    // renderChatHistory()는 모달이 열릴 때 호출하는 것이 적절합니다.

    // 사용자 닉네임 및 USER_ID 로드 함수 호출 (chatbot_core.js 함수 사용)
    // 이 함수는 초기 로드 시 한 번만 호출하면 됩니다.
    loadUserNicknameForChatbot();
    console.log("[Floating Chatbot UI Init] 사용자 정보 로딩 함수 호출 완료.");


    // ----------------------------------------------------
    // 이벤트 리스너 바인딩
    // ----------------------------------------------------

    // 챗봇 아이콘 클릭 시 모달 열기/닫기
    if (chatbotFloatingIcon && chatbotModalContainer) {
        chatbotFloatingIcon.addEventListener('click', function() {
            chatbotModalContainer.classList.toggle('active');
            if (chatbotModalContainer.classList.contains('active')) {
                // 모달이 열릴 때 메시지창을 맨 아래로 스크롤 (chatbot_core.js 함수 사용)
                if (chatHistory) scrollToBottom(chatHistory);
                // 모달이 열릴 때마다 chatHistoryArray의 내용을 다시 렌더링 (chatbot_core.js 함수 사용)
                renderChatHistory(); // 모달이 열릴 때마다 최신 기록 렌더링

                // 초기 환영 메시지의 시간 업데이트
                if (document.querySelector('#chatbotModalContainer .current-time')) { // 모달 내부의 .current-time 찾기
                    document.querySelector('#chatbotModalContainer .current-time').textContent = getCurrentTime();
                }

                // 챗봇 모달이 열리면 플로팅 아이콘 숨기기
                chatbotFloatingIcon.style.display = 'none';
                console.log("[Floating Chatbot UI Event] 챗봇 모달 열림, 아이콘 숨김.");
            } else {
                // 챗봇 모달이 닫히면 플로팅 아이콘 다시 보이게
                chatbotFloatingIcon.style.display = 'block';
                console.log("[Floating Chatbot UI Event] 챗봇 모달 닫힘, 아이콘 표시.");
            }
        });
        console.log("[Floating Chatbot UI Init] 챗봇 플로팅 아이콘 이벤트 리스너 바인딩 완료.");
    }

    // 닫기 버튼 클릭 시 모달 닫기
    if (closeChatbotModal && chatbotModalContainer) {
        closeChatbotModal.addEventListener('click', function() {
            chatbotModalContainer.classList.remove('active');
            // 닫기 버튼으로 모달 닫을 때 플로팅 아이콘 다시 보이게
            if (chatbotFloatingIcon) {
                chatbotFloatingIcon.style.display = 'block';
            }
            console.log("[Floating Chatbot UI Event] 닫기 버튼 클릭으로 모달 닫힘.");
        });
        console.log("[Floating Chatbot UI Init] 닫기 버튼 이벤트 리스너 바인딩 완료.");
    }

    // 내비게이션 바의 "챗봇 상담" 링크 클릭 시 모달 열기
    // main.html의 챗봇 상담 링크는 이제 `chatbot.html`로 직접 이동합니다.
    // 하지만, 만약 이 링크가 모달을 열도록 의도되었다면 아래 로직을 활성화합니다.
    // 현재 main.html의 <a href="chatbot.html" id="chatbotNavLink">챗봇 상담</a> 처럼 href에 페이지 경로가 있다면 이 로직은 불필요합니다.
    // 만약 href="#" 이라면 이 로직을 활성화해야 합니다. (현재 HTML에 href="chatbot.html" 로 되어있으므로 이 로직은 주석 처리 유지)
    /*
    if (chatbotNavLink && chatbotModalContainer && chatHistory) {
        chatbotNavLink.addEventListener('click', function(e) {
            e.preventDefault(); // 기본 링크 이동 방지
            chatbotModalContainer.classList.add('active');
            if (chatbotFloatingIcon) {
                chatbotFloatingIcon.style.display = 'none';
            }
            scrollToBottom(chatHistory);
            renderChatHistory(); // 모달이 열릴 때마다 최신 기록 렌더링
            console.log("[Floating Chatbot UI Init] 내비게이션 '챗봇 상담' 링크 이벤트 리스너 바인딩 완료.");
        });
    }
    */


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
        console.log("[Floating Chatbot UI Init] '전송' 버튼 및 채팅 입력 필드 이벤트 리스너 바인딩 완료.");
    } else {
        console.error("[Floating Chatbot UI Init] '전송' 버튼 또는 채팅 입력 필드를 찾을 수 없습니다.");
    }

    // 이미지 업로드 이벤트 리스너
    // selectedImageFile 및 addMessageToChat() 함수는 chatbot_core.js 에 정의되어 있습니다.
    if (uploadImageButton && imageUploadInput) {
        console.log("[Floating Chatbot UI Init] 이미지 업로드 버튼과 파일 입력 필드를 찾았습니다.");
        uploadImageButton.addEventListener('click', () => {
            console.log("[Floating Chatbot Event] '사진 추가' 버튼 클릭됨. 숨겨진 input[type=file] 클릭 시도.");
            imageUploadInput.click();
        });

        imageUploadInput.addEventListener('change', (event) => {
            const files = event.target.files;
            if (files && files.length > 0) {
                selectedImageFile = files[0]; // 전역 변수 업데이트
                console.log("[Floating Chatbot Event] 파일 선택됨:", selectedImageFile.name);

                // 파일 선택 즉시 사용자에게 미리보기와 안내 메시지 표시 (저장은 sendMessage에서)
                addMessageToChat('user', '이미지가 선택되었습니다. 메시지를 입력하고 전송해주세요.', true, selectedImageFile);

            } else {
                selectedImageFile = null;
                console.log("[Floating Chatbot Event] 파일 선택이 취소되거나 파일이 선택되지 않았습니다.");
            }
        });
    } else {
        console.warn("[Floating Chatbot UI Init] 경고: 'uploadImageButton' 또는 'imageUploadInput' 요소를 찾을 수 없습니다. HTML ID를 확인해주세요.");
    }

    // 이전 질문 내역 버튼 이벤트 리스너 바인딩
    // showHistoryModal() 함수는 chatbot_core.js 에 정의되어 있습니다.
    if (showHistoryButton) {
        showHistoryButton.addEventListener('click', showHistoryModal);
        console.log("[Floating Chatbot UI Init] '이전 질문 내역 확인' 버튼 이벤트 리스너 바인딩 완료.");
    } else {
        console.warn("[Floating Chatbot UI Init] 경고: 'show-history-button' 요소를 찾을 수 없습니다.");
    }

    // 모달 외부 클릭 시 닫기 (이전 질문 내역 모달과 챗봇 모달 모두 적용)
    window.onclick = function(event) {
        const historyModal = document.getElementById('history-modal'); // 이전 질문 내역 모달
        const currentChatbotModal = document.getElementById('chatbotModalContainer');

        // 이전 질문 내역 모달 닫기
        if (historyModal && event.target === historyModal) {
            historyModal.style.display = "none";
            console.log("[History Modal] 모달 외부 클릭으로 히스토리 모달 닫힘.");
        }

        // 챗봇 모달 외부 클릭 시 닫기 로직
        // 클릭된 요소가 챗봇 모달 내부(`chatbot-modal-content`)가 아닌지 확인하여,
        // 모달 콘텐츠를 클릭했을 때는 닫히지 않도록 합니다.
        if (currentChatbotModal && currentChatbotModal.classList.contains('active')) {
            const clickedInsideModalContent = currentChatbotModal.querySelector('.chatbot-modal-content').contains(event.target);
            // 플로팅 아이콘이나 내비게이션 링크를 클릭하여 모달이 열린 경우에는,
            // 해당 클릭이 '모달 외부 클릭'으로 간주되어 바로 닫히지 않도록 예외 처리합니다.
            const clickedFloatingIcon = chatbotFloatingIcon && chatbotFloatingIcon.contains(event.target);
            const clickedNavLink = chatbotNavLink && chatbotNavLink.contains(event.target);

            if (!clickedInsideModalContent && !clickedFloatingIcon && !clickedNavLink) {
                 // 모달 외부, 플로팅 아이콘, 내비게이션 링크 외의 영역을 클릭했을 때만 닫기
                currentChatbotModal.classList.remove('active');
                if (chatbotFloatingIcon) {
                    chatbotFloatingIcon.style.display = 'block'; // 플로팅 아이콘 다시 보이게
                }
                console.log("[Floating Chatbot] 모달 외부 클릭으로 챗봇 모달 닫힘.");
            }
        }
    };
});