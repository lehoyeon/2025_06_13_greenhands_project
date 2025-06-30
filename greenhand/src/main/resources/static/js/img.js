// 사용자 ID를 전역 변수로 선언하고 초기화되지 않은 상태로 둡니다.
let currentUserId = null;

// 햄버거 메뉴 토글 함수 (main.js 또는 global.js에 있다면 제거)
function toggleNavMenu() {
    const navLinksContainer = document.getElementById('navLinksContainer');
    if (navLinksContainer) {
        navLinksContainer.classList.toggle('active');
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    console.log("[IMG Init] DOMContentLoaded 이벤트 발생.");

    // 네비게이션 바 링크 활성화 (main.js 또는 다른 공통 스크립트에 있다면 제거)
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

    // ========================================
    // 공통 유틸리티 함수 (필요하다면 별도 파일로 분리)
    // ========================================
    function getCurrentTime() {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        return `${hours}:${minutes}`;
    }

    // ========================================
    // 사용자 ID 로드 함수 (chatbot.js에서 가져온 로직과 유사)
    // ========================================
    async function loadUserIdForDiagnosis() {
        try {
            console.log("[IMG User Load] 사용자 정보 로드 API 호출 시도: /api/main/user/me");
            const response = await fetch('/api/main/user/me');
            if (response.ok) {
                const userData = await response.json();
                if (userData.userId !== undefined && userData.userId !== null) {
                    currentUserId = userData.userId; // userId 저장
                    console.log("[IMG User Load] 현재 로그인된 사용자 ID:", currentUserId);
                } else if (userData.username) { // Fallback for Kakao ID if userId not present
                    const parsedId = parseInt(userData.username);
                    if (!isNaN(parsedId)) {
                        currentUserId = parsedId;
                        console.warn("[IMG User Load] USER_ID 설정됨 (Fallback to username - Kakao ID):", currentUserId);
                    } else {
                        console.warn("[IMG User Load] userData.username이 유효한 숫자가 아닙니다:", userData.username);
                    }
                } else {
                    console.warn("[IMG User Load] 사용자 ID를 불러오지 못했습니다. 진단 기능이 제한될 수 있습니다.");
                }
            } else {
                console.error("[IMG User Load] 사용자 정보 로드 실패:", response.status);
            }
        } catch (error) {
            console.error("[IMG User Load] 사용자 정보 로드 네트워크 오류:", error);
        }
    }

    // 페이지 로드 시 사용자 ID 로드
    await loadUserIdForDiagnosis();

    // ========================================
    // 작물 진단 기능 JavaScript
    // ========================================
    const imageUpload = document.getElementById('imageUpload');
    const imagePreview = document.getElementById('imagePreview');
    const placeholderText = document.getElementById('placeholderText');
    const uploadForm = document.getElementById('uploadForm');
    const diagnosisResultSection = document.querySelector('.diagnosis-result-section');
    const diagnosedImageDisplay = document.getElementById('diagnosedImageDisplay');

    // 새로운 결과 표시 요소들
    const diagnosisResultSummary = document.getElementById('diagnosisResultSummary');
    // const diagnosisDetailsContainer = document.getElementById('diagnosisDetailsContainer'); // 사용되지 않음. 제거 가능.
    const featureSection = document.getElementById('featureSection');
    const featureContent = document.getElementById('featureContent');
    const causeSection = document.getElementById('causeSection');
    const causeContent = document.getElementById('causeContent');
    const solutionSection = document.getElementById('solutionSection');
    const solutionContent = document.getElementById('solutionContent');
    const detailsFallback = document.getElementById('detailsFallback'); // 파싱 실패 시 대체 텍스트

    const diagnosisSeverity = document.getElementById('diagnosisSeverity');
    const diagnosisPlantName = document.getElementById('diagnosisPlantName');

    const promptTextarea = document.getElementById('prompt-text');
    const diagnoseButton = document.querySelector('.btn-diagnose');
    const diagnosisError = document.getElementById('diagnosisError');
    const viewDetailsBtn = document.getElementById('viewDetailsBtn');
    const showDiagnosisHistoryButton = document.getElementById('showDiagnosisHistoryButton');

    // 이미지 선택 시 미리보기 표시 및 결과 영역 초기화
    imageUpload.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                imagePreview.src = e.target.result;
                imagePreview.style.display = 'block';
                placeholderText.style.display = 'none';
            };
            reader.readAsDataURL(file);
            // 결과 영역 초기화
            resetDiagnosisUI(); // UI 초기화 함수 호출
            diagnoseButton.disabled = false;
        } else {
            imagePreview.src = '#';
            imagePreview.style.display = 'none';
            placeholderText.style.display = 'block';
            resetDiagnosisUI(); // UI 초기화 함수 호출
            diagnoseButton.disabled = true;
        }
    });

    // UI 초기화 헬퍼 함수
    function resetDiagnosisUI() {
        diagnosisResultSection.style.display = 'none';
        diagnosisResultSummary.textContent = '이미지를 분석 중입니다...'; // 제목 초기화
        diagnosisResultSummary.style.color = ''; // 색상 초기화
        featureContent.textContent = '';
        causeContent.textContent = '';
        solutionContent.textContent = '';
        detailsFallback.textContent = '';
        detailsFallback.style.display = 'none'; // 대체 텍스트 숨김
        featureSection.style.display = 'none'; // 섹션 숨김
        causeSection.style.display = 'none'; // 섹션 숨김
        solutionSection.style.display = 'none'; // 섹션 숨김
        diagnosisSeverity.textContent = '알 수 없음';
        diagnosisPlantName.textContent = '알 수 없음';
        diagnosedImageDisplay.style.display = 'none';
        diagnosisError.style.display = 'none';
        viewDetailsBtn.style.display = 'none';
    }


    // 폼 제출 (이미지 업로드 및 진단 요청)
    uploadForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        // UI 초기화 및 로딩 메시지
        diagnosisResultSection.style.display = 'block';
        diagnosisResultSummary.textContent = '이미지를 분석 중입니다...'; // 요약 영역에 로딩 메시지
        diagnosisResultSummary.style.color = '#616161'; // 로딩 메시지 색상
        featureContent.textContent = '';
        causeContent.textContent = '';
        solutionContent.textContent = '';
        detailsFallback.style.display = 'none';
        diagnosisSeverity.textContent = '알 수 없음';
        diagnosisPlantName.textContent = '알 수 없음';
        diagnosisError.style.display = 'none';
        diagnoseButton.disabled = true;
        diagnosedImageDisplay.style.display = 'none';
        viewDetailsBtn.style.display = 'none';

        const file = imageUpload.files[0];
        if (!file) {
            displayError("파일을 선택해주세요.");
            diagnoseButton.disabled = false;
            return;
        }
        if (currentUserId === null) {
            displayError("사용자 정보를 불러오지 못했습니다. 다시 로그인해주세요.");
            diagnoseButton.disabled = false;
            return;
        }

        try {
            const formData = new FormData();
            formData.append('imageFile', file);
            formData.append('prompt', promptTextarea.value.trim());
            formData.append('userId', currentUserId);

            console.log("[IMG JS] 진단 요청 FormData:", formData);

            const response = await fetch('/api/diagnose/plant', {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                const data = await response.json();
                console.log("[IMG JS] Spring Boot에서 받은 최종 진단 성공 데이터:", data);

                // AI 진단 결과 요약 (diagnosis_result)
                diagnosisResultSummary.textContent = `진단 결과: ${data.diagnosis_result || "정보 없음"}`;
                diagnosisResultSummary.style.color = '#4CAF50';

                // 상세 진단 내용 (diagnosis_details) 파싱 및 표시
                const detailsText = data.diagnosis_details || '';

                // 정규 표현식을 사용하여 각 섹션 추출 (더 유연하게 변경)
                // '특징:', '원인:', '해결 방안:' 키워드를 찾고 그 다음 키워드 또는 문자열 끝까지 텍스트를 추출
                // g (global) 플래그를 제거하여 첫 번째 매치만 찾고, 각 부분을 독립적으로 추출
                // ?: 비캡처 그룹으로 만들어 매치 결과에서 불필요한 그룹 제거
                // s (dotAll) 플래그로 . 이 줄바꿈도 포함하도록
                const featureMatch = detailsText.match(/특징:\s*(.*?)(?:\n\n원인:|\n원인:|$)/s);
                const causeMatch = detailsText.match(/원인:\s*(.*?)(?:\n\n해결 방안:|\n해결 방안:|$)/s);
                const solutionMatch = detailsText.match(/해결 방안:\s*(.*)/s);


                let parsedFeature = featureMatch && featureMatch[1] ? featureMatch[1].trim() : '';
                let parsedCause = causeMatch && causeMatch[1] ? causeMatch[1].trim() : '';
                let parsedSolution = solutionMatch && solutionMatch[1] ? solutionMatch[1].trim() : '';

                // 파싱된 내용이 없으면 '정보 없음'으로 설정
                featureContent.textContent = parsedFeature || '정보 없음';
                causeContent.textContent = parsedCause || '정보 없음';
                solutionContent.textContent = parsedSolution || '정보 없음';

                // 모든 섹션이 파싱되었고, 내용이 있다면 섹션을 표시
                if (parsedFeature !== '' || parsedCause !== '' || parsedSolution !== '') {
                    detailsFallback.style.display = 'none';
                    featureSection.style.display = 'block';
                    causeSection.style.display = 'block';
                    solutionSection.style.display = 'block';
                } else if (detailsText.trim() !== '') {
                    // 파싱은 안 됐지만 원본 텍스트가 있다면 대체 텍스트로 표시
                    detailsFallback.textContent = "상세 정보를 파싱할 수 없습니다. 원본 내용: " + detailsText;
                    detailsFallback.style.display = 'block';
                    featureSection.style.display = 'none';
                    causeSection.style.display = 'none';
                    solutionSection.style.display = 'none';
                } else {
                    // 원본 텍스트도 없다면 "상세 정보 없음" 표시
                    detailsFallback.textContent = '상세 정보 없음';
                    detailsFallback.style.display = 'block';
                    featureSection.style.display = 'none';
                    causeSection.style.display = 'none';
                    solutionSection.style.display = 'none';
                }


                // 심각도 및 작물명 표시
                diagnosisSeverity.textContent = data.severity || '알 수 없음';
                diagnosisPlantName.textContent = data.plant_name || '알 수 없음';

                // 진단된 이미지 표시 (서버에서 반환된 image_url 사용)
                if (data.image_url) {
                    diagnosedImageDisplay.src = data.image_url;
                    diagnosedImageDisplay.style.display = 'block';
                }

                localStorage.setItem('lastDiagnosisResult', JSON.stringify(data));
                localStorage.setItem('lastDiagnosedImageUrl', data.image_url || '');
                viewDetailsBtn.style.display = 'block';

            } else {
                const errorData = await response.json();
                console.error("진단 실패:", errorData);
                displayError(errorData.message || "진단 중 알 수 없는 오류 발생했습니다.");
            }
        } catch (error) {
            console.error('네트워크 오류:', error);
            displayError("네트워크 오류가 발생했거나 서버에 연결할 수 없습니다.");
        } finally {
            diagnoseButton.disabled = false;
        }
    });

    // 오류 메시지 표시 헬퍼 함수
    function displayError(message) {
        diagnosisResultSection.style.display = 'block'; // 에러 발생 시 결과 섹션 보이게
        diagnosisResultSummary.textContent = `오류: ${message}`; // 요약 영역에 에러 표시
        diagnosisResultSummary.style.color = '#D32F2F'; // 에러 메시지 색상
        featureContent.textContent = '';
        causeContent.textContent = '';
        solutionContent.textContent = '';
        detailsFallback.textContent = ''; // 대체 텍스트도 비움
        detailsFallback.style.display = 'none';
        featureSection.style.display = 'none';
        causeSection.style.display = 'none';
        solutionSection.style.display = 'none';
        diagnosisSeverity.textContent = '알 수 없음';
        diagnosisPlantName.textContent = '알 수 없음';

        diagnosisError.textContent = message; // 하단에 에러 메시지 표시
        diagnosisError.style.display = 'block';
        diagnosedImageDisplay.style.display = 'none';
        viewDetailsBtn.style.display = 'none';
    }

    // '자세한 진단 결과 확인' 버튼 클릭 이벤트
    if (viewDetailsBtn) {
        viewDetailsBtn.addEventListener('click', function() {
            window.location.href = '/img_results.html'; // 결과 페이지로 이동
        });
    }

    // ========================================
    // 이전 진단 내역 모달 관련 JavaScript
    // ========================================
    const diagnosisHistoryModal = document.getElementById('diagnosisHistoryModal');
    const diagnosisHistoryList = document.getElementById('diagnosisHistoryList');
    const closeDiagnosisHistoryModalButton = diagnosisHistoryModal ? diagnosisHistoryModal.querySelector('.close-button') : null;

    if (showDiagnosisHistoryButton) {
        showDiagnosisHistoryButton.addEventListener('click', openDiagnosisHistoryModal);
    }
    if (closeDiagnosisHistoryModalButton) {
        closeDiagnosisHistoryModalButton.addEventListener('click', closeDiagnosisHistoryModal);
    }

    async function openDiagnosisHistoryModal() {
        if (!diagnosisHistoryModal || !diagnosisHistoryList) return;

        diagnosisHistoryList.innerHTML = '<p style="text-align: center; color: #888;">이전 진단 내역을 불러오는 중...</p>';
        diagnosisHistoryModal.style.display = 'block';
        console.log("[IMG History Modal] 이전 진단 내역 모달 열기 시도.");

        if (currentUserId === null || isNaN(currentUserId)) {
            diagnosisHistoryList.innerHTML = '<p style="text-align: center; color: red;">사용자 정보를 불러오지 못했습니다. 로그인 상태를 확인해주세요.</p>';
            console.warn("[IMG History Modal] currentUserId가 NULL이거나 NaN입니다. 이전 진단 내역을 불러올 수 없습니다.");
            return;
        }

        try {
            console.log("[IMG History Modal] API 호출 시도: /api/diagnose/history/" + currentUserId);
            const response = await fetch(`/api/diagnose/history/${currentUserId}`);
            if (!response.ok) {
                const errorData = await response.json();
                console.error("[IMG History Modal] API 응답 오류:", response.status, errorData);
                throw new Error(`API 오류: ${errorData.message || response.statusText}`);
            }
            const history = await response.json();
            console.log("[IMG History Modal] 이전 진단 내역 로드 성공. 데이터:", history);

            diagnosisHistoryList.innerHTML = '';
            if (history.length === 0) {
                diagnosisHistoryList.innerHTML = '<p style="text-align: center; color: #888;">이전 진단 내역이 없습니다.</p>';
                console.log("[IMG History Modal] 이전 진단 내역이 없습니다.");
            } else {
                history.forEach(item => {
                    const historyItem = document.createElement('div');
                    historyItem.className = 'history-item';
                    historyItem.style.marginBottom = '15px';
                    historyItem.style.padding = '10px';
                    historyItem.style.border = '1px solid #ddd';
                    historyItem.style.borderRadius = '8px';
                    historyItem.style.backgroundColor = '#fff';
                    historyItem.style.boxShadow = '0 2px 5px rgba(0,0,0,0.05)';

                    let historyContent = `
                        <p><strong>진단 시각:</strong> ${new Date(item.diagnosedAt).toLocaleString('ko-KR')}</p>
                        <p><strong>진단 결과:</strong> ${item.diagnosisResult}</p>
                    `;
                    // 상세 내용 파싱하여 표시
                    const detailsText = item.diagnosisDetails || '';
                    // 정규 표현식 수정 (더 유연하게 줄바꿈 및 공백 처리)
                    const featureMatch = detailsText.match(/특징:\s*(.*?)(?:\r?\n\s*\r?\n\s*원인:|\r?\n원인:|$)/s);
                    const causeMatch = detailsText.match(/원인:\s*(.*?)(?:\r?\n\s*\r?\n\s*해결 방안:|\r?\n해결 방안:|$)/s);
                    const solutionMatch = detailsText.match(/해결 방안:\s*(.*)/s);

                    const parsedFeature = featureMatch && featureMatch[1] ? featureMatch[1].trim() : '정보 없음';
                    const parsedCause = causeMatch && causeMatch[1] ? causeMatch[1].trim() : '정보 없음';
                    const parsedSolution = solutionMatch && solutionMatch[1] ? solutionMatch[1].trim() : '정보 없음';

                    historyContent += `
                        <div class="history-detail-section">
                            <p><strong>특징:</strong> ${parsedFeature}</p>
                        </div>
                        <div class="history-detail-section">
                            <p><strong>원인:</strong> ${parsedCause}</p>
                        </div>
                        <div class="history-detail-section">
                            <p><strong>해결 방안:</strong> ${parsedSolution}</p>
                        </div>
                    `;

                    historyContent += `
                        ${item.severity ? `<p><strong>심각도:</strong> ${item.severity}</p>` : ''}
                        ${item.plantName ? `<p><strong>작물명:</strong> ${item.plantName}</p>` : ''}
                    `;
                    if (item.imageUrl) {
                        historyContent += `<p><img src="${item.imageUrl}" alt="진단 이미지" style="max-width: 150px; height: auto; border-radius: 4px; margin-top: 10px;"></p>`;
                    }
                    historyItem.innerHTML = historyContent;

                    diagnosisHistoryList.appendChild(historyItem);
                });
                console.log("[IMG History Modal] 이전 진단 내역 표시 완료.");
            }

        } catch (error) {
            console.error("이전 진단 내역 로드 중 오류 발생:", error);
            diagnosisHistoryList.innerHTML = `<p style="color: red; text-align: center;">오류 발생: ${error.message}</p>`;
        }
    }

    function closeDiagnosisHistoryModal() {
        if (diagnosisHistoryModal) {
            diagnosisHistoryModal.style.display = 'none';
            console.log("[IMG History Modal] 이전 진단 내역 모달 닫힘.");
        }
    }

    // 모달 외부 클릭 시 닫기
    window.onclick = function(event) {
        if (diagnosisHistoryModal && event.target === diagnosisHistoryModal) {
            closeDiagnosisHistoryModal();
        }
    };
});
