// src/main/resources/static/js/img/img.js

// 사용자 ID를 전역 변수로 선언하고 초기화되지 않은 상태로 둡니다.
let currentUserId = null;

// 페이지 로드 시 nav-bar 링크 활성화 (main.js의 toggleNavMenu는 유지)
document.addEventListener('DOMContentLoaded', () => {
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

    // 햄버거 메뉴 토글 함수 (main.js에서 가져온 경우 이 파일에서 제거 가능)
    // 현재는 img.html에서 main.js를 먼저 로드하므로, main.js에 이 함수가 있다고 가정합니다.
    // 만약 main.js에 없거나, img.js에서만 쓰인다면 여기에 정의해두는 것이 좋습니다.
    // function toggleNavMenu() { /* ... */ }

    // 사용자 ID 로드 (main.html의 loadUserInfo와 유사)
    loadUserIdForDiagnosis();

    // ========================================
    // 작물 진단 기능 JavaScript
    // ========================================
    const imageUpload = document.getElementById('imageUpload');
    const imagePreview = document.getElementById('imagePreview');
    const placeholderText = document.getElementById('placeholderText');
    const uploadForm = document.getElementById('uploadForm');
    const diagnosisResultSection = document.querySelector('.diagnosis-result-section');
    const geminiResponseText = document.getElementById('geminiResponseText'); // Gemini 응답 표시 영역
    const promptTextarea = document.getElementById('prompt-text'); // 프롬프트 텍스트 영역
    const diagnoseButton = document.querySelector('.btn-diagnose'); // 진단 시작 버튼
    const diagnosisError = document.getElementById('diagnosisError');
    const viewDetailsBtn = document.getElementById('viewDetailsBtn');


    // 이미지 선택 시 미리보기 표시
    imageUpload.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                imagePreview.src = e.target.result;
                imagePreview.style.display = 'block';
                placeholderText.style.display = 'none'; // 미리보기 보이면 텍스트 숨김
            };
            reader.readAsDataURL(file);
            diagnosisResultSection.style.display = 'none'; // 새 이미지 선택 시 결과 초기화
            geminiResponseText.textContent = ''; // Gemini 응답 초기화
            diagnosisError.style.display = 'none';
            diagnoseButton.disabled = false; // 이미지 선택 시 진단 버튼 활성화
            viewDetailsBtn.style.display = 'none'; // 버튼 숨기기
        } else {
            imagePreview.src = '#';
            imagePreview.style.display = 'none';
            placeholderText.style.display = 'block';
            diagnosisResultSection.style.display = 'none';
            geminiResponseText.textContent = '';
            diagnoseButton.disabled = true; // 이미지 없으면 진단 버튼 비활성화
            viewDetailsBtn.style.display = 'none';
        }
    });

    // 폼 제출 (이미지 업로드 및 진단 요청)
    uploadForm.addEventListener('submit', async function(event) {
        event.preventDefault(); // 폼의 기본 제출 방지

        diagnosisResultSection.style.display = 'block'; // 결과 섹션 표시
        geminiResponseText.textContent = '이미지를 분석 중입니다... 잠시만 기다려주세요.'; // 로딩 메시지
        geminiResponseText.style.color = '#616161'; // 로딩 메시지 색상
        diagnosisError.style.display = 'none'; // 이전 오류 메시지 숨김
        diagnoseButton.disabled = true; // 진단 중 버튼 비활성화
        viewDetailsBtn.style.display = 'none'; // '자세히 보기' 버튼 숨기기


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

        // 이미지 압축 및 Base64 인코딩
        let base64Image = null;
        try {
            const compressedFile = await compressImage(file, 1024, 0.8); // 최대 너비 1024px, 품질 0.8 (80%)
            base64Image = await getBase64(compressedFile); // Base64 인코딩
        } catch (error) {
            displayError("이미지 처리 중 오류 발생: " + error.message);
            diagnoseButton.disabled = false;
            return;
        }

        try {
            // Spring Boot 백엔드의 진단 API 엔드포인트로 JSON 전송
            const response = await fetch('/api/diagnose/plant', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image: base64Image,
                    mimeType: file.type, // 원본 파일의 MIME 타입 사용
                    prompt: promptTextarea.value.trim(),
                    userId: currentUserId
                })
            });

            if (response.ok) { // HTTP 상태 코드 200-299 범위 (성공)
                const data = await response.json();
                console.log("진단 성공:", data);

                geminiResponseText.textContent = data.response || "진단 결과를 받아오지 못했습니다."; // Gemini 응답 표시
                geminiResponseText.style.color = '#333'; // 성공 메시지 색상

                // '자세한 진단 결과 확인' 버튼 표시 및 localStorage에 결과 저장
                localStorage.setItem('diagnosisResult', JSON.stringify(data)); // 결과 저장
                localStorage.setItem('originalImageUrl', imagePreview.src); // 이미지 URL 저장
                viewDetailsBtn.style.display = 'block'; // 버튼 표시

            } else { // HTTP 상태 코드 400, 500 등 (오류)
                const errorData = await response.json();
                console.error("진단 실패:", errorData);
                displayError(errorData.message || "진단 중 알 수 없는 오류 발생했습니다.");
            }
        } catch (error) {
            console.error('네트워크 오류:', error);
            displayError("네트워크 오류가 발생했거나 서버에 연결할 수 없습니다.");
        } finally {
            diagnoseButton.disabled = false; // 버튼 다시 활성화
        }
    });

    // --- 사용자 ID 로드 함수 (API 호출) ---
    async function loadUserIdForDiagnosis() {
        try {
            const response = await fetch('/api/main/user/me'); // MainController의 API 엔드포인트
            if (response.ok) {
                const userData = await response.json();
                if (userData.userId) {
                    currentUserId = parseInt(userData.userId); // userId 저장
                    console.log("현재 로그인된 사용자 ID:", currentUserId);
                } else {
                    console.warn("사용자 ID를 불러오지 못했습니다. 진단 기능이 제한될 수 있습니다.");
                }
            } else {
                console.error("사용자 정보 로드 실패:", response.status);
            }
        } catch (error) {
            console.error("사용자 정보 로드 네트워크 오류:", error);
        }
    }


    // 이미지 압축/리사이즈 함수 (HTML5 Canvas 사용)
    async function compressImage(file, maxWidth, quality) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = event => {
                const img = new Image();
                img.src = event.target.result;
                img.onload = () => {
                    const elem = document.createElement('canvas');
                    let width = img.width;
                    let height = img.height;

                    if (width > height) {
                        if (width > maxWidth) {
                            height *= maxWidth / width;
                            width = maxWidth;
                        }
                    } else {
                        if (height > maxWidth) {
                            width *= maxWidth / height;
                            height = maxWidth;
                        }
                    }
                    elem.width = width;
                    elem.height = height;

                    const ctx = elem.getContext('2d');
                    ctx.drawImage(img, 0, 0, width, height);

                    // 압축된 이미지 데이터를 Blob 형태로 반환
                    ctx.canvas.toBlob((blob) => {
                        if (blob) {
                            // 원본 파일의 MIME 타입 유지
                            resolve(new File([blob], file.name, { type: file.type, lastModified: Date.now() }));
                        } else {
                            reject(new Error('Canvas to Blob conversion failed.'));
                        }
                    }, file.type, quality);
                };
                img.onerror = error => reject(error);
            };
            reader.onerror = error => reject(error);
        });
    }

    // Base64 인코딩 헬퍼 함수
    function getBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => resolve(reader.result.split(',')[1]); // "data:image/png;base64," 접두사 제거
            reader.onerror = (error) => reject(error);
        });
    }


    function displayError(message) {
        geminiResponseText.textContent = message;
        geminiResponseText.style.color = '#D32F2F'; // 에러 메시지 색상
        diagnosisError.textContent = message; // 기존 에러 메시지 표시 영역에도
        diagnosisError.style.display = 'block';
        // 이 부분은 Gemini 응답으로 대체되므로 필요 없어질 수 있습니다.
        // diagnosisStatus.textContent = '진단 실패!';
        // predictedDisease.textContent = 'N/A';
        // confidenceScore.textContent = 'N/A';
        // confidenceProgressBar.style.width = '0%';
        // confidenceProgressBar.textContent = '';
        viewDetailsBtn.style.display = 'none'; // 오류 시 버튼 숨기기
    }

    // '자세한 진단 결과 확인' 버튼 클릭 이벤트 (DOMContentLoaded 이후에만 존재)
    if (viewDetailsBtn) { // 버튼이 존재할 때만 이벤트 리스너 추가
        viewDetailsBtn.addEventListener('click', function() {
            window.location.href = '/imgdiagnostics/img_results.html'; // 결과 페이지로 이동
        });
    }
});