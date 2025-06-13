// --- 내 농장 (My Crops) 관련 더미 데이터 및 함수 ---
const userCropsData = {
    'tomato': {
        name: '토마토',
        startDate: '2025-05-01',
        potSize: '20cm 이상',
        waterAmount: '200ml (큰 컵 1잔)',
        wateringFrequency: '2~3일에 한 번 (흙 마름 확인 후)',
        soilType: '배양토 + 퇴비',
        progress: 70
    },
    'lettuce': {
        name: '상추',
        startDate: '2025-05-15',
        potSize: '15cm 이상',
        waterAmount: '100ml (작은 컵 1잔)',
        wateringFrequency: '매일 (오전)',
        soilType: '상토',
        progress: 45
    },
    'pepper': {
        name: '고추',
        startDate: '2025-06-05',
        potSize: '25cm 이상',
        waterAmount: '300ml (큰 컵 1.5잔)',
        wateringFrequency: '3일에 한 번',
        soilType: '배양토 + 마사토',
        progress: 10
    }
};

function selectCrop(cropKey) {
    const crop = userCropsData[cropKey];
    if (crop) {
        document.getElementById('detail-name').textContent = crop.name;
        document.getElementById('detail-start-date').textContent = crop.startDate;
        document.getElementById('detail-pot-size').textContent = crop.potSize;
        document.getElementById('detail-water-amount').textContent = crop.waterAmount;
        document.getElementById('detail-watering-frequency').textContent = crop.wateringFrequency;
        document.getElementById('detail-soil-type').textContent = crop.soilType;
        document.getElementById('detail-progress').textContent = `${crop.progress}%`;
        const progressBar = document.getElementById('detail-progress-bar');
        progressBar.style.width = `${crop.progress}%`;
        progressBar.textContent = `${crop.progress}%`;
    }
}

// --- 챗봇 시뮬레이션 로직 ---
function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    const message = chatInput.value.trim();
    if (message) {
        addMessageToChat('나', message, 'user');
        chatInput.value = '';

        setTimeout(() => {
            const botResponse = getBotResponse(message);
            addMessageToChat('AgroBuddy 챗봇', botResponse, 'bot');
        }, 800);
    }
}

function addMessageToChat(sender, message, type) {
    const chatHistory = document.getElementById('chat-history');
    if (!chatHistory) return; // Prevent error if chat history element doesn't exist

    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}`;
    const now = new Date();
    const time = `[${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}]`;
    
    messageDiv.innerHTML = `
        <div class="message-info">
            <span class="message-sender">${sender}</span> <span class="message-time">${time}</span>
        </div>
        <div class="message-bubble">${message}</div>
    `;
    chatHistory.appendChild(messageDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function getBotResponse(userMessage) {
    const msg = userMessage.toLowerCase();
    if (msg.includes("안녕") || msg.includes("hi")) {
        return "안녕하세요! 무엇을 도와드릴까요?";
    } else if (msg.includes("날씨")) {
        return "'작물 추천' 화면을 확인해 주세요. 더 자세한 정보가 필요하신가요?";
    } else if (msg.includes("병충해") || msg.includes("진단")) {
        return "'작물 진단' 화면에 사진을 올려주시면 상태를 진단해 드릴 수 있습니다.";
    } else if (msg.includes("재배") || msg.includes("가이드")) {
        return "재배 가이드는 '재배 가이드' 화면에서 선택한 작물에 맞춰 제공됩니다.";
    } else if (msg.includes("고마워") || msg.includes("감사")) {
        return "천만에요! 더 궁금한 점이 있으시면 언제든지 물어보세요.";
    } else if (msg.includes("화분") || msg.includes("물") || msg.includes("흙") || msg.includes("주기")) {
         return "'내 농장' 화면에서 등록된 작물을 선택하시면 관련 정보를 확인하실 수 있습니다.";
    }
    else {
        return "질문을 정확히 이해하지 못했습니다. 좀 더 구체적으로 말씀해 주시거나, 다른 화면의 기능을 이용해 보세요.";
    }
}


// --- 공통 DOMContentLoaded 이벤트 리스너 ---
document.addEventListener('DOMContentLoaded', () => {
    // 현재 페이지의 URL을 기반으로 내비게이션 바의 'active' 클래스 설정
    const currentPath = window.location.pathname.split('/').pop(); // 예: "login.html"
    const navLinks = document.querySelectorAll('.nav-bar a');

    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href').split('/').pop(); // "login.html"
        if (linkPath === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    // my_farm.html (이제 main.html) 페이지가 로드되었을 때만 실행
    if (currentPath === 'main.html') {
        const loggedInUser = localStorage.getItem('loggedInUser');
        if (loggedInUser) {
            document.getElementById('current-username-display').textContent = loggedInUser;
        } else {
            // 로그인 없이 직접 접근 시 로그인 페이지로 리다이렉트 (선택 사항)
            // alert('로그인이 필요합니다.');
            // window.location.href = 'login.html'; 
        }
        selectCrop('tomato'); // 기본 작물 선택 (실제로는 DB에서 가져올 것)
    }

    // 챗봇 관련 요소가 현재 페이지에 있을 경우에만 이벤트 리스너 바인딩
    // (6.html에서만 해당)
    const sendButton = document.getElementById('send-chat-message');
    const chatInput = document.getElementById('chat-input');
    if (sendButton && chatInput) {
        sendButton.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                sendMessage();
                e.preventDefault();
            }
        });
    }
});