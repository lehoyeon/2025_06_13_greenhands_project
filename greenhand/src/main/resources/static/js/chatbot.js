// resources/static/js/chatbot/chatbot.js

// USER_ID를 전역 변수로 선언하고 초기화되지 않은 상태로 둡니다.
// 로그인된 사용자 정보가 로드된 후 실제 userId로 업데이트됩니다.
let USER_ID = null;

// 햄버거 메뉴 토글 기능 (기존 코드 유지)
function toggleNavMenu() {
    const navLinksContainer = document.getElementById('navLinksContainer');
    navLinksContainer.classList.toggle('active');
}

// 페이지 로드 시, nav-bar의 '챗봇 상담' 링크를 활성화
document.addEventListener('DOMContentLoaded', () => {
    const currentPath = window.location.pathname.split('/').pop();
    const navLinks = document.querySelectorAll('.nav-bar a');
    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href').split('/').pop(); // href에서 파일명만 추출
        if (linkPath === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    // 초기 챗봇 환영 메시지의 시간 설정
    document.querySelector('.current-time').textContent = getCurrentTime();

    // 챗봇 관련 이벤트 리스너 바인딩
    const sendButton = document.getElementById('send-chat-message');
    const chatInput = document.getElementById('chat-input');
    if (sendButton && chatInput) {
        sendButton.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                sendMessage();
                e.preventDefault(); // Enter 키 입력 시 줄 바꿈 방지
            }
        });
    }

    // 이전 질문 내역 버튼 이벤트 리스너 바인딩
    document.getElementById('show-history-button').addEventListener('click', showHistoryModal);

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

// 메시지를 채팅 기록에 추가하는 함수
function addMessageToChat(sender, messageHtmlContent, isUser = false) {
    const chatHistory = document.getElementById('chat-history');
    const messageClass = isUser ? 'user' : 'bot';
    const senderName = isUser ? '나' : 'AgroBuddy 챗봇';
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${messageClass}`;
    messageDiv.innerHTML = `
        <div class="message-info">
            <span class="message-sender">${senderName}</span>
            <span class="message-time">[${getCurrentTime()}]</span>
        </div>
        <div class="message-bubble">${messageHtmlContent}</div>
    `;
    chatHistory.appendChild(messageDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight; // 스크롤을 맨 아래로
}

// 챗봇 API로 메시지를 전송하고 응답을 받는 함수
async function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    const userMessage = chatInput.value.trim();

    if (userMessage === "") {
        return; // 빈 메시지는 전송하지 않음
    }

    if (USER_ID === null) {
        alert('사용자 정보를 불러오는 중입니다. 잠시 후 다시 시도해주세요.'); // 사용자 ID가 없으면 메시지 전송 불가
        return;
    }

    addMessageToChat('user', userMessage, true); // 사용자 메시지 표시
    chatInput.value = ''; // 입력 필드 초기화

    // 로딩 메시지 표시
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

    try {
        const response = await fetch('http://localhost:8000/chatbot/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_query: userMessage, user_id: USER_ID }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`API 오류: ${errorData.detail || response.statusText}`);
        }

        const data = await response.json();
        let botResponseContent = data.response; // FastAPI에서 이미 HTML로 변환된 내용

        // 파일 다운로드 링크 처리 (FastAPI에서 HTML로 변환되지 않으므로 여기서 추가)
        let additionalElementsHtml = '';
        if (data.file_path) {
            const fileName = data.file_path.split('/').pop(); // 파일명만 추출
            const downloadUrl = `http://localhost:8000/files/${data.file_path}`; // FastAPI의 파일 다운로드 API 엔드포인트
            additionalElementsHtml += `<br><a href="${downloadUrl}" download="${fileName}" class="download-link">${fileName} 다운로드</a>`;
        }

        loadingMessageDiv.remove(); // 로딩 메시지 제거
        addMessageToChat('bot', botResponseContent + additionalElementsHtml); // HTML 내용 직접 표시

    } catch (error) {
        console.error("챗봇 API 호출 중 오류 발생:", error);
        loadingMessageDiv.remove(); // 로딩 메시지 제거
        addMessageToChat('bot', `죄송합니다. 오류가 발생했습니다: ${error.message}`);
    }
}

// 이전 질문 내역 모달 열기 함수
async function showHistoryModal() {
    const modal = document.getElementById('history-modal');
    const historyList = document.getElementById('history-list');
    historyList.innerHTML = '<p style="text-align: center; color: #888;">이전 질문을 불러오는 중...</p>'; // 로딩 메시지

    modal.style.display = 'block'; // 모달 표시

    if (USER_ID === null) {
        historyList.innerHTML = '<p style="text-align: center; color: red;">사용자 정보를 불러오지 못했습니다. 로그인 상태를 확인해주세요.</p>';
        return;
    }

    try {
        // 사용자 ID를 포함하여 이전 질문 내역 API 호출
        const response = await fetch(`http://localhost:8000/chatbot/history/${USER_ID}`);
        if (!response.ok) {
            throw new Error(`API 오류: ${response.statusText}`);
        }
        const history = await response.json(); // API 응답 데이터를 받음

        historyList.innerHTML = ''; // 로딩 메시지 제거
        if (history.length === 0) {
            historyList.innerHTML = '<p style="text-align: center; color: #888;">이전 질문 내역이 없습니다.</p>';
        } else {
            // history 배열의 각 요소가 객체라고 가정하고 'user_query' 필드에 접근
            // 만약 FastAPI에서 단순히 문자열 배열을 반환한다면, query.user_query 대신 query를 사용
            history.forEach(item => {
                const questionText = item.user_query || item; // 'user_query' 필드가 없으면 아이템 자체를 사용
                const queryItem = document.createElement('div');
                queryItem.className = 'history-item';
                queryItem.textContent = questionText; // 질문 텍스트
                queryItem.onclick = () => {
                    document.getElementById('chat-input').value = questionText; // 입력 필드에 질문 채우기
                    closeHistoryModal(); // 모달 닫기
                    sendMessage(); // 챗봇에 질문 전송
                };
                historyList.appendChild(queryItem);
            });
        }

    } catch (error) {
        console.error("이전 질문 내역 로드 중 오류 발생:", error);
        historyList.innerHTML = `<p style="color: red; text-align: center;">오류 발생: ${error.message}</p>`;
    }
}

// 이전 질문 내역 모달 닫기 함수
function closeHistoryModal() {
    document.getElementById('history-modal').style.display = 'none';
}

// 모달 외부 클릭 시 닫기
window.onclick = function(event) {
    const modal = document.getElementById('history-modal');
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

// --- 추가된 사용자 닉네임 및 USER_ID 로드 함수 ---
async function loadUserNicknameForChatbot() {
    try {
        const response = await fetch('/api/main/user/me'); // MainController의 API 엔드포인트
        if (response.ok) {
            const userData = await response.json();
            const initialGreetingElement = document.getElementById('initial-chatbot-greeting');
            const chatHeaderTitleElement = document.getElementById('chatbot-header-title');

            if (initialGreetingElement) {
                // 닉네임이 있으면 닉네임, 없으면 아이디 사용 (main.html과 동일한 로직)
                const displayUserName = userData.nickname && userData.nickname !== 'null' && userData.nickname !== '' ? userData.nickname : (userData.username || '사용자');
                initialGreetingElement.textContent = `안녕하세요, ${displayUserName}님! 농업에 대해 궁금한 점을 물어보세요.`;
            }
            if (chatHeaderTitleElement) {
                // 챗봇 헤더 타이틀도 변경하고 싶다면 (선택 사항)
                const displayUserName = userData.nickname && userData.nickname !== 'null' && userData.nickname !== '' ? userData.nickname : (userData.username || '사용자');
                chatHeaderTitleElement.textContent = `💬 ${displayUserName}님 챗봇 상담 💬`;
            }

            // USER_ID를 로그인된 사용자의 실제 userId로 업데이트
            if (userData.userId) {
                USER_ID = parseInt(userData.userId); // 문자열을 숫자로 변환
            } else {
                console.warn("사용자 ID를 불러오지 못했습니다. 챗봇 기능이 제한될 수 있습니다.");
            }
        } else if (response.status === 401 || response.status === 403) {
            console.warn('사용자 정보 로드 실패: 인증 필요.');
            // 인증되지 않은 경우 기본 메시지 유지
        } else {
            console.error('사용자 정보 로드 실패:', response.status);
            // 오류 시 기본 메시지 유지
        }
    } catch (error) {
        console.error('사용자 정보 로드 네트워크 오류:', error);
        // 네트워크 오류 시 기본 메시지 유지
    }
}