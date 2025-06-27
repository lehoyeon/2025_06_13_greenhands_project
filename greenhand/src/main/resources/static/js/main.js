// 햄버거 메뉴 토글 함수
function toggleNavMenu() {
    const navLinksContainer = document.getElementById('navLinksContainer');
    navLinksContainer.classList.toggle('active');
}

// 페이지 로드 시, nav-bar의 '내 농장' 링크를 활성화하고 사용자 정보 로드
document.addEventListener('DOMContentLoaded', () => {
    // 현재 URL의 마지막 부분(파일 이름)을 가져옵니다.
    const currentPath = window.location.pathname.split('/').pop();
    const navLinks = document.querySelectorAll('.nav-bar a');

    navLinks.forEach(link => {
        // 링크의 href 속성에서 마지막 부분(파일 이름)을 가져옵니다.
        const linkPath = link.getAttribute('href').split('/').pop();

        // 현재 페이지의 파일 이름과 링크의 파일 이름이 일치하면 'active' 클래스 추가
        if (linkPath === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    // '내 농장' 페이지 로드 시 사용자 이름 로드
    loadUserInfo();
});

// --- 사용자 정보 로드 (AJAX) ---
async function loadUserInfo() {
    try {
        const response = await fetch('/api/main/user/me'); // 사용자 정보 API 엔드포인트
        if (response.ok) {
            const userData = await response.json();
            const usernameDisplay = document.getElementById('current-username-display');
            if (usernameDisplay) {
                // 닉네임이 있으면 닉네임, 없으면 아이디 사용
                const displayUserName = userData.nickname && userData.nickname !== 'null' && userData.nickname !== '' ? userData.nickname : (userData.username || '사용자');
                usernameDisplay.textContent = `${displayUserName}님의 농장`; // 사용자명 표시
            }
        } else if (response.status === 401 || response.status === 403) {
            console.warn('사용자 정보 로드 실패: 인증 필요. 로그인 페이지로 리다이렉트.');
            // Spring Security가 보호하므로 일반적으로 자동으로 로그인 페이지로 리다이렉트됨
        } else {
            console.error('사용자 정보 로드 실패:', response.status);
            const usernameDisplay = document.getElementById('current-username-display');
            if(usernameDisplay) usernameDisplay.textContent = '정보 로드 실패';
        }
    } catch (error) {
        console.error('사용자 정보 로드 네트워크 오류:', error);
        const usernameDisplay = document.getElementById('current-username-display');
        if(usernameDisplay) usernameDisplay.textContent = '정보 로드 실패';
    }
}
