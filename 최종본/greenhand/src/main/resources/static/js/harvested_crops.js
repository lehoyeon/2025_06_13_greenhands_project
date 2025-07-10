// js/harvested_crops.js

document.addEventListener('DOMContentLoaded', async function() {
    console.log("harvested_crops.js loaded.");

    // USER_ID 로딩 대기 (chatbot_core.js에서 제공)
    if (typeof userLoadedPromise === 'undefined') {
        console.error("userLoadedPromise가 정의되지 않았습니다. chatbot_core.js가 먼저 로드되었는지 확인하세요.");
        document.getElementById('my-harvested-crops-list').innerHTML = '<p style="text-align: center; color: red;">시스템 초기화 중 오류가 발생했습니다. 페이지를 새로고침 해주세요.</p>';
        return;
    }
    await userLoadedPromise;

    if (USER_ID === null || isNaN(USER_ID)) {
        console.warn("User ID is not valid in harvested_crops.js. Harvested crops list cannot be loaded.");
        document.getElementById('my-harvested-crops-list').innerHTML = '<p style="text-align: center; color: red;">로그인 정보를 불러올 수 없습니다. 다시 로그인해주세요.</p>';
        return;
    } else {
        console.log(`harvested_crops.js에서 확인된 현재 로그인된 사용자 ID: ${USER_ID}`);
    }

    // --- DOM 요소 캐싱 ---
    const myHarvestedCropsListUl = document.getElementById('my-harvested-crops-list');
    const selectedHarvestedCropDetailsDiv = document.getElementById('selected-harvested-crop-details');

    const harvestDetailNameSpan = document.getElementById('harvest-detail-name');
    const harvestDetailHarvestedAtSpan = document.getElementById('harvest-detail-harvested-at');
    // const harvestDetailYieldInfoSpan = document.getElementById('harvest-detail-yield-info'); // ⭐ 제거
    // const harvestDetailStartDateSpan = document.getElementById('harvest-detail-start-date'); // ⭐ 제거
    const harvestDetailExpectedDaysSpan = document.getElementById('harvest-detail-expected-days');
    const harvestDetailEnvironmentSpan = document.getElementById('harvest-detail-environment');
    const harvestDetailDifficultySpan = document.getElementById('harvest-detail-difficulty');
    const harvestDetailThumbnailImg = document.getElementById('harvest-detail-thumbnail');


    // --- 초기화: 상세 정보 숨기기 ---
    function hideHarvestedCropDetails() {
        if (selectedHarvestedCropDetailsDiv) {
            selectedHarvestedCropDetailsDiv.style.display = 'none';
        }
    }
    hideHarvestedCropDetails();

    // --- 수확 작물 리스트 불러오기 및 렌더링 ---
    async function loadMyHarvestedCrops() {
        if (myHarvestedCropsListUl) {
            myHarvestedCropsListUl.innerHTML = '<p style="text-align: center; color: #000;">수확된 작물을 불러오는 중...</p>';
        }
        hideHarvestedCropDetails();

        try {
            // ⭐ /api/crops/harvested-crops/{user_id} 엔드포인트 호출 ⭐
            const response = await fetch(`http://localhost:8000/api/crops/harvested-crops/${USER_ID}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`수확 작물 로드 실패: ${errorData.detail || response.statusText}`);
            }
            const crops = await response.json();
            console.log("수확 작물 데이터:", crops); // ⭐️ 여기 로그를 꼭 확인!

            renderMyHarvestedCrops(crops);

            // 첫 번째 작물의 상세 정보 표시 (선택 사항, 또는 클릭 시 표시)
            if (crops.length > 0) {
                showHarvestedCropDetails(crops[0]);
            } else {
                if (myHarvestedCropsListUl) {
                    myHarvestedCropsListUl.innerHTML = '<p style="text-align: center;">수확된 작물이 없습니다.</p>';
                }
            }

        } catch (error) {
            console.error("수확 작물 로드 중 오류 발생:", error);
            if (myHarvestedCropsListUl) {
                myHarvestedCropsListUl.innerHTML = `<p style="text-align: center; color: red;">수확 작물을 불러올 수 없습니다: ${error.message}</p>`;
            }
        }
    }

    function renderMyHarvestedCrops(crops) {
        if (myHarvestedCropsListUl) {
            myHarvestedCropsListUl.innerHTML = ''; // 기존 내용 삭제
        }

        if (crops.length === 0) {
            if (myHarvestedCropsListUl) {
                myHarvestedCropsListUl.innerHTML = '<p style="text-align: center; color: #000;">수확된 작물 정보는 현재 표시되지 않습니다.</p>';
            }
            return;
        }

        crops.forEach(crop => {
            const li = document.createElement('li');
            li.classList.add('harvested-crop-item');
            li.dataset.userCropId = crop.id; // DB PK

            const harvestedAtDate = crop.harvested_at ? new Date(crop.harvested_at).toLocaleDateString() : '정보 없음';

            li.innerHTML = `
                <span class="crop-info-text">${crop.nick_name || crop.crop_name}</span>
                <span class="harvest-date">수확일: ${harvestedAtDate}</span>
            `;
            if (myHarvestedCropsListUl) {
                myHarvestedCropsListUl.appendChild(li);
            }

            // 각 작물 아이템 클릭 이벤트 (상세 정보 표시)
            li.addEventListener('click', () => showHarvestedCropDetails(crop));
        });
    }

    // --- 수확 작물 상세 정보 표시 함수 ---
    function showHarvestedCropDetails(crop) {
        if (!selectedHarvestedCropDetailsDiv) return;

        selectedHarvestedCropDetailsDiv.style.display = 'block';

        harvestDetailNameSpan.textContent = crop.nick_name || crop.crop_name;
        harvestDetailHarvestedAtSpan.textContent = crop.harvested_at ? new Date(crop.harvested_at).toLocaleDateString() : '정보 없음';
        harvestDetailExpectedDaysSpan.textContent = crop.expected_cultivation_days ? `${crop.expected_cultivation_days}일` : '정보 없음';

        // ⭐⭐⭐ 이 부분을 전부 주석 처리합니다 ⭐⭐⭐
        // let environmentText = '정보 없음';
        // const regions = crop.suitable_regions;
        // const envStatus = crop.environment;

        // let regionDisplay = '';
        // if (regions && regions.length > 0) {
        //     regionDisplay = regions.join(', ');
        // }

        // let envStatusDisplay = '';
        // if (envStatus === 'indoor') {
        //     envStatusDisplay = '실내';
        // } else if (envStatus === 'outdoor') {
        //     envStatusDisplay = '실외';
        // }

        // if (regionDisplay && envStatusDisplay) {
        //     environmentText = `${regionDisplay} (${envStatusDisplay})`;
        // } else if (regionDisplay) {
        //     environmentText = regionDisplay;
        // } else if (envStatusDisplay) {
        //     environmentText = envStatusDisplay;
        // }
        // harvestDetailEnvironmentSpan.textContent = environmentText;
        // ⭐⭐⭐ 여기까지 전부 주석 처리 ⭐⭐⭐

        harvestDetailDifficultySpan.textContent = crop.difficulty || '정보 없음';

        if (harvestDetailThumbnailImg) {
            if (crop.thumbnail_image) {
                harvestDetailThumbnailImg.src = `http://localhost:8000${crop.thumbnail_image}`;
                harvestDetailThumbnailImg.style.display = 'block';
            } else {
                harvestDetailThumbnailImg.style.display = 'none';
                harvestDetailThumbnailImg.src = '#';
            }
        }
    }

    // --- 페이지 초기 로드 시 수확 작물 불러오기 ---
    loadMyHarvestedCrops();
});