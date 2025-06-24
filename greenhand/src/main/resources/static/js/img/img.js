// src/main/resources/static/js/img/img.js

// 페이지 로드 시 nav-bar 링크 활성화 (main.html에서 가져옴)
// img.html 자체에 nav-bar가 있다면 작동합니다.
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
});

// 햄버거 메뉴 토글 함수 (main.html에서 가져옴)
// 이 함수는 nav-bar가 있는 페이지에서만 필요합니다.
function toggleNavMenu() {
    const navLinksContainer = document.getElementById('navLinksContainer');
    if (navLinksContainer) { // 요소가 존재할 때만 실행
        navLinksContainer.classList.toggle('active');
    }
}


// ========================================
// 작물 진단 기능 JavaScript
// ========================================
const imageUpload = document.getElementById('imageUpload');
const imagePreview = document.getElementById('imagePreview');
const placeholderText = document.getElementById('placeholderText');
const uploadForm = document.getElementById('uploadForm');
const diagnosisResultSection = document.querySelector('.diagnosis-result-section');
const diagnosisStatus = document.getElementById('diagnosisStatus');
const predictedDisease = document.getElementById('predictedDisease');
const confidenceScore = document.getElementById('confidenceScore');
const confidenceProgressBar = document.getElementById('confidenceProgressBar');
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
        diagnosisError.style.display = 'none';
        viewDetailsBtn.style.display = 'none'; // 버튼 숨기기
    } else {
        imagePreview.src = '#';
        imagePreview.style.display = 'none';
        placeholderText.style.display = 'block';
        diagnosisResultSection.style.display = 'none';
        viewDetailsBtn.style.display = 'none';
    }
});

// 폼 제출 (이미지 업로드 및 진단 요청)
uploadForm.addEventListener('submit', async function(event) {
    event.preventDefault(); // 폼의 기본 제출 방지

    diagnosisResultSection.style.display = 'block'; // 결과 섹션 표시
    diagnosisStatus.textContent = '모델이 이미지를 분석하고 있습니다...';
    predictedDisease.textContent = '진단 중...';
    confidenceScore.textContent = '진단 중...';
    confidenceProgressBar.style.width = '0%';
    confidenceProgressBar.textContent = '';
    diagnosisError.style.display = 'none'; // 이전 오류 메시지 숨김
    viewDetailsBtn.style.display = 'none'; // 진단 중에는 버튼 숨기기


    const formData = new FormData();
    const file = imageUpload.files[0];

    if (!file) {
        displayError("파일을 선택해주세요.");
        return;
    }

    // 클라이언트 측 이미지 리사이즈 및 압축 (선택 사항이지만 권장)
    // 브라우저에서 이미지 압축을 위한 라이브러리 사용 (예: browser-image-compression)
    // 여기서는 기본 HTML5 Canvas를 이용한 간단한 리사이즈 예시 (실제로는 더 복잡한 라이브러리 권장)
    const compressedFile = await compressImage(file, 1024, 0.8); // 최대 너비 1024px, 품질 0.8 (80%)
    formData.append('file', compressedFile, file.name); // 압축된 파일을 FormData에 추가


    try {
        // Spring Boot 백엔드의 진단 API 엔드포인트로 전송
        const response = await fetch('/api/main/diagnose', {
            method: 'POST',
            body: formData // FormData는 Content-Type을 자동으로 multipart/form-data로 설정
        });

        if (response.ok) { // HTTP 상태 코드 200-299 범위 (성공)
            const data = await response.json();
            console.log("진단 성공:", data);

            diagnosisStatus.textContent = '진단 완료!';
            predictedDisease.textContent = data.predicted_class || '알 수 없음';
            confidenceScore.textContent = data.confidence || 'N/A';

            // 확신도 바 업데이트 (예: "75.12%" -> 75.12)
            const confidenceValue = parseFloat(data.confidence.replace('%', ''));
            if (!isNaN(confidenceValue)) {
                confidenceProgressBar.style.width = `${confidenceValue}%`;
                confidenceProgressBar.textContent = `${confidenceValue.toFixed(2)}%`;
                confidenceProgressBar.style.backgroundColor = confidenceValue > 70 ? '#4CAF50' : (confidenceValue > 40 ? '#FFC107' : '#F44336'); // 색상 변경
            } else {
                confidenceProgressBar.style.width = '0%';
                confidenceProgressBar.textContent = 'N/A';
            }

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
    }
});

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

function displayError(message) {
    diagnosisStatus.textContent = '진단 실패!';
    predictedDisease.textContent = 'N/A';
    confidenceScore.textContent = 'N/A';
    confidenceProgressBar.style.width = '0%';
    confidenceProgressBar.textContent = '';
    diagnosisError.textContent = message;
    diagnosisError.style.display = 'block';
    viewDetailsBtn.style.display = 'none'; // 오류 시 버튼 숨기기
}

// '자세한 진단 결과 확인' 버튼 클릭 이벤트 (DOMContentLoaded 이후에만 존재)
// img.html에 이 버튼이 있다면, 이 리스너가 추가됩니다.
// HTML 로드 후 이 이벤트 리스너를 추가하는 것이 안전합니다.
// img.html의 script 블록에 이 리스너를 포함시키거나, 해당 버튼이 DOMContentLoaded 이후에 존재하도록 합니다.
document.addEventListener('DOMContentLoaded', () => {
    if (viewDetailsBtn) { // 버튼이 존재할 때만 이벤트 리스너 추가
        viewDetailsBtn.addEventListener('click', function() {
            window.location.href = '/img/img_results.html'; // 결과 페이지로 이동
        });
    }
});