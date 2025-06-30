document.addEventListener("DOMContentLoaded", function() {
    const recommendBtn = document.getElementById("recommend-btn");
    const cropsContainer = document.getElementById("recommended-crops");
    const detailBox = document.getElementById("selected-crop-details");
    const guideModal = document.getElementById("guide-modal");
    const guideSteps = document.getElementById("guide-steps");

    recommendBtn.addEventListener("click", async () => {
        const harvest = document.getElementById("harvest-select").value;
        const env = document.getElementById("env-select").value;

        if (!harvest || !env) {
            alert("수확 희망 시기와 재배 장소를 선택해주세요.");
            return;
        }

        cropsContainer.innerHTML = "불러오는 중...";
        detailBox.style.display = "none"; // 새로운 추천 시 상세 정보 박스 숨기기

        try {
            // 로컬 서버가 8000번 포트에서 실행 중이라면 해당 URL 사용
            // 아니면 해당 API 엔드포인트에 맞게 수정
            const response = await fetch("http://localhost:8000/api/recommend-crop", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ harvest, environment: env }),
            });

            if (!response.ok) {
                // HTTP 오류 상태 코드 (예: 404, 500) 처리
                const errorText = await response.text();
                throw new Error(`Server error: ${response.status} - ${errorText}`);
            }

            const crops = await response.json();

            if (!Array.isArray(crops) || crops.length === 0) {
                cropsContainer.innerHTML = "추천할 작물이 없습니다.";
                return;
            }

            cropsContainer.innerHTML = ""; // 기존 내용 비우기

            crops.forEach((crop) => {
                const btn = document.createElement("button");
                btn.textContent = crop.name;
                btn.classList.add("recommended-crop-btn"); // 스타일링을 위한 클래스 추가
                btn.onclick = () => showDetails(crop);
                cropsContainer.appendChild(btn);
            });
        } catch (err) {
            console.error("작물 추천 실패:", err);
            cropsContainer.innerHTML = `작물 추천에 실패했습니다: ${err.message || '알 수 없는 오류'}`;
        }
    });

    function showDetails(crop) {
        detailBox.style.display = "block";
        document.getElementById("detail-name").textContent = crop.name || '정보 없음';
        document.getElementById("detail-pot-size").textContent = crop.pot_size || '정보 없음';
        document.getElementById("detail-water-amount").textContent = crop.water_amount || '정보 없음';
        document.getElementById("detail-soil-type").textContent = crop.soil_type || '정보 없음';

        const difficultyMap = { "상": "#f44336", "중": "#ffeb3b", "하": "#2196f3" };
        const diff = crop.difficulty || '정보 없음';

        document.getElementById("detail-difficulty-text").textContent = diff;
        const bar = document.getElementById("detail-progress-bar");

        // 난이도에 따른 바 너비와 색상 설정
        let barWidth = "0%";
        let barColor = "#ccc";

        if (diff === "상") {
            barWidth = "100%";
            barColor = difficultyMap["상"];
        } else if (diff === "중") {
            barWidth = "66%"; // 상중하 3단계라고 가정 시 중간은 66%
            barColor = difficultyMap["중"];
        } else if (diff === "하") {
            barWidth = "33%"; // 가장 쉬운 난이도
            barColor = difficultyMap["하"];
        }

        bar.style.width = barWidth;
        bar.style.backgroundColor = barColor;
    }

    document.getElementById("guide-btn").addEventListener("click", () => {
        const steps = [
            "1. 품종 선택",
            "2. 파종 및 모종 준비 (실내/실외)",
            "3. 정식하기",
            "4. 물, 햇빛, 온도 관리",
            "5. 병충해 관리",
            "6. 수확하기"
        ]; // 가이드 내용을 좀 더 구체적으로 작성

        guideSteps.innerHTML = "";
        if (steps.length > 0) {
            steps.forEach(step => {
                const li = document.createElement("li");
                li.textContent = step;
                guideSteps.appendChild(li);
            });
        } else {
            const li = document.createElement("li");
            li.textContent = "아직 준비된 재배 가이드가 없습니다.";
            guideSteps.appendChild(li);
        }


        guideModal.style.display = "flex"; // flex로 설정하여 중앙 정렬 활성화
    });

    // 전역 스코프에 함수를 두어 HTML에서 직접 호출 가능하게 함
    window.closeGuideModal = function () {
        guideModal.style.display = "none";
    }

    // 재배 리스트 삭제 기능 (alert 대신 실제 기능으로 교체 필요)
    window.deleteSelectedCrops = function () {
        alert("선택된 작물을 삭제합니다 (기능 예정)");
        // 여기에 실제 삭제 로직 (예: AJAX 요청) 구현
    }
});