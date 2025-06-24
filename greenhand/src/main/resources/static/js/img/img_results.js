/* src/main/resources/static/js/img/img_results.js */

// 페이지 로드 시, nav-bar 링크 활성화 (공통)
document.addEventListener('DOMContentLoaded', () => {
    const currentPath = window.location.pathname.split('/').pop();
    const navLinks = document.querySelectorAll('.nav-bar a'); // 이 부분은 main.html의 nav-bar를 가정.
                                                              // img_results.html에 nav-bar가 있다면 작동.
    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href').split('/').pop();
        if (linkPath === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    loadDiagnosisResult(); // 진단 결과 로드 함수 호출
});

// 햄버거 메뉴 토글 함수 (공통)
function toggleNavMenu() {
    const navLinksContainer = document.getElementById('navLinksContainer');
    navLinksContainer.classList.toggle('active');
}

// --- 진단 결과 및 해결 방안 데이터 ---
// 실제로는 DB나 별도 JSON 파일에서 가져올 수 있습니다.
const diseaseSolutions = {
    "Tomato___Early_blight": {
        name: "토마토 - 점무늬병 (Early Blight)",
        description: [
            "- 오래된 잎에 나타나는 흑갈색 반점이 특징이며, 동심원 무늬가 있습니다.",
            "- 곰팡이성 질병으로, 심하면 잎이 노랗게 변하고 떨어집니다."
        ],
        solution: [
            "감염된 잎과 잔해를 즉시 제거하고 소각하세요.",
            "토마토 줄기 아래쪽 잎을 제거하여 공기 순환을 개선하고, 흙이 잎에 튀지 않도록 멀칭하세요.",
            "물은 잎에 닿지 않도록 뿌리에 직접 공급하고, 오전에 물을 주어 잎이 밤에 마르도록 하세요.",
            "친환경 살균제(예: 보르도액, 유황)를 초기 증상 시 살포하세요."
        ]
    },
    "Tomato___Bacterial_spot": {
        name: "토마토 - 세균성 점무늬병 (Bacterial Spot)",
        description: [
            "- 잎에 작고 둥글며 물에 젖은 듯한 반점이 나타나고, 나중에 검게 변하며 주변이 노랗게 됩니다.",
            "- 세균성 질병으로, 과일에도 발생할 수 있습니다."
        ],
        solution: [
            "감염된 식물 부분을 제거하고 도구를 소독하세요.",
            "작물 간 간격을 넓게 하여 통풍을 좋게 하고, 과습을 피하세요.",
            "구리 기반 살균제를 예방적으로 살포할 수 있습니다."
        ]
    },
    "Corn_(maize)___Common_rust": {
        name: "옥수수 - 녹병 (Common Rust)",
        description: [
            "- 잎 표면에 작고 붉거나 갈색의 융기된 반점(포자)이 나타납니다.",
            "- 습하고 서늘한 환경에서 빠르게 확산됩니다."
        ],
        solution: [
            "병에 강한 품종을 선택하세요.",
            "질소 비료 과용을 피하고, 균형 잡힌 영양 공급을 유지하세요.",
            "공기 순환을 좋게 하고, 물은 잎에 닿지 않도록 합니다.",
            "심하게 감염된 잎은 제거하고, 필요 시 살균제를 사용하세요."
        ]
    },
    // TODO: 다른 질병에 대한 정보 및 해결 방안 추가
    "N/A": { // 진단 실패 또는 알 수 없는 질병
        name: "진단 불가 / 알 수 없는 질병",
        description: ["이미지를 다시 업로드하거나, 더 선명한 사진을 사용해 주세요."],
        solution: ["AI 모델이 정확히 진단하지 못했습니다. 다른 각도에서 사진을 찍거나, 농업 전문가에게 문의하세요."]
    },
    "healthy": { // 건강한 작물
        name: "건강한 작물",
        description: ["귀하의 작물은 현재 건강한 상태로 보입니다!"],
        solution: [
            "현재의 재배 환경과 관리를 잘 유지하세요.",
            "정기적으로 잎과 줄기를 관찰하여 질병의 초기 증상을 확인하세요.",
            "필요한 영양분과 적절한 수분을 공급해주세요."
        ]
    }
};

// 진단 결과를 localStorage에서 로드하여 표시하는 함수
function loadDiagnosisResult() {
    const diagnosisResultJson = localStorage.getItem('diagnosisResult');
    const originalImageUrl = localStorage.getItem('originalImageUrl'); // 원본 이미지 URL

    if (!diagnosisResultJson) {
        document.getElementById('resultDiseaseName').textContent = '결과 없음';
        document.getElementById('predictedDiseaseResult').textContent = '데이터 없음';
        document.getElementById('confidenceScoreResult').textContent = '데이터 없음';
        document.getElementById('confidenceProgressBarResult').style.width = '0%';
        document.getElementById('confidenceProgressBarResult').textContent = '';
        document.getElementById('solutionContent').innerHTML = '<p>진단 결과를 불러올 수 없습니다. 다시 진단을 시도해주세요.</p>';
        document.getElementById('uploadedResultImage').style.display = 'none';
        return;
    }

    try {
        const result = JSON.parse(diagnosisResultJson);
        const diseaseName = result.predicted_class || "N/A";
        const confidence = parseFloat(result.confidence.replace('%', '')); // 숫자만 추출

        document.getElementById('resultDiseaseName').textContent = diseaseName;
        document.getElementById('predictedDiseaseResult').textContent = diseaseName;
        document.getElementById('confidenceScoreResult').textContent = `${confidence.toFixed(2)}%`;

        // 진행바 업데이트
        const progressBar = document.getElementById('confidenceProgressBarResult');
        if (!isNaN(confidence)) {
            progressBar.style.width = `${confidence}%`;
            progressBar.textContent = `${confidence.toFixed(2)}%`;
            progressBar.style.backgroundColor = confidence > 70 ? '#4CAF50' : (confidence > 40 ? '#FFC107' : '#F44336'); // 색상 변경
        } else {
            progressBar.style.width = '0%';
            progressBar.textContent = 'N/A';
        }

        // 업로드된 이미지 표시
        const uploadedResultImage = document.getElementById('uploadedResultImage');
        if (originalImageUrl) {
            uploadedResultImage.src = originalImageUrl;
            uploadedResultImage.style.display = 'block';
        } else {
            uploadedResultImage.style.display = 'none';
        }

        // 해결 방안 표시
        const solution = diseaseSolutions[diseaseName] || diseaseSolutions["N/A"];
        const solutionContentDiv = document.getElementById('solutionContent');
        solutionContentDiv.innerHTML = `
            <p><strong>특징:</strong></p>
            <ul>${solution.description.map(desc => `<li>${desc}</li>`).join('')}</ul>
            <p><strong>해결 방안:</strong></p>
            <ol>${solution.solution.map(sol => `<li>${sol}</li>`).join('')}</ol>
        `;

    } catch (e) {
        console.error("진단 결과 파싱 오류:", e);
        document.getElementById('solutionContent').innerHTML = '<p style="color:#f44336;">결과를 불러오는 중 오류가 발생했습니다.</p>';
    }
}