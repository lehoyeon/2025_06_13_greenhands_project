// js/img.js

// currentUserId 대신 chatbot_core.js의 USER_ID 전역 변수를 사용합니다.
// 따라서 이 파일에서 currentUserId를 선언하거나 loadUserIdForDiagnosis를 호출할 필요가 없습니다.

document.addEventListener('DOMContentLoaded', async () => {
    console.log("[IMG Init] DOMContentLoaded 이벤트 발생.");

    // 네비게이션 바 링크 활성화 (main.js 또는 다른 공통 스크립트에 있다면 제거)
    // 이 부분은 main.js에서 처리하는 것이 일반적입니다. 여기서는 중복 가능성이 있으므로 필요에 따라 제거합니다.
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
    // 작물 진단 기능 JavaScript
    // ========================================
    const imageUpload = document.getElementById('imageUpload');
    const imagePreview = document.getElementById('imagePreview');
    const placeholderText = document.getElementById('placeholderText');
    const uploadForm = document.getElementById('uploadForm');
    const diagnosisResultSection = document.querySelector('.diagnosis-result-section');
    const diagnosedImageDisplay = document.getElementById('diagnosedImageDisplay');

    // 결과 표시 요소들
    const diagnosisResultSummary = document.getElementById('diagnosisResultSummary');
    const featureSection = document.getElementById('featureSection');
    const featureContent = document.getElementById('featureContent');
    const causeSection = document.getElementById('causeSection');
    const causeContent = document.getElementById('causeContent');
    const solutionSection = document.getElementById('solutionSection');
    const solutionContent = document.getElementById('solutionContent');
    const detailsFallback = document.getElementById('detailsFallback');
    const diagnosisSeverity = document.getElementById('diagnosisSeverity');
    const diagnosisPlantName = document.getElementById('diagnosisPlantName');

    const promptTextarea = document.getElementById('prompt-text');
    const diagnoseButton = document.querySelector('.btn-diagnose');
    const diagnosisError = document.getElementById('diagnosisError');
    // viewDetailsBtn은 HTML에 없으므로 변수 선언 및 관련 로직 모두 제거합니다.


    // 이미지 선택 시 미리보기 표시 및 결과 영역 초기화
    if (imageUpload && imagePreview && placeholderText && diagnoseButton) {
        imageUpload.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    if (imagePreview) {
                        imagePreview.src = e.target.result;
                        imagePreview.style.display = 'block';
                    }
                    if (placeholderText) {
                        placeholderText.style.display = 'none';
                    }
                };
                reader.readAsDataURL(file);
                resetDiagnosisUI(); // UI 초기화 함수 호출
                diagnoseButton.disabled = false;
            } else {
                if (imagePreview) {
                    imagePreview.src = '#';
                    imagePreview.style.display = 'none';
                }
                if (placeholderText) {
                    placeholderText.style.display = 'block';
                }
                resetDiagnosisUI(); // UI 초기화 함수 호출
                diagnoseButton.disabled = true;
            }
        });
    }


    // UI 초기화 헬퍼 함수
    function resetDiagnosisUI() {
        console.log("[IMG JS] resetDiagnosisUI: UI 초기화 시작");

        // 모든 요소를 가져올 때 null 체크를 추가하여 오류 방지
        const currentDiagnosisResultSection = document.querySelector('.diagnosis-result-section');
        const currentDiagnosisResultSummary = document.getElementById('diagnosisResultSummary');
        const currentFeatureContent = document.getElementById('featureContent');
        const currentCauseContent = document.getElementById('causeContent');
        const currentSolutionContent = document.getElementById('solutionContent');
        const currentDetailsFallback = document.getElementById('detailsFallback');
        const currentFeatureSection = document.getElementById('featureSection');
        const currentCauseSection = document.getElementById('causeSection');
        const currentSolutionSection = document.getElementById('solutionSection');
        const currentDiagnosisSeverity = document.getElementById('diagnosisSeverity');
        const currentDiagnosisPlantName = document.getElementById('diagnosisPlantName');
        const currentDiagnosedImageDisplay = document.getElementById('diagnosedImageDisplay');
        const currentDiagnosisError = document.getElementById('diagnosisError');

        if (currentDiagnosisResultSection) currentDiagnosisResultSection.style.display = 'none';
        if (currentDiagnosisResultSummary) {
            currentDiagnosisResultSummary.textContent = '이미지를 분석 중입니다...'; // 제목 초기화
            currentDiagnosisResultSummary.style.color = ''; // 색상 초기화
        }
        if (currentFeatureContent) currentFeatureContent.textContent = '';
        if (currentCauseContent) currentCauseContent.textContent = '';
        if (currentSolutionContent) currentSolutionContent.textContent = '';
        if (currentDetailsFallback) {
            currentDetailsFallback.textContent = '';
            currentDetailsFallback.style.display = 'none';
        }
        if (currentFeatureSection) currentFeatureSection.style.display = 'none';
        if (currentCauseSection) currentCauseSection.style.display = 'none';
        if (currentSolutionSection) currentSolutionSection.style.display = 'none';
        if (currentDiagnosisSeverity) currentDiagnosisSeverity.textContent = '알 수 없음';
        if (currentDiagnosisPlantName) currentDiagnosisPlantName.textContent = '알 수 없음';
        if (currentDiagnosedImageDisplay) currentDiagnosedImageDisplay.style.display = 'none';
        if (currentDiagnosisError) currentDiagnosisError.style.display = 'none';
        console.log("[IMG JS] resetDiagnosisUI: UI 초기화 완료");
    }


    // 폼 제출 (이미지 업로드 및 진단 요청)
    if (uploadForm && diagnoseButton && promptTextarea) {
        uploadForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            // UI 초기화 및 로딩 메시지
            resetDiagnosisUI(); // UI 초기화 함수 호출
            // 이미 resetDiagnosisUI에서 display='none'으로 설정했으므로 다시 'block'으로 설정
            if (diagnosisResultSection) diagnosisResultSection.style.display = 'block';
            if (diagnosisResultSummary) {
                diagnosisResultSummary.textContent = '이미지를 분석 중입니다...'; // 요약 영역에 로딩 메시지
                diagnosisResultSummary.style.color = '#616161'; // 로딩 메시지 색상
            }
            diagnoseButton.disabled = true;
            if (diagnosedImageDisplay) diagnosedImageDisplay.style.display = 'none';

            const file = imageUpload.files[0];
            if (!file) {
                displayError("파일을 선택해주세요.");
                diagnoseButton.disabled = false;
                return;
            }
            // USER_ID는 chatbot_core.js에서 전역으로 관리됩니다.
            // USER_ID가 정의되어 있는지 확인합니다.
            // USER_ID 변수는 chatbot_core.js에서 전역으로 선언되어야 합니다. (예: window.USER_ID = ... 또는 var USER_ID = ...)
            if (typeof USER_ID === 'undefined' || USER_ID === null || isNaN(USER_ID)) {
                displayError("사용자 정보를 불러오지 못했습니다. 다시 로그인해주세요.");
                diagnoseButton.disabled = false;
                return;
            }

            try {
                const formData = new FormData();
                formData.append('imageFile', file);
                formData.append('prompt', promptTextarea.value.trim());
                formData.append('userId', USER_ID); // USER_ID 사용

                console.log("[IMG JS] 진단 요청 FormData:", formData);

                const response = await fetch('/api/diagnose/plant', {
                    method: 'POST',
                    body: formData,
                });

                if (response.ok) {
                    const data = await response.json();
                    console.log("[IMG JS] Spring Boot에서 받은 최종 진단 성공 데이터:", data);

                    // AI 진단 결과 요약 (diagnosis_result)
                    if (diagnosisResultSummary) diagnosisResultSummary.textContent = `진단 결과: ${data.diagnosis_result || "정보 없음"}`;
                    if (diagnosisResultSummary) diagnosisResultSummary.style.color = '#4CAF50';

                    // 상세 진단 내용 (diagnosis_details) 파싱 및 표시
                    const detailsText = data.diagnosis_details || '';

                    // 정규표현식 수정: 각 섹션 뒤에 개행 문자가 0개 이상 있을 수 있도록 ? 앞에 * 추가
                    const featureMatch = detailsText.match(/특징:\s*(.*?)(?:\r?\n\s*\r?\n*\s*원인:|\r?\n원인:|$)/s);
                    const causeMatch = detailsText.match(/원인:\s*(.*?)(?:\r?\n\s*\r?\n*\s*해결 방안:|\r?\n해결 방안:|$)/s);
                    const solutionMatch = detailsText.match(/해결 방안:\s*(.*)/s);

                    let parsedFeature = featureMatch && featureMatch[1] ? featureMatch[1].trim() : '';
                    let parsedCause = causeMatch && causeMatch[1] ? causeMatch[1].trim() : '';
                    let parsedSolution = solutionMatch && solutionMatch[1] ? solutionMatch[1].trim() : '';

                    // 파싱된 내용이 없으면 '정보 없음'으로 설정
                    if (featureContent) featureContent.textContent = parsedFeature || '정보 없음';
                    if (causeContent) causeContent.textContent = parsedCause || '정보 없음';
                    if (solutionContent) solutionContent.textContent = parsedSolution || '정보 없음';

                    // 모든 섹션이 파싱되었고, 내용이 있다면 섹션을 표시
                    // '정보 없음'도 내용으로 간주되므로 조건 수정: 실제 내용이 파싱되지 않았을 때만 대체 텍스트 표시
                    if (featureSection) featureSection.style.display = (parsedFeature && parsedFeature !== '정보 없음') ? 'block' : 'none';
                    if (causeSection) causeSection.style.display = (parsedCause && parsedCause !== '정보 없음') ? 'block' : 'none';
                    if (solutionSection) solutionSection.style.display = (parsedSolution && parsedSolution !== '정보 없음') ? 'block' : 'none';


                    // detailsFallback 처리 로직 개선
                    if (!parsedFeature && !parsedCause && !parsedSolution && detailsText.trim() !== '') {
                        // 파싱은 안 됐지만 원본 텍스트가 있다면 대체 텍스트로 표시
                        if (detailsFallback) {
                            detailsFallback.textContent = "상세 정보를 파싱할 수 없습니다. 원본 내용: " + detailsText;
                            detailsFallback.style.display = 'block';
                        }
                    } else if (!parsedFeature && !parsedCause && !parsedSolution && detailsText.trim() === '') {
                         // 원본 텍스트도 없다면 "상세 정보 없음" 표시
                        if (detailsFallback) {
                            detailsFallback.textContent = '상세 정보 없음';
                            detailsFallback.style.display = 'block';
                        }
                    } else {
                        // 파싱된 내용이 하나라도 있거나 원본 텍스트가 비어있지 않으면 detailsFallback 숨김
                        if (detailsFallback) detailsFallback.style.display = 'none';
                    }

                    // 심각도 및 작물명 표시
                    if (diagnosisSeverity) diagnosisSeverity.textContent = data.severity || '알 수 없음';
                    if (diagnosisPlantName) diagnosisPlantName.textContent = data.plant_name || '알 수 없음';

                    // 진단된 이미지 표시 (서버에서 반환된 image_url 사용)
                    if (data.image_url) {
                        if (diagnosedImageDisplay) {
                            diagnosedImageDisplay.src = data.image_url;
                            diagnosedImageDisplay.style.display = 'block';
                        }
                    }

                    localStorage.setItem('lastDiagnosisResult', JSON.stringify(data));
                    localStorage.setItem('lastDiagnosedImageUrl', data.image_url || '');

                } else {
                    const errorData = await response.json();
                    console.error("[IMG JS] 진단 실패:", errorData);
                    displayError(errorData.message || "진단 중 알 수 없는 오류 발생했습니다.");
                }
            } catch (error) {
                console.error('[IMG JS] 네트워크 오류:', error);
                displayError("네트워크 오류가 발생했거나 서버에 연결할 수 없습니다.");
            } finally {
                diagnoseButton.disabled = false;
            }
        });
    }


    // 오류 메시지 표시 헬퍼 함수
    function displayError(message) {
        // 모든 요소를 가져올 때 null 체크를 추가하여 오류 방지
        const currentDiagnosisResultSection = document.querySelector('.diagnosis-result-section');
        const currentDiagnosisResultSummary = document.getElementById('diagnosisResultSummary');
        const currentFeatureContent = document.getElementById('featureContent');
        const currentCauseContent = document.getElementById('causeContent');
        const currentSolutionContent = document.getElementById('solutionContent');
        const currentDetailsFallback = document.getElementById('detailsFallback');
        const currentFeatureSection = document.getElementById('featureSection');
        const currentCauseSection = document.getElementById('causeSection');
        const currentSolutionSection = document.getElementById('solutionSection');
        const currentDiagnosisSeverity = document.getElementById('diagnosisSeverity');
        const currentDiagnosisPlantName = document.getElementById('diagnosisPlantName');
        const currentDiagnosisError = document.getElementById('diagnosisError');
        const currentDiagnosedImageDisplay = document.getElementById('diagnosedImageDisplay');


        if (currentDiagnosisResultSection) currentDiagnosisResultSection.style.display = 'block';
        if (currentDiagnosisResultSummary) {
            currentDiagnosisResultSummary.textContent = `오류: ${message}`;
            currentDiagnosisResultSummary.style.color = '#D32F2F';
        }
        if (currentFeatureContent) currentFeatureContent.textContent = '';
        if (currentCauseContent) currentCauseContent.textContent = '';
        if (currentSolutionContent) currentSolutionContent.textContent = '';
        if (currentDetailsFallback) {
            currentDetailsFallback.textContent = '';
            currentDetailsFallback.style.display = 'none';
        }
        if (currentFeatureSection) currentFeatureSection.style.display = 'none';
        if (currentCauseSection) currentCauseSection.style.display = 'none';
        if (currentSolutionSection) currentSolutionSection.style.display = 'none';
        if (currentDiagnosisSeverity) currentDiagnosisSeverity.textContent = '알 수 없음';
        if (currentDiagnosisPlantName) currentDiagnosisPlantName.textContent = '알 수 없음';

        if (currentDiagnosisError) {
            currentDiagnosisError.textContent = message;
            currentDiagnosisError.style.display = 'block';
        }
        if (currentDiagnosedImageDisplay) currentDiagnosedImageDisplay.style.display = 'none';
    }


    // ========================================
    // 이전 진단 내역 모달 관련 JavaScript
    // ========================================
    const diagnosisHistoryModal = document.getElementById('diagnosisHistoryModal');
    const diagnosisHistoryList = document.getElementById('diagnosisHistoryList');
    // showDiagnosisHistoryButton 변수는 이미 상단에 선언되어 있으므로 재선언하지 않습니다.
    const showDiagnosisHistoryButton = document.getElementById('showDiagnosisHistoryButton');
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

        // USER_ID는 chatbot_core.js에서 전역으로 관리됩니다.
        // USER_ID가 정의되어 있는지 확인합니다.
        if (typeof USER_ID === 'undefined' || USER_ID === null || isNaN(USER_ID)) {
            diagnosisHistoryList.innerHTML = '<p style="text-align: center; color: red;">사용자 정보를 불러오지 못했습니다. 로그인 상태를 확인해주세요.</p>';
            console.warn("[IMG History Modal] USER_ID가 NULL이거나 NaN입니다. 이전 진단 내역을 불러올 수 없습니다.");
            return;
        }

        try {
            console.log("[IMG History Modal] API 호출 시도: /api/diagnose/history/" + USER_ID);
            const response = await fetch(`/api/diagnose/history/${USER_ID}`);
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
                    const detailsText = item.diagnosisDetails || '';
                    // 정규표현식 수정: 각 섹션 뒤에 개행 문자가 0개 이상 있을 수 있도록 ? 앞에 * 추가
                    const featureMatch = detailsText.match(/특징:\s*(.*?)(?:\r?\n\s*\r?\n*\s*원인:|\r?\n원인:|$)/s);
                    const causeMatch = detailsText.match(/원인:\s*(.*?)(?:\r?\n\s*\r?\n*\s*해결 방안:|\r?\n해결 방안:|$)/s);
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
            console.error("[IMG History Modal] 이전 진단 내역 로드 중 오류 발생:", error);
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
        // 챗봇 모달 관련 로직은 floating_chatbot.js에서 처리합니다.
    };
});