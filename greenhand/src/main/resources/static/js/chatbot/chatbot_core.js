// js/chatbot/chatbot_core.js

// USER_ID를 전역 변수로 선언하고 초기화되지 않은 상태로 둡니다.
let USER_ID = null;
let selectedImageFile = null;

// 챗봇 대화 기록을 저장할 배열
let chatHistoryArray = [];

// ★★★ 사용자 정보 로딩 상태를 추적하는 Promise ★★★
// loadUserNicknameForChatbot 함수가 이 Promise를 resolve하도록 합니다.
let userLoadedPromiseResolve;
let userLoadedPromise = new Promise(resolve => {
    userLoadedPromiseResolve = resolve;
});


// 햄버거 메뉴 토글 기능 (기존 코드 유지)
function toggleNavMenu() {
    const navLinksContainer = document.getElementById('navLinksContainer');
    if (navLinksContainer) {
        navLinksContainer.classList.toggle('active');
    }
}

// ----------------------------------------------------
// 유틸리티 함수들
// ----------------------------------------------------

function getCurrentTime() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
}

function scrollToBottom(element) {
    if (element) {
        element.scrollTop = element.scrollHeight;
    }
}

// ----------------------------------------------------
// 챗봇 대화 기록 관리 함수 (Session Storage 사용)
// ----------------------------------------------------

function loadChatHistoryFromSessionStorage() {
    const savedChat = sessionStorage.getItem('chatHistory');
    if (savedChat) {
        try {
            const parsedChat = JSON.parse(savedChat);
            if (Array.isArray(parsedChat) && parsedChat.length > 0) {
                chatHistoryArray = parsedChat;
                console.log("[Chat History] 세션 스토리지에서 대화 기록 불러옴:", chatHistoryArray);
            } else {
                chatHistoryArray = [];
                console.log("[Chat History] 세션 스토리지에 저장된 대화 기록이 유효하지 않거나 비어있습니다.");
            }
        } catch (e) {
            console.error("[Chat History Error] 세션 스토리지 대화 기록 파싱 오류:", e);
            chatHistoryArray = [];
        }
    } else {
        chatHistoryArray = [];
        console.log("[Chat History] 세션 스토리지에 저장된 대화 기록이 없습니다.");
    }
}

function renderChatHistory() {
    const chatHistoryDom = document.getElementById('chat-history');
    if (!chatHistoryDom) {
        console.error("[Chatbot UI Error] 'chat-history' 요소를 찾을 수 없습니다. 대화 기록을 렌더링할 수 없습니다.");
        return;
    }

    const initialGreeting = document.getElementById('initial-chatbot-greeting');
    let greetingHtml = '';
    if (initialGreeting) {
        greetingHtml = initialGreeting.outerHTML;
    }

    chatHistoryDom.innerHTML = '';

    if (greetingHtml) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = greetingHtml;
        chatHistoryDom.appendChild(tempDiv.firstChild);
    }

    chatHistoryArray.forEach(msg => {
        addMessageToChat(
            msg.senderType,
            msg.content,
            msg.isUser,
            null,
            msg.imageUrlFromServer,
            msg.fileUrlFromServer,
            msg.linkUrl
        );
    });
    scrollToBottom(chatHistoryDom);
    console.log("[Chat History] 대화 기록 화면에 렌더링 완료.");
}


function addMessageAndSave(senderType, content, isUser, imageUrlFromServer = null, fileUrlFromServer = null, linkUrl = null) {
    const messageObject = {
        senderType: senderType,
        content: content,
        isUser: isUser,
        timestamp: new Date().toISOString(),
        imageUrlFromServer: imageUrlFromServer,
        fileUrlFromServer: fileUrlFromServer,
        linkUrl: linkUrl
    };

    chatHistoryArray.push(messageObject);
    sessionStorage.setItem('chatHistory', JSON.stringify(chatHistoryArray));

    addMessageToChat(senderType, content, isUser, null, imageUrlFromServer, fileUrlFromServer, linkUrl);

    console.log("[Chat History] 메시지 추가 및 세션 스토리지 저장 완료.");
}

// ----------------------------------------------------
// 챗봇 메시지 UI 관련 함수
// ----------------------------------------------------

function addMessageToChat(sender, messageHtmlContent, isUser = false, imageFile = null, imageUrlFromServer = null, fileUrlFromServer = null, linkUrl = null) {
    const chatHistory = document.getElementById('chat-history');
    if (!chatHistory) {
        console.error("[Chatbot UI Error] 'chat-history' 요소를 찾을 수 없습니다. 메시지를 추가할 수 없습니다.");
        return;
    }

    const senderName = isUser ? '나' : 'AgroBuddy 챗봇';
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${isUser ? 'user' : 'bot'}`;

    const messageInfo = document.createElement('div');
    messageInfo.className = 'message-info';
    messageInfo.innerHTML = `
        <span class="message-sender">${senderName}</span>
        <span class="message-time">[${getCurrentTime()}]</span>
    `;

    const messageBubble = document.createElement('div');
    messageBubble.className = 'message-bubble';

    messageDiv.appendChild(messageInfo);
    messageDiv.appendChild(messageBubble);

    if (imageFile) { // 클라이언트에서 선택한 이미지 미리보기 (사용자 메시지용)
        const reader = new FileReader();
        reader.onload = (e) => {
            const imageElement = document.createElement('img');
            imageElement.src = e.target.result;
            imageElement.alt = "업로드 이미지";
            imageElement.style.maxWidth = '100%';
            imageElement.style.height = 'auto';
            imageElement.style.display = 'block';
            imageElement.style.marginBottom = messageHtmlContent ? '10px' : '0';
            messageBubble.appendChild(imageElement);

            if (messageHtmlContent && messageHtmlContent.trim() !== "") { // 텍스트 내용이 있다면 추가
                messageBubble.innerHTML += `<div>${messageHtmlContent}</div>`;
            }

            chatHistory.appendChild(messageDiv);
            scrollToBottom(chatHistory);
            console.log(`[Chatbot UI] 사용자 이미지 메시지 (클라이언트 미리보기) 추가 완료. 파일: ${imageFile.name}`);
        };
        reader.readAsDataURL(imageFile);
    } else if (imageUrlFromServer) { // 서버로부터 받은 이미지 URL (봇 응답 또는 이전 기록)
        const fullImageUrl = `http://localhost:8000${imageUrlFromServer}`;
        const imageElement = document.createElement('img');
        imageElement.src = fullImageUrl;
        imageElement.alt = "첨부 이미지";
        imageElement.style.maxWidth = '100%';
        imageElement.style.height = 'auto';
        imageElement.style.display = 'block';
        imageElement.style.marginBottom = messageHtmlContent ? '10px' : '0';
        messageBubble.appendChild(imageElement);

        if (messageHtmlContent && messageHtmlContent.trim() !== "") { // 텍스트 내용이 있다면 추가
            messageBubble.innerHTML += `<div>${messageHtmlContent}</div>`;
        }

        chatHistory.appendChild(messageDiv);
        scrollToBottom(chatHistory);
        console.log(`[Chatbot UI] 이미지 URL 메시지 (서버 응답/이전 기록) 추가 완료. URL: ${fullImageUrl}`);
    } else if (fileUrlFromServer) { // 서버로부터 받은 파일 다운로드 링크 (보고서 전용)
        // messageHtmlContent 먼저 추가
        messageBubble.innerHTML = messageHtmlContent;

        const downloadLink = document.createElement('a');
        const fullFileUrl = `http://localhost:8000${fileUrlFromServer}`;
        downloadLink.href = fullFileUrl;
        const fileName = fullFileUrl.substring(fullFileUrl.lastIndexOf('/') + 1); // 올바른 파일명 추출
        downloadLink.textContent = `[${fileName}] 다운로드`;
        downloadLink.target = "_blank";
        downloadLink.download = true;

        downloadLink.style.display = 'block';
        downloadLink.style.marginTop = '10px';
        downloadLink.style.padding = '8px 12px';
        downloadLink.style.backgroundColor = '#4CAF50';
        downloadLink.style.color = 'white';
        downloadLink.style.textAlign = 'center';
        downloadLink.style.textDecoration = 'none';
        downloadLink.style.borderRadius = '5px';
        downloadLink.style.maxWidth = 'fit-content';

        messageBubble.appendChild(downloadLink);

        chatHistory.appendChild(messageDiv);
        scrollToBottom(chatHistory);
        console.log(`[Chatbot UI] 파일 다운로드 링크 추가 완료. URL: ${fullFileUrl}`);
    } else { // 텍스트 메시지만 (linkUrl이 함께 올 수 있음)
        let finalContent = messageHtmlContent;

        // '작물 진단' 페이지 링크 처리
        const textToFind = "'작물 진단' 페이지";
        const fullLinkUrl = `http://localhost:8080/${linkUrl}`;

        const escapedTextToFind = textToFind.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(escapedTextToFind, 'g');

        if (linkUrl && finalContent.includes(textToFind)) { // linkUrl이 있고, 텍스트가 메시지에 포함되어 있다면
            finalContent = finalContent.replace(
                regex,
                `<a href="${fullLinkUrl}" target="_blank" style="color: blue; text-decoration: underline; font-weight: bold;">${textToFind}</a>`
            );
            console.log(`[Chatbot UI] 텍스트 메시지 내 '${textToFind}'에 링크 추가 완료. URL: ${fullLinkUrl}`);
        } else if (linkUrl) { // 텍스트에 포함되어 있지 않지만 linkUrl이 있다면 메시지 끝에 추가 (선택 사항)
            finalContent += `<br><br>더 자세한 정보는 <a href="${fullLinkUrl}" target="_blank" style="color: blue; text-decoration: underline; font-weight: bold;">[바로가기]</a>`;
            console.warn(`[Chatbot UI] '${textToFind}' 문구를 찾을 수 없어 메시지 끝에 링크 추가. URL: ${fullLinkUrl}`);
        }


        messageBubble.innerHTML = finalContent; // 최종적으로 가공된 내용을 UI에 표시

        chatHistory.appendChild(messageDiv);
        scrollToBottom(chatHistory);
        console.log(`[Chatbot UI] 텍스트 메시지 추가 완료. 내용: "${finalContent.substring(0, Math.min(finalContent.length, 30))}..."`);
    }
}

// ----------------------------------------------------
// 챗봇 API 통신 함수
// ----------------------------------------------------

async function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    const userMessage = chatInput.value.trim();
    const imageUploadInput = document.getElementById('image-upload-input');
    const chatHistory = document.getElementById('chat-history');

    if (userMessage === "" && !selectedImageFile) {
        alert("메시지를 입력하거나 이미지를 선택해주세요.");
        return;
    }

    // ★★★ USER_ID가 설정될 때까지 기다리는 로직 ★★★
    if (USER_ID === null || isNaN(USER_ID)) {
        console.warn("[Chatbot Send] USER_ID가 아직 설정되지 않았습니다. 사용자 정보를 기다리는 중...");

        // 5초 타임아웃을 가진 Promise를 생성하여 USER_ID 로딩을 기다립니다.
        const timeoutPromise = new Promise(resolve => setTimeout(resolve, 5000)); // 5초 후 resolve
        const userReadyPromise = Promise.race([userLoadedPromise, timeoutPromise]); // userLoadedPromise 또는 timeoutPromise 중 먼저 완료되는 것을 기다림

        await userReadyPromise; // 기다림

        if (USER_ID === null || isNaN(USER_ID)) { // 기다린 후에도 USER_ID가 유효하지 않으면 에러
            alert('사용자 정보를 불러오지 못했습니다. 잠시 후 다시 시도하거나, 로그아웃 후 다시 로그인해주세요.');
            console.error("[Chatbot Send] USER_ID 로드 실패: 타임아웃 또는 유효하지 않은 값.");
            return;
        }
        console.log("[Chatbot Send] USER_ID 설정 확인됨:", USER_ID);
    }

    // ★★★ 사용자 메시지 및 이미지 (클라이언트 미리보기)를 먼저 UI에 표시 ★★★
    let userMessageContentForUI = userMessage;
    let userMessageImageUrlForUI = null;

    if (selectedImageFile) {
        const reader = new FileReader();
        await new Promise(resolve => {
            reader.onload = (e) => {
                userMessageImageUrlForUI = e.target.result; // Data URL for client-side preview
                resolve();
            };
            reader.readAsDataURL(selectedImageFile);
        });
        userMessageContentForUI = userMessage || '';
    }

    // 사용자 메시지를 UI에 표시하고 저장
    // addMessageAndSave의 마지막 3개 인자(imageUrlFromServer, fileUrlFromServer, linkUrl)는 null로 초기화
    addMessageAndSave('user', userMessageContentForUI, true, userMessageImageUrlForUI, null, null);

    chatInput.value = '';

    // 챗봇 응답을 기다리는 로딩 메시지 추가
    const loadingMessageDiv = document.createElement('div');
    loadingMessageDiv.className = 'chat-message bot loading-message';
    loadingMessageDiv.innerHTML = `
        <div class="message-info">
            <span class="message-sender">AgroBuddy 챗봇</span> <span class="message-time">[${getCurrentTime()}]</span>
        </div>
        <div class="message-bubble">...</div>
    `;
    if (chatHistory) {
        chatHistory.appendChild(loadingMessageDiv);
        scrollToBottom(chatHistory);
    }
    console.log("[Chatbot Send] 로딩 메시지 추가 (DOM에 직접).");

    try {
        const formData = new FormData();
        formData.append('user_query', userMessage);
        formData.append('user_id', USER_ID);
        if (selectedImageFile) {
            formData.append('image_file', selectedImageFile);
            console.log("[Chatbot Send] FormData에 이미지 파일 추가됨:", selectedImageFile.name);
        }

        console.log("[Chatbot Send] API 호출 시도: http://localhost:8000/chatbot/ask");
        const response = await fetch('http://localhost:8000/chatbot/ask', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error("[Chatbot Send] API 응답 오류:", response.status, errorData);
            throw new Error(`API 오류: ${errorData.message || errorData.detail || response.statusText}`);
        }

        const data = await response.json();
        console.log("[Chatbot Send] API 응답 성공. 응답 데이터:", data);

        // 로딩 메시지 제거 (DOM에서 직접 제거)
        loadingMessageDiv.remove();
        console.log("[Chatbot Send] 로딩 메시지 제거됨 (DOM에서).");

        let botResponseText = data.response || "죄송합니다. 응답 내용을 찾을 수 없습니다.";
        let botResponseImageUrl = data.image_url || null;
        let botResponseFilePath = data.file_path || null;
        let botResponseLinkUrl = data.link_url || null;

        // 봇 응답을 chatHistoryArray에 저장하고 세션 스토리지에 반영
        addMessageAndSave('bot', botResponseText, false, botResponseImageUrl, botResponseFilePath, botResponseLinkUrl);

        // 이미지 전송 후 상태 초기화 (input과 selectedImageFile)
        selectedImageFile = null;
        if (imageUploadInput) {
            imageUploadInput.value = '';
            console.log("[Chatbot Send] selectedImageFile 및 파일 input 초기화됨.");
        }

    } catch (error) {
        console.error("챗봇 통신 중 오류 발생:", error);

        loadingMessageDiv.remove(); // 오류 시에도 로딩 메시지 제거

        addMessageToChat('bot', `죄송합니다. 오류가 발생했습니다: ${error.message || '알 수 없는 오류'}`, false);
    }
}

// removeLastMessageIfLoading 함수는 이제 사용되지 않습니다. (로딩 메시지를 DOM에 직접 추가하기 때문)
function removeLastMessageIfLoading() {
    const loadingMessageDom = document.querySelector('.chat-message.bot.loading-message');
    if (loadingMessageDom) {
        loadingMessageDom.remove();
        console.log("[Chatbot Send] 레거시 로딩 메시지 제거 함수 호출됨 (제거)");
    }
}


// ----------------------------------------------------
// 이전 질문 내역 모달 관련 함수
// ----------------------------------------------------

async function showHistoryModal() {
    const modal = document.getElementById('history-modal');
    const historyList = document.getElementById('history-list');
    if (!modal || !historyList) {
        console.error("[History Modal Error] 모달 또는 히스토리 리스트 요소를 찾을 수 없습니다.");
        return;
    }

    historyList.innerHTML = '<p style="text-align: center; color: #888;">이전 질문을 불러오는 중...</p>';
    modal.style.display = 'block';
    console.log("[History Modal] 이전 질문 내역 모달 열기 시도.");

    // ★★★ USER_ID가 설정될 때까지 기다리는 로직 추가 ★★★
    if (USER_ID === null || isNaN(USER_ID)) {
        console.warn("[History Modal] USER_ID가 아직 설정되지 않았습니다. 사용자 정보를 기다리는 중...");
        const maxWaitTime = 5000; // 5초
        const startTime = Date.now();
        while ((USER_ID === null || isNaN(USER_ID)) && (Date.now() - startTime < maxWaitTime)) {
            await new Promise(resolve => setTimeout(resolve, 100)); // 0.1초 대기
        }

        if (USER_ID === null || isNaN(USER_ID)) {
            historyList.innerHTML = '<p style="text-align: center; color: red;">사용자 정보를 불러오지 못했습니다. 로그인 상태를 확인해주세요.</p>';
            console.error("[History Modal] USER_ID 로드 실패: 타임아웃 또는 유효하지 않은 값.");
            return; // USER_ID가 여전히 유효하지 않으면 함수 종료
        }
        console.log("[History Modal] USER_ID 설정 확인됨:", USER_ID);
    }

    try {
        console.log("[History Modal] API 호출 시도: /api/chatbot/history/" + USER_ID);
        const response = await fetch(`/api/chatbot/history/${USER_ID}`);
        if (!response.ok) {
            const errorData = await response.json();
            console.error("[History Modal] API 응답 오류:", response.status, errorData);
            throw new Error(`API 오류: ${errorData.message || errorData.detail || response.statusText}`);
        }
        const history = await response.json();
        console.log("[History Modal] 이전 질문 내역 로드 성공. 데이터:", history);

        historyList.innerHTML = '';
        if (history.length === 0) {
            historyList.innerHTML = '<p style="text-align: center; color: #888;">이전 질문 내역이 없습니다.</p>';
            console.log("[History Modal] 이전 질문 내역이 없습니다.");
        } else {
            history.forEach(item => {
                const queryItem = document.createElement('div');
                queryItem.className = 'history-item';

                let historyContent = `<strong>나:</strong> ${item.user_query}`;
                if (item.image_url) { // 이미지 URL이 있다면 표시
                    const fullImageUrl = `http://localhost:8000${item.image_url}`;
                    historyContent += `<br><img src="${fullImageUrl}" alt="첨부 이미지" style="max-width: 100px; max-height: 100px; border-radius: 4px; margin-top: 5px;">`;
                }
                historyContent += `<br><strong>AgroBuddy 챗봇:</strong> ${item.bot_response}`;

                if (item.file_path) { // 파일 다운로드 링크가 있다면 표시
                    const fullFileUrl = `http://localhost:8000${item.file_path}`;
                    const fileName = fullFileUrl.substring(fullFileUrl.lastIndexOf('/') + 1);
                    historyContent += `<br><a href="${fullFileUrl}" target="_blank" download style="display:inline-block; margin-top:5px; padding:5px 10px; background-color:#e0e0e0; color:#333; text-decoration:none; border-radius:3px;">[${fileName}] 다운로드</a>`;
                }
                if (item.link_url) { // 페이지 이동 링크가 있다면 표시 (기존의 "작물 진단 페이지" 문구는 없음)
                    const histLinkText = "작물 진단 페이지";
                    const histFullLinkUrl = `http://localhost:8080/${item.link_url}`;
                    historyContent += `<br><a href="${histFullLinkUrl}" target="_blank" class="chat-link-button history-link" style="color: blue; text-decoration: underline; font-weight: bold;">${histLinkText}</a>`;
                }

                queryItem.innerHTML = historyContent;

                queryItem.onclick = () => {
                    document.getElementById('chat-input').value = item.user_query;
                    closeHistoryModal();
                    console.log(`[History Modal] 이전 질문 클릭됨: "${item.user_query}"`);
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
    const modal = document.getElementById('history-modal');
    if (modal) {
        modal.style.display = 'none';
        console.log("[History Modal] 이전 질문 내역 모달 닫힘.");
    }
}

// 모달 외부 클릭 시 닫기
window.onclick = function(event) {
    const modal = document.getElementById('history-modal');
    if (modal && event.target === modal) {
        modal.style.display = "none";
        console.log("[History Modal] 모달 외부 클릭으로 히스토리 모달 닫힘.");
    }
}

// ----------------------------------------------------
// 사용자 정보 로드 함수
// ----------------------------------------------------

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
                const displayUserName = userData.nickname && userData.nickname !== 'null' && userData.nickname !== '' ? userData.nickname : (userData.username || '사용자');
                initialGreetingElement.textContent = `안녕하세요, ${displayUserName}님! 농업에 대해 궁금한 점을 물어보세요.`;
                console.log(`[User Load] 초기 환영 메시지 업데이트: ${displayUserName}님`);
            }
            if (chatHeaderTitleElement) {
                const displayUserName = userData.nickname && userData.nickname !== 'null' && userData.nickname !== '' ? userData.nickname : (userData.username || '사용자');
                chatHeaderTitleElement.textContent = `💬 ${displayUserName}님 챗봇 상담 💬`;
                console.log(`[User Load] 챗봇 헤더 타이틀 업데이트: ${displayUserName}님`);
            }

            let tempUserId = null;
            if (userData.userId !== undefined && userData.userId !== null) {
                const parsedId = Number(userData.userId);
                if (!isNaN(parsedId) && typeof parsedId === 'number') {
                    tempUserId = parsedId;
                } else {
                    console.error("[User Load] userData.userId를 유효한 숫자로 변환할 수 없습니다:", userData.userId);
                }
            } else if (userData.username) {
                const parsedId = Number(userData.username);
                if (!isNaN(parsedId)) {
                    tempUserId = parsedId;
                    console.warn("[User Load] USER_ID 설정됨 (Fallback to username):", USER_ID, " (타입:", typeof USER_ID, "). 백엔드 MainController에서 'userId'를 우선적으로 넘겨주는지 확인하세요.");
                } else {
                    console.warn("[User Load] userData.username도 유효한 숫자가 아닙니다:", userData.username);
                }
            } else {
                console.warn("[User Load] 사용자 ID(userId 또는 username)를 불러오지 못했습니다. 챗봇 기능이 제한될 수 있습니다.");
                USER_ID = null;
            }

            USER_ID = tempUserId; // 최종 USER_ID 할당
            console.log("[User Load] 최종 설정된 USER_ID:", USER_ID, " (타입:", typeof USER_ID, ")");

            // ★★★ USER_ID가 최종적으로 설정되지 않았다면 에러 메시지 표시 ★★★
            // 이 로직은 Promise가 resolve된 후에 실행되므로 안전합니다.
            if (USER_ID === null || isNaN(USER_ID)) {
                displayUserLoadError("사용자 정보를 불러오지 못했습니다. 다시 로그인해주세요.");
            } else {
                // 사용자 정보 로드 성공 후 UI 활성화
                const diagnoseButton = document.querySelector('.btn-diagnose');
                if (diagnoseButton) {
                    diagnoseButton.disabled = false;
                }
                const showDiagnosisHistoryButton = document.getElementById('showDiagnosisHistoryButton');
                if (showDiagnosisHistoryButton) {
                    showDiagnosisHistoryButton.disabled = false;
                }
                // img.html의 초기 UI 상태 복원 (로딩 메시지 제거)
                const diagnosisResultSummary = document.getElementById('diagnosisResultSummary');
                if (diagnosisResultSummary) {
                    diagnosisResultSummary.textContent = "이미지를 분석 중입니다..."; // 또는 "진단 준비 완료"
                    diagnosisResultSummary.style.color = '#333';
                }
                const diagnosisError = document.getElementById('diagnosisError');
                if (diagnosisError) {
                    diagnosisError.style.display = 'none';
                }
                console.log("[User Load] 사용자 정보 로드 성공, 관련 UI 활성화됨.");
                userLoadedPromiseResolve(true); // ★★★ USER_ID 로딩 성공 알림 ★★★
            }

        } else if (response.status === 401 || response.status === 403) {
            console.warn('[User Load] 사용자 정보 로드 실패: 인증 필요 (상태 코드:', response.status, ').');
            displayUserLoadError("로그인이 필요합니다. 다시 로그인해주세요.");
            userLoadedPromiseResolve(false); // ★★★ USER_ID 로딩 실패 알림 ★★★
        } else {
            console.error('[User Load] 사용자 정보 로드 실패 (상태 코드:', response.status, ').');
            displayUserLoadError("사용자 정보를 불러오는 중 서버 오류가 발생했습니다.");
            userLoadedPromiseResolve(false); // ★★★ USER_ID 로딩 실패 알림 ★★★
        }
    } catch (error) {
        console.error('[User Load] 사용자 정보 로드 네트워크 오류:', error);
        displayUserLoadError("네트워크 오류로 사용자 정보를 불러올 수 없습니다.");
        userLoadedPromiseResolve(false); // ★★★ USER_ID 로딩 실패 알림 ★★★
    }
}

// 사용자 정보 로드 오류 메시지 표시 헬퍼 함수
function displayUserLoadError(message) {
    const diagnosisError = document.getElementById('diagnosisError');
    const diagnosisResultSummary = document.getElementById('diagnosisResultSummary');

    if (diagnosisError) {
        diagnosisError.textContent = message;
        diagnosisError.style.display = 'block';
    }
    if (diagnosisResultSummary) {
        diagnosisResultSummary.textContent = "오류 발생";
        diagnosisResultSummary.style.color = '#D32F2F';
    }

    const diagnoseButton = document.querySelector('.btn-diagnose');
    if (diagnoseButton) {
        diagnoseButton.disabled = true;
    }
    const showDiagnosisHistoryButton = document.getElementById('showDiagnosisHistoryButton');
    if (showDiagnosisHistoryButton) {
        showDiagnosisHistoryButton.disabled = true;
    }
}

// DOMContentLoaded 시 사용자 정보 로드 함수 호출
document.addEventListener('DOMContentLoaded', loadUserNicknameForChatbot);