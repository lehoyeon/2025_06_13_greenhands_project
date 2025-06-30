document.addEventListener('DOMContentLoaded', function () {
    const params = new URLSearchParams(window.location.search);

    // 로그인/로그아웃/회원가입 성공 메시지 표시 로직
    const errorMessage = document.getElementById('login-error-message');
    const logoutMessage = document.getElementById('logout-success-message');
    const signupMessage = document.getElementById('signup-success-message');

    if (params.has('error')) {
        if (errorMessage) errorMessage.style.display = 'block';
    } else {
        if (errorMessage) errorMessage.style.display = 'none';
    }

    if (params.has('logout')) {
        if (logoutMessage) logoutMessage.style.display = 'block';
    } else {
        if (logoutMessage) logoutMessage.style.display = 'none';
    }

    if (params.has('signupSuccess')) {
        if (signupMessage) {
            signupMessage.style.display = 'block';
        } else {
            // 메시지 요소가 없으면 alert 사용
            alert("✅ 회원가입이 성공적으로 완료되었습니다!");
        }
    }

    // URL 파라미터 정리 (팝업 재표시 방지)
    const newUrl = new URL(window.location.href);
    ['error', 'logout', 'signupSuccess'].forEach(p => newUrl.searchParams.delete(p));
    window.history.replaceState({}, document.title, newUrl.toString());

    // ========================================
    // 아이디/비밀번호 찾기 모달 관련 JavaScript
    // ========================================
    const openFindAccountModalBtn = document.getElementById('openFindAccountModal');
    const findAccountModal = document.getElementById('findAccountModal');
    const findIdTab = document.getElementById('findIdTab');
    const resetPwTab = document.getElementById('resetPwTab');
    const findIdSection = document.getElementById('findIdSection');
    const resetPwSection = document.getElementById('resetPwSection');
    const findIdForm = document.getElementById('findIdForm');
    const resetPwForm = document.getElementById('resetPwForm');
    const findIdResult = document.getElementById('findIdResult');
    const resetPwResult = document.getElementById('resetPwResult');

    if (openFindAccountModalBtn) {
        openFindAccountModalBtn.addEventListener('click', function (event) {
            event.preventDefault();
            findAccountModal.style.display = 'flex';
            findIdTab.click(); // 아이디 찾기 탭을 기본으로 활성화
        });
    }

    // 전역 스코프에 함수를 두어 HTML에서 직접 호출 가능하게 함
    window.closeFindAccountModal = function () {
        findAccountModal.style.display = 'none';
        findIdResult.style.display = 'none';
        resetPwResult.style.display = 'none';
        findIdForm.reset();
        resetPwForm.reset();
    }

    window.addEventListener('click', function (event) {
        if (event.target == findAccountModal) {
            closeFindAccountModal();
        }
    });

    findIdTab.addEventListener('click', () => {
        findIdTab.classList.add('active');
        resetPwTab.classList.remove('active');
        findIdSection.classList.add('active');
        resetPwSection.classList.remove('active');
        findIdResult.style.display = 'none';
        resetPwResult.style.display = 'none';
        findIdForm.reset();
    });

    resetPwTab.addEventListener('click', () => {
        resetPwTab.classList.add('active');
        findIdTab.classList.remove('active');
        findIdSection.classList.remove('active');
        resetPwSection.classList.add('active');
        findIdResult.style.display = 'none';
        resetPwResult.style.display = 'none';
        resetPwForm.reset();
    });

    findIdForm.addEventListener('submit', async function (event) {
        event.preventDefault();
        findIdResult.style.display = 'none';

        const email = document.getElementById('findIdEmail').value.trim();
        const phoneNumber = document.getElementById('findIdPhoneNumber').value.trim().replace(/-/g, '');

        if (!email || !phoneNumber) {
            displayResult(findIdResult, "이메일과 전화번호를 모두 입력해주세요.", 'error');
            return;
        }

        try {
            const response = await fetch('/api/find-id', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, phoneNumber })
            });

            const contentType = response.headers.get("content-type") || "";

            if (response.ok && contentType.includes("application/json")) {
                const data = await response.json();
                displayResult(findIdResult, `찾으시는 아이디: ${data.username}`, 'success');
            } else {
                const errorText = await response.text();
                displayResult(findIdResult, "아이디 찾기 실패: " + errorText, 'error');
            }
        } catch (error) {
            console.error('아이디 찾기 네트워크 오류:', error);
            displayResult(findIdResult, "네트워크 오류가 발생했습니다.", 'error');
        }
    });

    resetPwForm.addEventListener('submit', async function (event) {
        event.preventDefault();
        resetPwResult.style.display = 'none';

        const username = document.getElementById('resetPwUsername').value.trim();
        const phoneNumber = document.getElementById('resetPwPhoneNumber').value.trim().replace(/-/g, '');

        if (!username || !phoneNumber) {
            displayResult(resetPwResult, "아이디와 전화번호를 모두 입력해주세요.", 'error');
            return;
        }

        try {
            const response = await fetch('/api/reset-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, phoneNumber })
            });

            const contentType = response.headers.get("content-type") || "";

            if (response.ok && contentType.includes("application/json")) {
                const data = await response.json();
                displayResult(resetPwResult, data.message, 'success');
            } else {
                const errorText = await response.text();
                displayResult(resetPwResult, "비밀번호 재설정 실패: " + errorText, 'error');
            }
        } catch (error) {
            console.error('비밀번호 재설정 네트워크 오류:', error);
            displayResult(resetPwResult, "네트워크 오류가 발생했습니다.", 'error');
        }
    });

    function displayResult(element, message, type) {
        element.textContent = message;
        element.classList.remove('success', 'error');
        element.classList.add(type);
        element.style.display = 'block';
    }
});