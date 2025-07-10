// js/crop.js

document.addEventListener("DOMContentLoaded", async function() {
    console.log("crop.js loaded");

    // ⭐ USER_ID 로딩 대기 ⭐
    // chatbot_core.js의 userLoadedPromise를 사용합니다.
    if (typeof userLoadedPromise === 'undefined') {
        console.error("userLoadedPromise가 정의되지 않았습니다. chatbot_core.js가 먼저 로드되었는지 확인하세요.");
        alert("시스템 초기화 중 오류가 발생했습니다. 페이지를 새로고침 해주세요.");
        return;
    }

    await userLoadedPromise; // USER_ID가 로드될 때까지 기다립니다.

    // 이제 USER_ID는 chatbot_core.js에 의해 설정된 값입니다.
    // USER_ID가 null이거나 유효하지 않은 경우를 대비한 체크는 여전히 필요합니다.
    if (USER_ID === null || isNaN(USER_ID)) {
        console.warn("User ID is not valid. Some functionalities might be limited.");
        alert("사용자 정보를 불러올 수 없습니다. 로그인 상태를 확인해주세요.");
        return;
    } else {
        console.log(`crop.js에서 확인된 현재 로그인된 사용자 ID: ${USER_ID}`);
    }

    // --- 전역 변수 초기화 ---
    let currentSelectedCropForDetails = null;
    let currentCropForGuide = null;
    let currentUserCropIdToUpdate = null; // 기존 DB 레코드 업데이트 시 사용될 ID

    // --- DOM 요소 가져오기 ---
    const recommendBtn = document.getElementById("recommend-btn"); // '작물 추천' 버튼
    const cropsContainer = document.getElementById("recommended-crops"); // 추천 작물 목록 표시 영역
    const detailBox = document.getElementById("selected-crop-details"); // 선택된 작물 상세 정보 표시 영역

    const cultivationListUl = document.getElementById("cultivation-list"); // '관심 작물' 리스트 UL
    // ⭐ 중요: HTML에 #main-cultivation-list가 없으므로 null일 수 있습니다.
    const mainCultivationListUl = document.getElementById("main-cultivation-list"); // '나의 농장' 리스트 UL

    const deleteAllCultivatedCropsBtn = document.getElementById("delete-all-cultivated-crops-btn"); // '전체 삭제' 버튼

    // '재배 리스트에 추가' 버튼 (추천 작물 상세 박스 내)
    const addToCultivationListBtn = document.getElementById("add-to-cultivation-list-btn");

    // '가이드 모달' 요소
    const guideModal = document.getElementById("guide-modal");
    const modalGuideTitle = document.getElementById("modal-guide-title");
    const guideContentDiv = document.getElementById("guide-content");

    // '별칭 모달' 요소
    const aliasModal = document.getElementById("alias-modal");
    const aliasForCropNameSpan = document.getElementById("alias-for-crop-name"); // 별칭 모달 내 작물 이름 표시
    const cropAliasInput = document.getElementById("crop-alias-input"); // 별칭 입력 필드
    const confirmAliasBtn = document.getElementById("confirm-alias-btn"); // 별칭 모달 '등록' 버튼
    const plantingMethodSelect = document.getElementById("planting-method-select"); // ⭐ 추가: 파종 방법 선택 요소 ⭐

    // --- 모달 닫기 버튼 이벤트 리스너 연결 ---
    // 가이드 모달 닫기
    const guideModalCloseBtn = document.querySelector('#guide-modal .close-btn');
    if (guideModalCloseBtn) {
        guideModalCloseBtn.addEventListener('click', closeGuideModal);
    } else {
        console.error("Error: '#guide-modal .close-btn' element not found.");
    }

    // 별칭 모달 닫기
    const aliasModalCloseBtn = document.querySelector('#alias-modal .close-btn');
    if (aliasModalCloseBtn) {
        aliasModalCloseBtn.addEventListener('click', closeAliasModal);
    } else {
        console.error("Error: '#alias-modal .close-btn' element not found.");
    }

    // --- 모달 닫기 함수 정의 ---
    function closeGuideModal() {
        guideModal.style.display = "none";
        currentCropForGuide = null;
    }

    function closeAliasModal() {
        aliasModal.style.display = 'none';
        currentCropForGuide = null; // 모달 닫을 때 현재 작물 정보 초기화
        currentUserCropIdToUpdate = null; // 업데이트할 ID 초기화
        cropAliasInput.value = ''; // 입력 필드 초기화
        aliasForCropNameSpan.textContent = ''; // 작물 이름 초기화
        plantingMethodSelect.value = ''; // ⭐ 추가: 파종 방법 선택 초기화 ⭐
    }

    // 모달 외부 클릭 시 닫기
    window.onclick = function(event) {
        if (event.target === guideModal) {
            closeGuideModal();
        }
        if (event.target === aliasModal) {
            closeAliasModal();
        }
    };


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
            const response = await fetch("http://localhost:8000/api/crops/recommend-crop", {
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
                if (response.status === 404) {
                    cropsContainer.innerHTML = `<p>선택하신 조건에 맞는 작물이 없습니다.</p>`;
                } else {
                    throw new Error(`서버 에러: ${response.status} - ${errorText}`);
                }
                return;
            }

            let recommendedCrops = await response.json();
            console.log("📥 API 응답 (추천 작물):", recommendedCrops);

            if (!Array.isArray(recommendedCrops) || recommendedCrops.length === 0) {
                cropsContainer.innerHTML = "<p>선택하신 조건에 맞는 작물이 없습니다.</p>";
                return;
            }

            cropsContainer.innerHTML = "";
            recommendedCrops.forEach((crop) => {
                const cropItem = document.createElement("div");
                cropItem.classList.add("recommended-crop-item");
                cropItem.innerHTML = `
                    <img src="${crop.thumbnail_image || 'http://localhost:8080/img/default_crop.png'}" alt="${crop.name}" class="crop-thumbnail">
                    <h3>${crop.name}</h3>
                    <p>난이도: ${crop.difficulty || '정보 없음'}</p>
                `;
                cropItem.onclick = () => showDetails(crop); // 클릭 시 상세 정보 표시
                cropsContainer.appendChild(cropItem);
            });

        } catch (err) {
            console.error("작물 추천 실패:", err);
            cropsContainer.innerHTML = `<p>작물 추천에 실패했습니다: ${err.message || '알 수 없는 오류'}</p>`;
        }
    });

    // === 작물 상세 정보 표시 (RecommendedCropResponse 객체 처리) ===
    function showDetails(crop) {
        console.log("추천 crop 객체 확인:", crop);
        currentSelectedCropForDetails = crop; // 현재 선택된 작물 정보 저장
        detailBox.style.display = "block"; // 상세 정보 박스 표시

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
        document.getElementById("detail-pest-control").textContent = crop.pest_control || '정보 없음';

        // 난이도 프로그레스 바 업데이트
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


    // --- 재배 리스트에 추가 (is_main_crop = false) ---
    addToCultivationListBtn.addEventListener("click", async () => {
        if (!currentSelectedCropForDetails) {
            alert("먼저 작물을 선택해주세요.");
            return;
        }
        if (!currentSelectedCropForDetails.id) {
             alert("작물 ID가 없어 재배 리스트에 추가할 수 없습니다. 다시 추천받아주세요.");
             console.error("Missing crop ID:", currentSelectedCropForDetails);
             return;
        }
        if (USER_ID === null || isNaN(USER_ID)) {
            alert("작물을 추가하려면 로그인이 필요합니다.");
            return;
        }

        try {
            console.log("선택된 작물 정보 (재배 리스트 추가):", currentSelectedCropForDetails);
            console.log("보낼 crop_id:", currentSelectedCropForDetails.id);

            const response = await fetch("http://localhost:8000/api/crops/user-crops/add", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    user_id: USER_ID,
                    crop_id: currentSelectedCropForDetails.id,
                    alias: currentSelectedCropForDetails.name,
                    is_main_crop: false // 관심 작물 리스트에 추가 시 is_main_crop은 false
                }),
            });

            if (response.ok) {
                alert("관심 작물 리스트에 추가되었습니다!");
                loadRecommendedCropList(); // 관심 작물 리스트 새로고침
            } else {
                const errorData = await response.json();
                alert(`관심 작물 리스트 추가 실패: ${errorData.detail || response.statusText}`);
                console.error("관심 작물 리스트 추가 실패:", errorData);
            }
        } catch (err) {
            console.error("관심 작물 리스트 추가 실패:", err);
            alert(`관심 작물 리스트 추가 중 오류 발생: ${err.message || '알 수 없는 오류'}`);
        }
    });

    // --- 재배 리스트 불러오기 (is_main_crop에 따라 구분) ---
    async function loadRecommendedCropList() {
        if (USER_ID === null || isNaN(USER_ID)) {
            cultivationListUl.innerHTML = '<p>로그인 후 관심 작물 리스트를 볼 수 있습니다.</p>';
            return;
        }
        cultivationListUl.innerHTML = '<p>관심 작물 리스트 불러오는 중...</p>';
        try {
            const response = await fetch(`http://localhost:8000/api/crops/user-crops/${USER_ID}?is_main_crop=false`);
            if (response.ok) {
                const userCrops = await response.json();
                renderCultivationList(userCrops, cultivationListUl, "관심 작물 리스트가 비어있습니다.");
            } else {
                const errorData = await response.json();
                cultivationListUl.innerHTML = `<p>관심 작물 리스트 로드 실패: ${errorData.detail || response.statusText}</p>`;
                console.error("관심 작물 리스트 로드 실패:", errorData);
            }
        } catch (err) {
            console.error("관심 작물 리스트 로드 실패:", err);
            cultivationListUl.innerHTML = `<p>관심 작물 리스트를 불러올 수 없습니다: ${err.message || '알 수 없는 오류'}</p>`;
        }
    }

    async function loadMainCultivationList() {
        // ⭐ 중요: HTML에 <ul id="main-cultivation-list"></ul> 요소가 없습니다.
        // 이 리스트를 사용하려면 crop.html 파일에 해당 ul 요소를 추가해야 합니다.
        // 현재는 요소가 없으므로 경고 메시지 출력 후 함수를 종료합니다.
        if (!mainCultivationListUl) {
            console.warn("HTML에 id='main-cultivation-list' 요소가 없습니다. '나의 농장' 리스트를 렌더링할 수 없습니다.");
            return;
        }

        if (USER_ID === null || isNaN(USER_ID)) {
            mainCultivationListUl.innerHTML = '<p>로그인 후 나의 농장 작물을 볼 수 있습니다.</p>';
            return;
        }
        mainCultivationListUl.innerHTML = '<p>나의 농장 작물 불러오는 중...</p>';
        try {
            const response = await fetch(`http://localhost:8000/api/crops/user-crops/${USER_ID}?is_main_crop=true`);
            if (response.ok) {
                const userCrops = await response.json();
                renderCultivationList(userCrops, mainCultivationListUl, "나의 농장에 작물이 없습니다. 관심 작물을 등록해주세요!");
            } else {
                const errorData = await response.json();
                mainCultivationListUl.innerHTML = `<p>나의 농장 작물 로드 실패: ${errorData.detail || response.statusText}</p>`;
                console.error("나의 농장 작물 로드 실패:", errorData);
            }
        } catch (err) {
            console.error("나의 농장 작물 로드 실패:", err);
            mainCultivationListUl.innerHTML = `<p>나의 농장 작물을 불러올 수 없습니다: ${err.message || '알 수 없는 오류'}</p>`;
        }
    }


    // === 재배 리스트 렌더링 (UI) (UserCropResponse 객체 처리) ===
    function renderCultivationList(cultivationList, targetUlElement, emptyMessage) {
        targetUlElement.innerHTML = ''; // 기존 내용 지우기

        if (!Array.isArray(cultivationList) || cultivationList.length === 0) {
            targetUlElement.innerHTML = `<li>${emptyMessage}</li>`;
            return;
        }

        cultivationList.forEach(crop => { // crop은 UserCropResponse 객체
            const li = document.createElement('li');
            li.classList.add('cultivation-list-item'); // CSS 스타일링을 위한 클래스
            li.dataset.userCropId = crop.id; // DB의 PK
            li.dataset.cropKbId = crop.crop_id_from_kb; // knowledge_base ID (예: 'lettuce')
            li.dataset.cropName = crop.crop_name; // 실제 작물 이름
            li.dataset.nickName = crop.nick_name; // 사용자가 지정한 별칭

            const cropImage = crop.thumbnail_image ? `http://localhost:8080/images/default_crop.png` : 'http://localhost:8080/images/default_crop.png';
            const displayName = crop.nick_name || crop.crop_name;

            let actionsHtml = '';
            // targetUlElement.id를 사용하여 '나의 농장' 리스트와 '관심 작물' 리스트의 버튼을 구분
            if (targetUlElement.id === "main-cultivation-list") { // 나의 농장 리스트
                actionsHtml = `
                    <button class="btn btn-small view-guide-btn" data-crop-kbid="${crop.crop_id_from_kb}" data-crop-name="${crop.crop_name}">재배 가이드 보기</button>
                    <button class="btn btn-small delete-cultivation-btn" data-user-crop-id="${crop.id}">삭제</button>
                    `;
            } else { // 관심 작물 리스트 (cultivation-list)
                actionsHtml = `
                    <button class="btn btn-small view-guide-btn" data-crop-kbid="${crop.crop_id_from_kb}" data-crop-name="${crop.crop_name}">재배 가이드 보기</button>
                    <button class="btn btn-small add-to-main-from-list-btn"
                            data-user-crop-id="${crop.id}"
                            data-crop-kbid="${crop.crop_id_from_kb}"
                            data-crop-name="${crop.crop_name}"
                            data-current-alias="${crop.nick_name || ''}">나의 농장에 등록</button>
                    <button class="btn btn-small delete-cultivation-btn" data-user-crop-id="${crop.id}">삭제</button>
                `;
            }

            li.innerHTML = `
                <img src="${cropImage}" alt="${displayName}" class="crop-thumbnail-small">
                <span>${displayName} (${crop.crop_name})</span>
                <div class="item-actions">
                    ${actionsHtml}
                </div>
            `;
            targetUlElement.appendChild(li);
        });

        // ⭐ 동적으로 생성된 버튼에 이벤트 리스너 연결 (DOMContentLoaded 외부에서 실행되도록) ⭐
        // 이벤트 위임 대신, 각 버튼에 직접 이벤트 리스너를 다시 붙이는 방식으로 수정

        // 삭제 버튼 이벤트 리스너
        targetUlElement.querySelectorAll('.delete-cultivation-btn').forEach(button => {
            button.addEventListener('click', async (event) => {
                const userCropIdToDelete = event.target.dataset.userCropId;
                if (confirm("정말로 이 작물을 재배 리스트에서 삭제하시겠습니까?")) {
                    try {
                        // ⭐ API 경로 수정: user_id를 URL에 포함 ⭐
                        const response = await fetch(`http://localhost:8000/api/crops/user-crops/${USER_ID}/${userCropIdToDelete}`, {
                            method: "DELETE",
                            headers: { "Content-Type": "application/json" } // body는 없어도 headers는 유지
                        });

                        if (!response.ok) {
                            const errorText = await response.text();
                            throw new Error(`삭제 실패: ${response.status} - ${errorText}`);
                        }

                        const result = await response.json();
                        alert(result.message);
                        loadRecommendedCropList(); // 관심 작물 리스트 새로고침
                        loadMainCultivationList(); // 나의 농장 리스트 새로고침
                    } catch (err) {
                        console.error("재배 리스트 삭제 실패:", err);
                        alert(`재배 리스트 삭제 중 오류 발생: ${err.message || '알 수 없는 오류'}`);
                    }
                }
            });
        });

        // '나의 농장에 등록' 버튼 (관심 작물 리스트에서) 이벤트 리스너
        targetUlElement.querySelectorAll('.add-to-main-from-list-btn').forEach(button => {
            button.addEventListener('click', (event) => {
                console.log("나의 농장에 등록 (관심 작물 리스트) 버튼 클릭됨!");
                const userCropIdToActivate = event.target.dataset.userCropId;
                const cropKbIdToActivate = event.target.dataset.cropKbid;
                const cropNameForAlias = event.target.dataset.cropName;
                const currentAlias = event.target.dataset.currentAlias;

                currentUserCropIdToUpdate = userCropIdToActivate; // 기존 레코드 ID 저장

                // 별칭 모달에 전달할 정보 설정
                currentCropForGuide = {
                    name: cropNameForAlias,
                    id: cropKbIdToActivate,
                };
                aliasForCropNameSpan.textContent = cropNameForAlias; // 모달 헤더에 실제 작물 이름 표시
                cropAliasInput.value = currentAlias || cropNameForAlias; // 기존 별칭 또는 작물 이름으로 채움
                aliasModal.style.display = 'flex';
                // aliasModalIsMainCropCheckbox 관련 코드 제거 (HTML에 없음)
            });
        });

        // 재배 가이드 보기 버튼 이벤트 리스너
        targetUlElement.querySelectorAll('.view-guide-btn').forEach(button => {
            button.addEventListener('click', async (event) => {
                const cropKbId = event.target.dataset.cropKbid;
                const cropName = event.target.dataset.cropName;

                try {
                    // ⭐ API 경로 및 메서드 확인: /api/crops/crop-guide (POST) ⭐
                    const response = await fetch("http://localhost:8000/api/crops/crop-guide", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ crop_id: cropKbId }),
                    });

                    if (!response.ok) {
                        const errorText = await response.text();
                        throw new Error(`가이드 로드 실패: ${response.status} - ${errorText}`);
                    }

                    const guideData = await response.json();
                    console.log("가이드 데이터:", guideData); // 가이드 데이터 구조 확인

                    currentCropForGuide = {
                        name: cropName, // 실제 작물 이름
                        id: cropKbId,
                        detailed_guide: guideData.detailed_guide // 백엔드에서 'detailed_guide' 키로 반환된다고 가정
                    };
                    showGuideModal(currentCropForGuide); // 가이드 모달 표시

                } catch (err) {
                    console.error("재배 가이드 로드 실패:", err);
                    alert(`재배 가이드를 불러올 수 없습니다: ${err.message || '알 수 없는 오류'}`);
                }
            });
        });
    }


    // === 상세 재배 가이드 모달 표시 함수 ===
    function showGuideModal(crop) {
        modalGuideTitle.textContent = `${crop.name} 재배 가이드`;
        guideContentDiv.innerHTML = "";

        if (crop.detailed_guide) {
            // 상세 가이드가 객체 또는 배열 형식으로 올 수 있으므로 적절히 파싱하여 표시
            if (typeof crop.detailed_guide === 'object' && !Array.isArray(crop.detailed_guide)) {
                const ul = document.createElement("ul");
                for (const key in crop.detailed_guide) {
                    if (Object.hasOwnProperty.call(crop.detailed_guide, key)) {
                        const li = document.createElement("li");
                        li.textContent = `${key}: ${crop.detailed_guide[key]}`; // "step1: 내용" 형식으로 표시
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
            } else { // 단순 문자열인 경우
                const p = document.createElement("p");
                p.textContent = crop.detailed_guide;
                guideContentDiv.appendChild(p);
            }
        } else {
            const p = document.createElement("p");
            p.textContent = "아직 준비된 재배 가이드가 없습니다.";
            guideContentDiv.appendChild(p);
        }
        guideModal.style.display = "flex"; // flex로 설정하여 중앙 정렬될 수 있도록
    }


    // === 모든 재배 작물 삭제 기능 (백엔드 연동) ===
    deleteAllCultivatedCropsBtn.addEventListener("click", async () => {
        if (USER_ID === null || isNaN(USER_ID)) {
            alert("모든 작물을 삭제하려면 로그인이 필요합니다.");
            return;
        }
        if (confirm("정말로 모든 작물을 재배 리스트에서 삭제하시겠습니까? (나의 농장 작물 포함)")) {
            try {
                // ⭐ API 경로 수정: user_id를 URL에 포함 ⭐
                const response = await fetch(`http://localhost:8000/api/crops/user-crops/all/${USER_ID}`, {
                    method: "DELETE",
                    headers: { "Content-Type": "application/json" }
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`전체 삭제 실패: ${response.status} - ${errorText}`);
                }

                const result = await response.json();
                alert(result.message);
                loadRecommendedCropList(); // 관심 작물 리스트 새로고침
                loadMainCultivationList(); // 나의 농장 리스트 새로고침
            } catch (err) {
                console.error("모든 재배 작물 삭제 실패:", err);
                alert(`모든 재배 작물 삭제 중 오류 발생: ${err.message || '알 수 없는 오류'}`);
            }
        }
    });


    // === 별칭 모달 '등록' 버튼 클릭 시 로직 ===
    confirmAliasBtn.addEventListener('click', async () => {
        const alias = cropAliasInput.value.trim();
        const plantingMethod = plantingMethodSelect.value; // ⭐ 추가: 파종 방법 값 가져오기 ⭐

        if (!alias) {
            alert("별칭을 입력해주세요.");
            return;
        }
        if (!plantingMethod) { // ⭐ 추가: 파종 방법 선택 검증 ⭐
            alert("파종 방법을 선택해주세요 (씨앗 또는 모종).");
            return;
        }
        if (!currentCropForGuide || !currentCropForGuide.id) {
            alert("작물 정보가 유효하지 않습니다.");
            return;
        }
        if (USER_ID === null || isNaN(USER_ID)) {
            alert("작물을 등록하려면 로그인이 필요합니다.");
            return;
        }

        try {
            const payload = {
                user_id: USER_ID,
                crop_id: currentCropForGuide.id,
                alias: alias,
                is_main_crop: true, // 나의 농장으로 등록하는 경우 항상 true
                planting_method: plantingMethod // ⭐ 추가: 파종 방법 백엔드로 전송 ⭐
            };

            // 기존 레코드를 업데이트하는 경우 user_crop_db_id 추가
            if (currentUserCropIdToUpdate) {
                payload.user_crop_db_id = currentUserCropIdToUpdate;
            }

            console.log("Activate API로 보낼 payload:", payload);

            const activateResponse = await fetch("http://localhost:8000/api/crops/user-crops/activate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            if (!activateResponse.ok) {
                const errorText = await activateResponse.text();
                throw new Error(`농장 등록 (활성화) 실패: ${activateResponse.status} - ${errorText}`);
            }

            const activateResult = await activateResponse.json();
            alert(`'${alias}' (${currentCropForGuide.name})이(가) 나의 농장에 성공적으로 등록되었습니다!`);
            closeAliasModal(); // 별칭 모달 닫기
            closeGuideModal(); // 가이드 모달도 함께 닫기 (선택 사항)

            // 두 리스트 모두 새로고침하여 변경된 상태를 반영
            loadRecommendedCropList();
            loadMainCultivationList();
            currentUserCropIdToUpdate = null; // 성공 후 ID 초기화

        } catch (err) {
            console.error("나의 농장 등록 실패:", err);
            alert(`나의 농장 등록 중 오류 발생: ${err.message || '알 수 없는 오류'}`);
        }
    });

    // --- 페이지 초기 로드 시 리스트 불러오기 ---
    loadRecommendedCropList();
    loadMainCultivationList(); // 이 함수는 mainCultivationListUl이 HTML에 없으면 경고만 출력합니다.

}); // DOMContentLoaded 끝