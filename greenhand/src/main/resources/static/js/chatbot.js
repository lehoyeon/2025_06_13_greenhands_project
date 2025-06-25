// resources/static/js/chatbot/chatbot.js

// USER_ID를 전역 변수로 선언하고 초기화되지 않은 상태로 둡니다.
// 로그인된 사용자 정보가 로드된 후 실제 userId로 업데이트됩니다.
let USER_ID = null;
let selectedImageFile = null;

// 햄버거 메뉴 토글 기능 (기존 코드 유지)
function toggleNavMenu() {
    const navLinksContainer = document.getElementById('navLinksContainer');
    navLinksContainer.classList.toggle('active');
}

// 페이지 로드 시, nav-bar의 '챗봇 상담' 링크를 활성화
document.addEventListener('DOMContentLoaded', () => {
    console.log("[Chatbot Init] DOMContentLoaded 이벤트 발생.");
    const currentPath = window.location.pathname.split('/').pop();
    const navLinks = document.querySelectorAll('.nav-bar a');
    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href').split('/').pop(); // href에서 파일명만 추출
        if (linkPath === currentPath) {
            link.classList.add('active');
            console.log(`[Chatbot Init] 내비게이션 링크 활성화됨: ${currentPath}`);
        } else {
            link.classList.remove('active');
        }
    });

    // 초기 챗봇 환영 메시지의 시간 설정
    document.querySelector('.current-time').textContent = getCurrentTime();

    // 챗봇 관련 이벤트 리스너 바인딩
    const sendButton = document.getElementById('send-chat-message');
    const chatInput = document.getElementById('chat-input');
    const uploadImageButton = document.getElementById('upload-image-button');
    const imageUploadInput = document.getElementById('image-upload-input');

    if (sendButton && chatInput) {
        sendButton.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                sendMessage();
                e.preventDefault(); // Enter 키 입력 시 줄 바꿈 방지
            }
        });
        console.log("[Chatbot Init] '전송' 버튼 및 채팅 입력 필드 이벤트 리스너 바인딩 완료.");
    } else {
        console.error("[Chatbot Init] '전송' 버튼 또는 채팅 입력 필드를 찾을 수 없습니다.");
    }

    // --- 이미지 업로드 이벤트 리스너 수정된 부분 ---
    if (uploadImageButton && imageUploadInput) {
        console.log("[Chatbot Init] 이미지 업로드 버튼과 파일 입력 필드를 찾았습니다.");
        uploadImageButton.addEventListener('click', () => {
            console.log("[Chatbot Event] '사진 추가' 버튼 클릭됨. 숨겨진 input[type=file] 클릭 시도.");
            imageUploadInput.click(); // 숨겨진 input[type="file"] 클릭 유도
        });

        imageUploadInput.addEventListener('change', (event) => {
            const files = event.target.files;
            if (files && files.length > 0) {
                selectedImageFile = files[0]; // 전역 변수에 선택된 파일 할당
                console.log("[Chatbot Event] 파일 선택됨:", selectedImageFile.name, selectedImageFile.type, selectedImageFile.size, "바이트");

                // 파일 선택 즉시 사용자에게 미리보기와 안내 메시지 표시
                addMessageToChat('user', '이미지가 선택되었습니다. 메시지를 입력하고 전송해주세요.', true, selectedImageFile);

            } else {
                selectedImageFile = null; // 파일 선택이 취소된 경우 초기화
                console.log("[Chatbot Event] 파일 선택이 취소되거나 파일이 선택되지 않았습니다.");
            }
        });
    } else {
        console.warn("[Chatbot Init] 경고: 'uploadImageButton' 또는 'imageUploadInput' 요소를 찾을 수 없습니다. HTML ID를 확인해주세요.");
    }
    // --- /이미지 업로드 이벤트 리스너 수정된 부분 ---

    // 이전 질문 내역 버튼 이벤트 리스너 바인딩
    const showHistoryBtn = document.getElementById('show-history-button');
    if (showHistoryBtn) {
        showHistoryBtn.addEventListener('click', showHistoryModal);
        console.log("[Chatbot Init] '이전 질문 내역 확인' 버튼 이벤트 리스너 바인딩 완료.");
    } else {
        console.warn("[Chatbot Init] 경고: 'show-history-button' 요소를 찾을 수 없습니다.");
    }

    // --- 추가된 닉네임 및 USER_ID 로드 함수 호출 ---
    loadUserNicknameForChatbot();
});

// 현재 시간 가져오는 함수
function getCurrentTime() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
}

/**
 * 메시지를 채팅 기록에 추가하는 함수
 * @param {string} sender 메시지를 보내는 주체 (예: 'user', 'bot')
 * @param {string} messageHtmlContent 메시지 내용 (HTML 문자열 가능)
 * @param {boolean} isUser 사용자인지 챗봇인지 여부
 * @param {File | null} imageFile (선택 사항) 클라이언트 미리보기용 File 객체
 * @param {string | null} imageUrlFromServer (선택 사항) 서버에서 받은 이미지 URL (이전 기록용 또는 봇 응답 이미지)
 */
function addMessageToChat(sender, messageHtmlContent, isUser = false, imageFile = null, imageUrlFromServer = null) {
    const chatHistory = document.getElementById('chat-history');
    if (!chatHistory) {
        console.error("[Chatbot UI Error] 'chat-history' 요소를 찾을 수 없습니다. 메시지를 추가할 수 없습니다.");
        return;
    }

    const messageClass = isUser ? 'user' : 'bot';
    const senderName = isUser ? '나' : 'AgroBuddy 챗봇';
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${messageClass}`;

    const messageInfo = document.createElement('div');
    messageInfo.className = 'message-info';
    messageInfo.innerHTML = `
        <span class="message-sender">${senderName}</span>
        <span class="message-time">[${getCurrentTime()}]</span>
    `;

    const messageBubble = document.createElement('div');
    messageBubble.className = 'message-bubble';

    messageDiv.appendChild(messageInfo);
    messageDiv.appendChild(messageBubble); // 일단 버블만 추가하고 내용은 아래에서 채움

    if (imageFile) { // 새로 업로드하는 이미지 (클라이언트 미리보기)
        const reader = new FileReader();
        reader.onload = (e) => {
            const imageElement = document.createElement('img');
            imageElement.src = e.target.result;
            imageElement.alt = "업로드 이미지";
            imageElement.style.maxWidth = '100%';
            imageElement.style.height = 'auto';
            imageElement.style.display = 'block';
            imageElement.style.marginBottom = messageHtmlContent ? '10px' : '0'; // 텍스트가 있으면 여백 추가
            messageBubble.appendChild(imageElement);

            if (messageHtmlContent) {
                // 이미지가 있고 텍스트 내용도 있으면 줄 바꿈 후 텍스트 추가
                messageBubble.innerHTML += `<div>${messageHtmlContent}</div>`;
            }

            chatHistory.appendChild(messageDiv);
            chatHistory.scrollTop = chatHistory.scrollHeight;
            console.log(`[Chatbot UI] 사용자 이미지 메시지 (클라이언트 미리보기) 추가 완료. 파일: ${imageFile.name}`);
        };
        reader.readAsDataURL(imageFile);
    } else if (imageUrlFromServer) { // 서버로부터 받은 이미지 URL (이전 기록용 또는 봇이 반환한 이미지)
        // FastAPI 서버의 `uploaded_images` 정적 서빙 경로에 맞춰 URL을 조정
        const fullImageUrl = `http://localhost:8000${imageUrlFromServer}`;
        const imageElement = document.createElement('img');
        imageElement.src = fullImageUrl;
        imageElement.alt = "첨부 이미지";
        imageElement.style.maxWidth = '100%';
        imageElement.style.height = 'auto';
        imageElement.style.display = 'block';
        imageElement.style.marginBottom = messageHtmlContent ? '10px' : '0'; // 텍스트가 있으면 여백 추가
        messageBubble.appendChild(imageElement);

        if (messageHtmlContent) {
            messageBubble.innerHTML += `<div>${messageHtmlContent}</div>`;
        }

        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        console.log(`[Chatbot UI] 이미지 URL 메시지 (서버 응답/이전 기록) 추가 완료. URL: ${fullImageUrl}`);
    } else { // 이미지 없이 텍스트만
        messageBubble.innerHTML = messageHtmlContent;
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        console.log(`[Chatbot UI] 텍스트 메시지 추가 완료. 내용: "${messageHtmlContent.substring(0, Math.min(messageHtmlContent.length, 30))}..."`);
    }
}


// 챗봇 API로 메시지를 전송하고 응답을 받는 함수
async function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    const userMessage = chatInput.value.trim();
    const imageUploadInput = document.getElementById('image-upload-input');

    // 메시지와 이미지 둘 다 없으면 전송하지 않음
    if (userMessage === "" && !selectedImageFile) {
        console.log("[Chatbot Send] 메시지 내용과 선택된 이미지가 없어 전송하지 않습니다.");
        return;
    }

    if (USER_ID === null) {
        alert('사용자 정보를 불러오는 중입니다. 잠시 후 다시 시도해주세요.');
        console.warn("[Chatbot Send] USER_ID가 NULL입니다. 사용자 정보를 기다리는 중...");
        return;
    }

    // --- 👇 수정된 부분: 사용자 텍스트 메시지를 로딩 메시지보다 먼저 표시 👇 ---
    if (userMessage !== "") { // 텍스트 메시지가 있을 경우
        console.log("[Chatbot Send] 사용자 텍스트 메시지 즉시 표시:", userMessage);
        addMessageToChat('user', userMessage, true);
    }
    // 이미지 파일은 'change' 이벤트에서 이미 addMessageToChat으로 미리보기 되었을 것입니다.
    // 따라서 여기서는 텍스트 메시지만 즉시 표시하는 로직을 추가합니다.
    // 만약 텍스트 없이 이미지만 보내는 경우, 이미지는 이미 'change' 이벤트에서 추가되었으므로 중복되지 않습니다.
    // --- 👆 수정된 부분 👆 ---

    chatInput.value = ''; // 텍스트 입력 필드 초기화 (사용자 메시지 표시 후)

    // 챗봇 응답을 기다리는 로딩 메시지 추가
    const loadingMessageDiv = document.createElement('div');
    loadingMessageDiv.className = 'chat-message bot';
    loadingMessageDiv.innerHTML = `
        <div class="message-info">
            <span class="message-sender">AgroBuddy 챗봇</span> <span class="message-time">[${getCurrentTime()}]</span>
        </div>
        <div class="message-bubble">...</div>
    `;
    document.getElementById('chat-history').appendChild(loadingMessageDiv);
    document.getElementById('chat-history').scrollTop = document.getElementById('chat-history').scrollHeight;
    console.log("[Chatbot Send] 로딩 메시지 추가.");

    try {
        const formData = new FormData();
        formData.append('userQuery', userMessage);
        formData.append('userId', USER_ID);
        if (selectedImageFile) {
            formData.append('imageFile', selectedImageFile);
            console.log("[Chatbot Send] FormData에 이미지 파일 추가됨:", selectedImageFile.name);
        }

        console.log("[Chatbot Send] API 호출 시도: /api/chatbot/ask");
        const response = await fetch('/api/chatbot/ask', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error("[Chatbot Send] API 응답 오류:", response.status, errorData);
            throw new Error(`API 오류: ${errorData.message || response.statusText}`);
        }

        const data = await response.json(); // 서버로부터 받은 JSON 응답
        console.log("[Chatbot Send] API 응답 성공. 응답 데이터:", data);

        // 응답 메시지 표시
        loadingMessageDiv.remove(); // 로딩 메시지 제거
        console.log("[Chatbot Send] 로딩 메시지 제거됨.");

        const botResponseText = data.response || "죄송합니다. 응답 내용을 찾을 수 없습니다.";
        const botResponseImageUrl = data.image_url || null; // 예시: 서버 응답에 'image_url' 필드가 있다면

        addMessageToChat('bot', botResponseText, false, null, botResponseImageUrl); // 챗봇 응답 및 이미지 추가
        console.log(`[Chatbot Send] 챗봇 응답 대화창에 추가 시도. 텍스트: "${botResponseText.substring(0, Math.min(botResponseText.length, 30))}...", 이미지 URL: ${botResponseImageUrl}`);

        // ✅ 이미지 전송 후 상태 초기화
        selectedImageFile = null; // 전송 완료 후 선택된 파일 정보 초기화
        if (imageUploadInput) {
            imageUploadInput.value = ''; // 파일 input 초기화 (같은 파일 재선택 가능하게)
            console.log("[Chatbot Send] selectedImageFile 및 파일 input 초기화됨.");
        }

    } catch (error) {
        console.error("챗봇 오류:", error);
        loadingMessageDiv.remove();
        addMessageToChat('bot', `죄송합니다. 오류가 발생했습니다: ${error.message}`);
    }
}

// 이전 질문 내역 모달 열기 함수
async function showHistoryModal() {
    const modal = document.getElementById('history-modal');
    const historyList = document.getElementById('history-list');
    if (!modal || !historyList) {
        console.error("[History Modal Error] 모달 또는 히스토리 리스트 요소를 찾을 수 없습니다.");
        return;
    }

    historyList.innerHTML = '<p style="text-align: center; color: #888;">이전 질문을 불러오는 중...</p>'; // 로딩 메시지
    modal.style.display = 'block'; // 모달 표시
    console.log("[History Modal] 이전 질문 내역 모달 열기 시도.");

    if (USER_ID === null) {
        historyList.innerHTML = '<p style="text-align: center; color: red;">사용자 정보를 불러오지 못했습니다. 로그인 상태를 확인해주세요.</p>';
        console.warn("[History Modal] USER_ID가 NULL입니다. 이전 질문 내역을 불러올 수 없습니다.");
        return;
    }

    try {
        // Spring Boot 컨트롤러의 엔드포인트로 변경
        console.log("[History Modal] API 호출 시도: /api/chatbot/history/" + USER_ID);
        const response = await fetch(`/api/chatbot/history/${USER_ID}`);
        if (!response.ok) {
            const errorData = await response.json();
            console.error("[History Modal] API 응답 오류:", response.status, errorData);
            throw new Error(`API 오류: ${errorData.message || response.statusText}`); // Spring Boot에서 'message' 필드 반환 가정
        }
        const history = await response.json(); // FastAPI가 반환하는 객체 배열 형태 (Spring Boot가 그대로 중계)
        console.log("[History Modal] 이전 질문 내역 로드 성공. 데이터:", history);

        historyList.innerHTML = ''; // 로딩 메시지 제거
        if (history.length === 0) {
            historyList.innerHTML = '<p style="text-align: center; color: #888;">이전 질문 내역이 없습니다.</p>';
            console.log("[History Modal] 이전 질문 내역이 없습니다.");
        } else {
            history.forEach(item => {
                const queryItem = document.createElement('div');
                queryItem.className = 'history-item';

                let historyContent = `<strong>나:</strong> ${item.user_query}`;
                if (item.image_url) {
                    // 이전 기록의 이미지를 표시 (FastAPI의 /uploaded_images/ 경로 반영)
                    const fullImageUrl = `http://localhost:8000${item.image_url}`;
                    historyContent += `<br><img src="${fullImageUrl}" alt="첨부 이미지" style="max-width: 100px; max-height: 100px; border-radius: 4px; margin-top: 5px;">`;
                }
                historyContent += `<br><strong>AgroBuddy 챗봇:</strong> ${item.bot_response}`;

                queryItem.innerHTML = historyContent; // HTML 내용을 넣으므로 innerHTML 사용

                queryItem.onclick = () => {
                    document.getElementById('chat-input').value = item.user_query; // 입력 필드에 질문 채우기
                    closeHistoryModal(); // 모달 닫기
                    // 이전 기록을 클릭했을 때 이미지는 다시 전송하지 않습니다. (텍스트만)
                    console.log(`[History Modal] 이전 질문 클릭됨: "${item.user_query}"`);
                    // sendMessage(); // 이전 질문을 클릭했을 때 자동으로 메시지를 보내지 않도록 주석 처리
                                   // 사용자가 입력 필드에 질문이 채워진 것을 확인 후 직접 '전송' 누르도록 유도
                };
                historyList.appendChild(queryItem);
            });
            console.log("[History Modal] 이전 질문 내역 표시 완료.");
        }

    } catch (error) {
        console.error("이전 질문 내역 로드 중 오류 발생:", error);
        historyList.innerHTML = `<p style="color: red; text-align: center;">오류 발생: ${error.message}</p>`;
    }
}

// 이전 질문 내역 모달 닫기 함수
function closeHistoryModal() {
    document.getElementById('history-modal').style.display = 'none';
    console.log("[History Modal] 이전 질문 내역 모달 닫힘.");
}

// 모달 외부 클릭 시 닫기
window.onclick = function(event) {
    const modal = document.getElementById('history-modal');
    if (modal && event.target === modal) { // modal이 존재하는지 확인
        modal.style.display = "none";
        console.log("[History Modal] 모달 외부 클릭으로 모달 닫힘.");
    }
}

// --- 추가된 사용자 닉네임 및 USER_ID 로드 함수 ---
async function loadUserNicknameForChatbot() {
    try {
        console.log("[User Load] 사용자 정보 로드 API 호출 시도: /api/main/user/me");
        const response = await fetch('/api/main/user/me'); // MainController의 API 엔드포인트
        if (response.ok) {
            const userData = await response.json();
            console.log("[User Load] 사용자 정보 로드 성공:", userData);
            const initialGreetingElement = document.getElementById('initial-chatbot-greeting');
            const chatHeaderTitleElement = document.getElementById('chatbot-header-title');

            if (initialGreetingElement) {
                // 닉네임이 있으면 닉네임, 없으면 아이디 사용 (main.html과 동일한 로직)
                const displayUserName = userData.nickname && userData.nickname !== 'null' && userData.nickname !== '' ? userData.nickname : (userData.username || '사용자');
                initialGreetingElement.textContent = `안녕하세요, ${displayUserName}님! 농업에 대해 궁금한 점을 물어보세요.`;
                console.log(`[User Load] 초기 환영 메시지 업데이트: ${displayUserName}님`);
            }
            if (chatHeaderTitleElement) {
                // 챗봇 헤더 타이틀도 변경하고 싶다면 (선택 사항)
                const displayUserName = userData.nickname && userData.nickname !== 'null' && userData.nickname !== '' ? userData.nickname : (userData.username || '사용자');
                chatHeaderTitleElement.textContent = `💬 ${displayUserName}님 챗봇 상담 💬`;
                console.log(`[User Load] 챗봇 헤더 타이틀 업데이트: ${displayUserName}님`);
            }

            // USER_ID를 로그인된 사용자의 실제 userId로 업데이트
            if (userData.userId) {
                USER_ID = parseInt(userData.userId); // 문자열을 숫자로 변환
                console.log("[User Load] USER_ID 설정됨:", USER_ID);
            } else {
                console.warn("[User Load] 사용자 ID를 불러오지 못했습니다. 챗봇 기능이 제한될 수 있습니다.");
            }
        } else if (response.status === 401 || response.status === 403) {
            console.warn('[User Load] 사용자 정보 로드 실패: 인증 필요 (상태 코드:', response.status, ').');
            // 인증되지 않은 경우 기본 메시지 유지
        } else {
            console.error('[User Load] 사용자 정보 로드 실패 (상태 코드:', response.status, ').');
            // 오류 시 기본 메시지 유지
        }
    } catch (error) {
        console.error('[User Load] 사용자 정보 로드 네트워크 오류:', error);
        // 네트워크 오류 시 기본 메시지 유지
    }
}