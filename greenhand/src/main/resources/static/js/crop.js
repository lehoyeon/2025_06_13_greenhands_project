// crop.js (최종 수정)

document.addEventListener("DOMContentLoaded", function() {
    const recommendBtn = document.getElementById("recommend-btn");
    const cropsContainer = document.getElementById("recommended-crops");
    const detailBox = document.getElementById("selected-crop-details");
    const guideModal = document.getElementById("guide-modal");
    const guideContentDiv = document.getElementById("guide-content");
    const aliasModal = document.getElementById("alias-modal");
    const cropAliasInput = document.getElementById("crop-alias-input");
    const confirmAliasBtn = document.getElementById("confirm-alias-btn");
    const aliasForCropNameSpan = document.getElementById("alias-for-crop-name");
    const cultivationListUl = document.getElementById("cultivation-list");
    const addToCultivationListBtn = document.getElementById("add-to-cultivation-list-btn");
    const deleteAllCultivatedCropsBtn = document.getElementById("delete-all-cultivated-crops-btn");
    const addToMainBtn = document.getElementById("add-to-main-btn");

    // 임시 사용자 ID (실제 앱에서는 로그인 후 서버에서 받아와야 합니다)
    const USER_ID = 1;

    let currentSelectedCropForDetails = null; // 상세 정보 박스에 표시된 현재 작물 (RecommendedCropResponse 타입)
    let currentCropForGuide = null; // 가이드 모달에 표시된 현재 작물 (knowledge_base의 원본 데이터, RecommendedCropResponse 타입과 유사)


    // 페이지 로드 시 백엔드에서 재배 리스트 불러오기
    loadCultivationListFromBackend();


    // === 작물 추천 기능 ===
    recommendBtn.addEventListener("click", async () => {
        const env = document.getElementById("env-select").value;
        const duration = document.getElementById("cultivation-duration-select").value;
        const region = document.getElementById("region-select").value;

        if (!duration || !env || !region) {
            alert("재배 기간, 재배 장소, 지역을 모두 선택해주세요.");
            return;
        }

        cropsContainer.innerHTML = "<p>작물 추천 중...</p>";
        detailBox.style.display = "none";
        currentSelectedCropForDetails = null;

        try {
            const response = await fetch("/api/crops/recommend-crop", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    environment: env,
                    duration: duration,
                    region: region
                }),
            });

            if (!response.ok) {
                const errorText = await response.text();
                // 404 Not Found 에러 메시지를 좀 더 친절하게 표시
                if (response.status === 404) {
                    cropsContainer.innerHTML = `<p>선택하신 조건에 맞는 작물이 없습니다.</p>`;
                } else {
                    throw new Error(`서버 에러: ${response.status} - ${errorText}`);
                }
                return; // 에러 발생 시 이후 코드 실행 중단
            }

            // recommendedCrops는 이제 RecommendedCropResponse 객체의 배열입니다.
            const recommendedCrops = await response.json();

            if (!Array.isArray(recommendedCrops) || recommendedCrops.length === 0) {
                cropsContainer.innerHTML = "<p>선택하신 조건에 맞는 작물이 없습니다.</p>";
                return;
            }

            cropsContainer.innerHTML = "";

            recommendedCrops.forEach((crop) => {
                const cropItem = document.createElement("div");
                cropItem.classList.add("recommended-crop-item");
                cropItem.innerHTML = `
                    <img src="${crop.thumbnail_image || '/images/default_crop.png'}" alt="${crop.name}" class="crop-thumbnail">
                    <h3>${crop.name}</h3>
                    <p>난이도: ${crop.difficulty || '정보 없음'}</p>
                `;
                // showDetails 함수에 RecommendedCropResponse 객체를 그대로 전달
                cropItem.onclick = () => showDetails(crop);
                cropsContainer.appendChild(cropItem);
            });

        } catch (err) {
            console.error("작물 추천 실패:", err);
            cropsContainer.innerHTML = `<p>작물 추천에 실패했습니다: ${err.message || '알 수 없는 오류'}</p>`;
        }
    });

    // === 작물 상세 정보 표시 (RecommendedCropResponse 객체 처리) ===
    function showDetails(crop) {
        currentSelectedCropForDetails = crop; // RecommendedCropResponse 객체 저장
        detailBox.style.display = "block";
        document.getElementById("detail-name").textContent = crop.name || '정보 없음';

        const prepList = document.getElementById("detail-preparations");
        prepList.innerHTML = '';
        if (crop.initial_preparations && Array.isArray(crop.initial_preparations)) {
            crop.initial_preparations.forEach(prep => {
                const li = document.createElement("li");
                li.textContent = prep;
                prepList.appendChild(li);
            });
        } else {
            const li = document.createElement("li");
            li.textContent = "준비물 정보가 없습니다.";
            prepList.appendChild(li);
        }

        document.getElementById("detail-pot-size").textContent = crop.pot_size || '정보 없음';
        document.getElementById("detail-water-amount").textContent = crop.water_amount || '정보 없음';
        document.getElementById("detail-soil-type").textContent = crop.soil_type || '정보 없음';
        // RecommendedCropResponse에는 'pest_control' 필드가 있음
        document.getElementById("detail-pest-control").textContent = crop.pest_control || '정보 없음';

        const difficultyMap = { "상": "#f44336", "중": "#ffeb3b", "하": "#2196f3" };
        const diff = crop.difficulty || '정보 없음';

        document.getElementById("detail-difficulty-text").textContent = diff;
        const bar = document.getElementById("detail-progress-bar");

        let barWidth = "0%";
        let barColor = "#ccc";

        if (diff === "상") {
            barWidth = "100%";
            barColor = difficultyMap["상"];
        } else if (diff === "중") {
            barWidth = "66%";
            barColor = difficultyMap["중"];
        } else if (diff === "하") {
            barWidth = "33%";
            barColor = difficultyMap["하"];
        }

        bar.style.width = barWidth;
        bar.style.backgroundColor = barColor;
    }

    // === 재배 리스트에 추가 기능 (백엔드 연동) ===
    addToCultivationListBtn.addEventListener("click", async () => {
        if (!currentSelectedCropForDetails) {
            alert("먼저 작물을 선택해주세요.");
            return;
        }

        try {
            const response = await fetch("/api/crops/user-crops/add", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    user_id: USER_ID,
                    crop_id: currentSelectedCropForDetails.id, // knowledge_base의 ID (e.g., "lettuce")
                    alias: currentSelectedCropForDetails.name // 기본 별칭은 작물 이름
                }),
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`작물 추가 실패: ${response.status} - ${errorText}`);
            }

            const result = await response.json();
            alert(`${currentSelectedCropForDetails.name}이(가) 재배 리스트에 추가되었습니다.`);
            loadCultivationListFromBackend();
        } catch (err) {
            console.error("재배 리스트 추가 실패:", err);
            alert(`재배 리스트 추가 중 오류 발생: ${err.message || '알 수 없는 오류'}`);
        }
    });

    // === 재배 리스트 불러오기 (백엔드 연동) ===
    async function loadCultivationListFromBackend() {
        cultivationListUl.innerHTML = '<p>재배 리스트 불러오는 중...</p>';
        try {
            const response = await fetch(`/api/crops/user-crops/${USER_ID}`);
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`재배 리스트 로드 실패: ${response.status} - ${errorText}`);
            }
            // 이 'crops'는 UserCropResponse 객체의 배열입니다.
            const crops = await response.json();
            renderCultivationList(crops);
        } catch (err) {
            console.error("재배 리스트 로드 실패:", err);
            cultivationListUl.innerHTML = `<p>재배 리스트를 불러올 수 없습니다: ${err.message || '알 수 없는 오류'}</p>`;
        }
    }

    // === 재배 리스트 렌더링 (UI) (UserCropResponse 객체 처리) ===
    function renderCultivationList(cultivationList) {
        cultivationListUl.innerHTML = '';

        if (!Array.isArray(cultivationList) || cultivationList.length === 0) {
            cultivationListUl.innerHTML = '<li>재배 리스트가 비어있습니다.</li>';
            return;
        }

        cultivationList.forEach(crop => { // crop은 UserCropResponse 객체
            const li = document.createElement('li');
            li.classList.add('cultivation-list-item');
            // 'id'는 DB의 PK
            li.dataset.userCropId = crop.id;
            // 'crop_id_from_kb'는 knowledge_base ID (예: 'lettuce')
            li.dataset.cropKbId = crop.crop_id_from_kb;

            li.innerHTML = `
                <img src="${crop.thumbnail_image || '/images/default_crop.png'}" alt="${crop.nick_name}" class="crop-thumbnail-small">
                <span>${crop.nick_name || crop.crop_name} (${crop.crop_name})</span>
                <div class="item-actions">
                    <button class="btn btn-small view-guide-btn" data-crop-kbid="${crop.crop_id_from_kb}">재배 가이드 보기</button>
                    <button class="btn btn-small delete-cultivation-btn" data-user-crop-id="${crop.id}">삭제</button>
                </div>
            `;
            cultivationListUl.appendChild(li);
        });
    }

    // === 재배 리스트 항목 클릭 (재배 가이드 보기 및 삭제) ===
    cultivationListUl.addEventListener('click', async (event) => {
        const target = event.target;
        if (target.classList.contains('view-guide-btn')) {
            const cropKbId = target.dataset.cropKbid;

            try {
                const response = await fetch("/api/crops/crop-guide", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ crop_id: cropKbId }), // knowledge_base ID 전달
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`가이드 로드 실패: ${response.status} - ${errorText}`);
                }

                const guideData = await response.json(); // expects {"detailed_guide": ...}

                // 재배 리스트 항목에서 작물 이름 가져오기
                const listItem = target.closest('.cultivation-list-item');
                const cropNameText = listItem.querySelector('span').textContent;
                const cropNameMatch = cropNameText.match(/\((.*?)\)/); // 괄호 안의 실제 작물 이름 추출
                const actualCropName = cropNameMatch ? cropNameMatch[1] : cropNameText.split('(')[0].trim();


                currentCropForGuide = {
                    name: actualCropName,
                    id: cropKbId, // guide 모달에서 나의 농장 추가 시 필요할 수 있으므로 KB ID도 저장
                    detailed_guide: guideData.detailed_guide
                };
                showGuideModal(currentCropForGuide);

            } catch (err) {
                console.error("재배 가이드 로드 실패:", err);
                alert(`재배 가이드를 불러올 수 없습니다: ${err.message || '알 수 없는 오류'}`);
            }

        } else if (target.classList.contains('delete-cultivation-btn')) {
            const userCropIdToDelete = target.dataset.userCropId;
            if (confirm("정말로 이 작물을 재배 리스트에서 삭제하시겠습니까?")) {
                try {
                    const response = await fetch(`/api/crops/user-crops/${USER_ID}/${userCropIdToDelete}`, {
                        method: "DELETE",
                        headers: { "Content-Type": "application/json" }
                    });

                    if (!response.ok) {
                        const errorText = await response.text();
                        throw new Error(`삭제 실패: ${response.status} - ${errorText}`);
                    }

                    const result = await response.json();
                    alert(result.message);
                    loadCultivationListFromBackend();
                } catch (err) {
                    console.error("재배 리스트 삭제 실패:", err);
                    alert(`재배 리스트 삭제 중 오류 발생: ${err.message || '알 수 없는 오류'}`);
                }
            }
        }
    });

    // === 모든 재배 작물 삭제 기능 (백엔드 연동) ===
    deleteAllCultivatedCropsBtn.addEventListener("click", async () => {
        if (confirm("정말로 모든 작물을 재배 리스트에서 삭제하시겠습니까?")) {
            try {
                const response = await fetch(`/api/crops/user-crops/all/${USER_ID}`, {
                    method: "DELETE",
                    headers: { "Content-Type": "application/json" }
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`전체 삭제 실패: ${response.status} - ${errorText}`);
                }

                const result = await response.json();
                alert(result.message);
                loadCultivationListFromBackend();
            } catch (err) {
                console.error("모든 재배 작물 삭제 실패:", err);
                alert(`모든 재배 작물 삭제 중 오류 발생: ${err.message || '알 수 없는 오류'}`);
            }
        }
    });


    // === 상세 재배 가이드 모달 표시 ===
    function showGuideModal(crop) {
        document.getElementById("modal-guide-title").textContent = `${crop.name} 재배 가이드`;
        guideContentDiv.innerHTML = "";

        if (crop.detailed_guide) {
            if (typeof crop.detailed_guide === 'object' && !Array.isArray(crop.detailed_guide)) {
                const ul = document.createElement("ul");
                for (const key in crop.detailed_guide) {
                    if (Object.hasOwnProperty.call(crop.detailed_guide, key)) {
                        const li = document.createElement("li");
                        li.textContent = crop.detailed_guide[key];
                        ul.appendChild(li);
                    }
                }
                guideContentDiv.appendChild(ul);
            } else if (Array.isArray(crop.detailed_guide)) {
                const ul = document.createElement("ul");
                crop.detailed_guide.forEach(step => {
                    const li = document.createElement("li");
                    li.textContent = step;
                    ul.appendChild(li);
                });
                guideContentDiv.appendChild(ul);
            } else {
                 const p = document.createElement("p");
                 p.textContent = crop.detailed_guide;
                 guideContentDiv.appendChild(p);
            }
        } else {
            const p = document.createElement("p");
            p.textContent = "아직 준비된 재배 가이드가 없습니다.";
            guideContentDiv.appendChild(p);
        }
        guideModal.style.display = "flex";
    }

    window.closeGuideModal = function () {
        guideModal.style.display = "none";
        currentCropForGuide = null;
    }

    // === 나의 농장에 작물 등록 (별칭) 기능 ===
    addToMainBtn.addEventListener('click', () => {
        if (!currentCropForGuide || !currentCropForGuide.id) { // knowledge_base ID가 있는지 확인
            alert("가이드 중인 작물이 없거나 ID 정보를 찾을 수 없습니다.");
            return;
        }
        aliasForCropNameSpan.textContent = currentCropForGuide.name;
        cropAliasInput.value = '';
        aliasModal.style.display = 'flex';
    });

    confirmAliasBtn.addEventListener('click', async () => {
        const alias = cropAliasInput.value.trim();
        if (!alias) {
            alert("별칭을 입력해주세요.");
            return;
        }
        if (!currentCropForGuide || !currentCropForGuide.id) {
            alert("작물 정보가 유효하지 않습니다.");
            return;
        }

        try {
            // "나의 농장에 작물 등록"은 재배 리스트에 추가하는 것과 동일한 API를 사용
            // DB에 `user_crops_new` 테이블에 저장됩니다.
            const response = await fetch("/api/crops/user-crops/add", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    user_id: USER_ID,
                    crop_id: currentCropForGuide.id, // knowledge_base의 ID
                    alias: alias
                }),
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`농장 등록 실패: ${response.status} - ${errorText}`);
            }

            const result = await response.json();
            alert(`'${alias}' (${currentCropForGuide.name})이(가) 나의 농장에 등록되었습니다!`);
            closeAliasModal();
            loadCultivationListFromBackend(); // 재배 리스트 새로고침
        } catch (err) {
            console.error("나의 농장 등록 실패:", err);
            alert(`나의 농장 등록 중 오류 발생: ${err.message || '알 수 없는 오류'}`);
        }
    });

    window.closeAliasModal = function() {
        aliasModal.style.display = 'none';
    }
});