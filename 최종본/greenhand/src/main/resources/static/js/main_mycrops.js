// js/main_mycrops.js

document.addEventListener('DOMContentLoaded', async function() {
    console.log("main_mycrops.js loaded.");

    if (typeof userLoadedPromise === 'undefined') {
        console.error("userLoadedPromise가 정의되지 않았습니다. chatbot_core.js가 먼저 로드되었는지 확인하세요.");
        document.getElementById('my-main-crops-list').innerHTML = '<p style="text-align: center; color: red;">시스템 초기화 중 오류가 발생했습니다. 페이지를 새로고침 해주세요.</p>';
        return;
    }
    await userLoadedPromise;

    if (USER_ID === null || isNaN(USER_ID)) {
        console.warn("User ID is not valid in main_mycrops.js. My crops list cannot be loaded.");
        document.getElementById('my-main-crops-list').innerHTML = '<p style="text-align: center; color: red;">로그인 정보를 불러올 수 없습니다. 다시 로그인해주세요.</p>';
        return;
    } else {
        console.log(`main_mycrops.js에서 확인된 현재 로그인된 사용자 ID: ${USER_ID}`);
    }

    // --- DOM 요소 캐싱 ---
    const myMainCropsListUl = document.getElementById('my-main-crops-list');
    const selectedCropDetailsDiv = document.getElementById('selected-crop-details');

    const detailNameSpan = document.getElementById('detail-name');
    const detailStartDateSpan = document.getElementById('detail-start-date');
    const detailPotSizeSpan = document.getElementById('detail-pot-size');
    const detailWaterAmountSpan = document.getElementById('detail-water-amount');
    const detailWateringFrequencySpan = document.getElementById('detail-watering-frequency');
    const detailSoilTypeSpan = document.getElementById('detail-soil-type');
    const detailProgressSpan = document.getElementById('detail-progress');
    const detailProgressBarFill = document.getElementById('detail-progress-bar');

    const harvestStatusContainer = document.getElementById('harvest-status-container');
    const harvestStatusText = document.getElementById('harvest-status-text');
    const harvestCompleteButtonArea = document.getElementById('harvest-complete-button-area');

    const viewSelectedCropGuideBtn = document.getElementById('view-selected-crop-guide-btn');
    const deleteSelectedCropBtn = document.getElementById('delete-selected-crop-btn');

    const harvestCropBtn = document.createElement('button');
    harvestCropBtn.id = 'harvest-crop-btn-detail';
    harvestCropBtn.className = 'btn btn-primary';
    harvestCropBtn.textContent = '수확 완료';
    harvestCropBtn.style.marginTop = '10px';
    harvestCropBtn.style.display = 'none';

    if (harvestCompleteButtonArea) {
        harvestCompleteButtonArea.appendChild(harvestCropBtn);
    }

    let currentSelectedCropData = null; // 현재 선택된 작물 데이터를 전역 변수로 관리


    const guideModal = document.getElementById("guide-modal");
    const modalGuideTitle = document.getElementById("modal-guide-title");
    const guideContentDiv = document.getElementById("guide-content");

    const dailyCareChecklistUl = document.getElementById('daily-care-checklist');
    const checklistSection = document.querySelector('.checklist-section');

    const diagnosisSection = document.querySelector('.diagnosis-section');
    const diagnosisImageUploadInput = document.getElementById('diagnosis-image-upload');
    const runDiagnosisBtn = document.getElementById('runDiagnosisBtn');
    const diagnosisResultArea = document.getElementById('diagnosis-result-area');


    const guideModalCloseBtn = document.querySelector('#guide-modal .close-btn');
    if (guideModalCloseBtn) {
        guideModalCloseBtn.addEventListener('click', () => guideModal.style.display = 'none');
    }
    window.onclick = function(event) {
        if (event.target === guideModal) {
            guideModal.style.display = 'none';
        }
    };


    function hideCropDetails() {
        selectedCropDetailsDiv.style.display = 'none';
        currentSelectedCropData = null;
        dailyCareChecklistUl.innerHTML = '<p style="text-align: center; color: #555;">체크리스트를 불러오는 중...</p>';

        if (harvestStatusContainer) harvestStatusContainer.style.display = 'none';
        if (checklistSection) checklistSection.style.display = 'none';
        if (diagnosisSection) diagnosisSection.style.display = 'none';
        if (diagnosisImageUploadInput) diagnosisImageUploadInput.value = '';
        if (diagnosisResultArea) diagnosisResultArea.innerHTML = '<p>진단 결과가 여기에 표시됩니다.</p>';
    }
    hideCropDetails();


    async function harvestCrop(userCropIdToHarvest) {
        try {
            const response = await fetch(`http://localhost:8000/api/crops/harvest/${USER_ID}/${userCropIdToHarvest}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`수확 완료 실패: ${response.status} - ${errorData.detail || response.statusText}`);
            }

            const result = await response.json();
            alert(`축하합니다! 그동안 열심히 기르셨네요. ${currentSelectedCropData.nick_name || currentSelectedCropData.crop_name} 수확을 완료했습니다!`);
            loadMyMainCrops();
            hideCropDetails();
        } catch (err) {
            console.error("수확 완료 처리 실패:", err);
            alert(`수확 완료 처리 중 오류 발생: ${err.message || '알 수 없는 오류'}`);
        }
    }

    async function runPlantDiagnosis(file, plantName, targetResultArea) {
        if (!file) {
            targetResultArea.innerHTML = '<p style="color: red;">진단할 사진을 선택해주세요.</p>';
            return;
        }

        targetResultArea.innerHTML = '<p>사진을 분석하고 있습니다. 잠시만 기다려 주세요...</p>';
        const reader = new FileReader();
        reader.readAsDataURL(file);

        reader.onload = async function() {
            const base64Image = reader.result.split(',')[1];
            const mimeType = file.type;

            if (typeof USER_ID === 'undefined' || USER_ID === null || isNaN(USER_ID)) {
                targetResultArea.innerHTML = '<p style="color: red;">사용자 정보를 불러오지 못했습니다. 다시 로그인해주세요.</p>';
                return;
            }

            try {
                const response = await fetch("http://localhost:8000/diagnose/plant", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        image_base64: base64Image,
                        mime_type: mimeType,
                        prompt: `이 식물 사진을 보고, 식물에 질병이 있는지 여부와 건강 상태를 알려주세요. 만약 질병이 있다면 어떤 질병으로 추정되며, 어떻게 관리해야 할지 간략하게 설명해주세요. 작물명은 ${plantName}입니다.`,
                        user_id: USER_ID
                    }),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(`진단 실패: ${response.status} - ${errorData.detail || response.statusText}`);
                }

                const result = await response.json();
                console.log("진단 결과:", result);

                const detailsText = result.diagnosis_details || '';
                const featureMatch = detailsText.match(/특징:\s*(.*?)(?:\n\n원인:|\n원인:|$)/s);
                const causeMatch = detailsText.match(/원인:\s*(.*?)(?:\n\n해결 방안:|\n해결 방안:|$)/s);
                const solutionMatch = detailsText.match(/해결 방안:\s*(.*)/s);

                const parsedFeature = featureMatch && featureMatch[1] ? featureMatch[1].trim() : '정보 없음';
                const parsedCause = causeMatch && causeMatch[1] ? causeMatch[1].trim() : '정보 없음';
                const parsedSolution = solutionMatch && solutionMatch[1] ? solutionMatch[1].trim() : '정보 없음';

                targetResultArea.innerHTML = `
                    <h4>진단 결과: ${result.diagnosis_result || '정보 없음'}</h4>
                    <p><strong>특징:</strong> ${parsedFeature}</p>
                    <p><strong>원인:</strong> ${parsedCause}</p>
                    <p><strong>해결 방안:</strong> ${parsedSolution}</p>
                    <p><strong>심각도:</strong> ${result.severity || '알 수 없음'}</p>
                    <p><strong>진단된 작물명:</strong> ${result.plant_name || '알 수 없음'}</p>
                    ${result.image_url ? `<img src="http://localhost:8000${result.image_url}" alt="진단 이미지" style="max-width: 100%; height: auto; margin-top: 10px;">` : ''}
                `;
                // ⭐ 이미지 진단 완료 메시지 추가 ⭐
                alert("오늘 진단을 완료했습니다! 더 필요하시다면 이미지 진단 페이지에서 이용해주세요.");

            } catch (error) {
                console.error("식물 진단 중 오류 발생:", error);
                targetResultArea.innerHTML = `<p style="color: red;">진단 오류: ${error.message}</p>`;
            }
        };

        reader.onerror = function(error) {
            console.error("파일 읽기 오류:", error);
            targetResultArea.innerHTML = '<p style="color: red;">사진을 읽는 중 오류가 발생했습니다. 예상치 못한 오류가 발생했습니다.</p>';
        };
    }

    // --- 나의 농장 작물 리스트 불러오기 및 렌더링 ---
    async function loadMyMainCrops() {
        myMainCropsListUl.innerHTML = '<p style="text-align: center; color: #000;">나의 농장 작물을 불러오는 중...</p>';
        hideCropDetails();

        try {
            const response = await fetch(`http://localhost:8000/api/crops/user-crops/${USER_ID}?is_main_crop=true`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`나의 농장 작물 로드 실패: ${response.status} - ${errorData.detail || response.statusText}`);
            }
            const crops = await response.json();
            console.log("나의 농장 작물 데이터:", crops);

            renderMyMainCrops(crops);

            if (crops.length > 0) {
                const firstCropElement = myMainCropsListUl.querySelector('li.main-crop-progress-item');
                if (firstCropElement) {
                    firstCropElement.classList.add('selected');
                    showCropDetails(crops[0]);
                }
            } else {
                myMainCropsListUl.innerHTML = '<p style="text-align: center; color: #000;">등록된 작물이 없습니다. 작물을 등록해보세요!</p>';
            }

        } catch (error) {
            console.error("나의 농장 작물 로드 중 오류 발생:", error);
            myMainCropsListUl.innerHTML = `<p style="text-align: center; color: red;">나의 농장 작물을 불러올 수 없습니다: ${error.message}</p>`;
        }
    }

    function renderMyMainCrops(crops) {
        myMainCropsListUl.innerHTML = '';

        if (crops.length === 0) {
            myMainCropsListUl.innerHTML = '<p style="text-align: center; color: #000;">등록된 작물이 없습니다. 작물을 등록해보세요!</p>';
            return;
        }

        crops.forEach(crop => {
            const li = document.createElement('li');
            li.classList.add('main-crop-progress-item');
            li.dataset.userCropId = crop.id;
            li.dataset.cropKbId = crop.crop_id_from_kb;

            const progressPercent = parseFloat(crop.progress_percent) || 0;
            const displayedProgress = progressPercent.toFixed(2);

            let statusTextInList = '';
            if (progressPercent >= 100) {
                statusTextInList = '';
            } else if (crop.days_remaining !== null && crop.days_remaining !== undefined) {
                statusTextInList = `${crop.days_remaining}일 수확까지 남은날짜`;
            } else {
                statusTextInList = '진행 중';
            }

            li.innerHTML = `
                <span class="crop-name-status">${crop.nick_name || crop.crop_name} (${crop.growth_stage || '진행 중'})${statusTextInList ? ` (${statusTextInList})` : ''}</span>
                <div class="progress-bar-main">
                    <div class="progress-fill" style="width: ${displayedProgress}%;"></div>
                </div>
                <span class="progress-percent">${displayedProgress}%</span>
                <i class="material-icons info-icon">info</i>
            `;

            if (progressPercent >= 100) {
                const listHarvestButton = document.createElement('button');
                listHarvestButton.className = 'btn btn-primary btn-list-harvest';
                listHarvestButton.textContent = '수확 완료';
                listHarvestButton.onclick = (event) => {
                    event.stopPropagation();
                    if (confirm(`'${crop.nick_name || crop.crop_name}' 작물을 수확 완료 처리하시겠습니까?`)) {
                        harvestCrop(crop.id);
                    }
                };
                const cropNameStatusSpan = li.querySelector('.crop-name-status');
                if (cropNameStatusSpan) {
                    cropNameStatusSpan.appendChild(document.createTextNode(' '));
                    cropNameStatusSpan.appendChild(listHarvestButton);
                }
            }

            myMainCropsListUl.appendChild(li);

            li.addEventListener('click', () => {
                const previouslySelected = myMainCropsListUl.querySelector('li.selected');
                if (previouslySelected) {
                    previouslySelected.classList.remove('selected');
                }
                li.classList.add('selected');
                showCropDetails(crop);
            });
        });
    }

    // ⭐⭐ 이벤트 핸들러 함수들 정의 (showCropDetails 밖으로 이동) ⭐⭐
    function handleViewGuideClick() {
        if (currentSelectedCropData && currentSelectedCropData.crop_id_from_kb) {
            fetchCropGuideAndShowModal(
                currentSelectedCropData.crop_id_from_kb,
                currentSelectedCropData.nick_name || currentSelectedCropData.crop_name,
                currentSelectedCropData.growth_stage
            );
        } else {
            alert("가이드를 볼 작물 정보가 없습니다.");
        }
    }

    function handleDeleteCropClick() {
        if (currentSelectedCropData && currentSelectedCropData.id) {
            if (confirm(`정말로 '${currentSelectedCropData.nick_name || currentSelectedCropData.crop_name}' 작물을 삭제하시겠습니까?`)) {
                deleteUserCrop(currentSelectedCropData.id);
            }
        } else {
            alert("삭제할 작물 정보가 없습니다.");
        }
    }

    function handleHarvestCropClick() {
        if (currentSelectedCropData && currentSelectedCropData.id) {
            if (confirm(`'${currentSelectedCropData.nick_name || currentSelectedCropData.crop_name}' 작물을 수확 완료 처리하시겠습니까?`)) {
                harvestCrop(currentSelectedCropData.id);
            }
        } else {
            alert("수확할 작물 정보가 없습니다.");
        }
    }

    function handleRunDiagnosisClick() {
        if (diagnosisImageUploadInput && diagnosisImageUploadInput.files.length > 0) {
            runPlantDiagnosis(diagnosisImageUploadInput.files[0], currentSelectedCropData.crop_name, diagnosisResultArea);
        } else {
            alert("진단할 사진을 선택해주세요.");
        }
    }

    function handleDiagnosisImageChange() {
        console.log("진단 이미지 파일이 선택됨:", diagnosisImageUploadInput.files[0] ? diagnosisImageUploadInput.files[0].name : "없음");
    }

    // --- 작물 상세 정보 표시 함수 ---
    async function showCropDetails(crop) {
        currentSelectedCropData = crop; // 선택된 작물 데이터를 전역 변수에 저장 (매우 중요)

        selectedCropDetailsDiv.style.display = 'block';

        detailNameSpan.textContent = crop.nick_name || crop.crop_name;
        detailStartDateSpan.textContent = crop.created_at ? new Date(crop.created_at).toLocaleDateString() : '정보 없음';
        detailPotSizeSpan.textContent = crop.pot_size || '정보 없음';
        detailWaterAmountSpan.textContent = crop.water_amount || '정보 없음';

        let wateringFrequencyText = '정보 없음';
        let wateringDetail = null;
        try {
            const kbResponse = await fetch(`http://localhost:8000/api/crops/crop-info/${crop.crop_id_from_kb}`);
            if (kbResponse.ok) {
                const kbData = await kbResponse.json();
                if (kbData.watering_frequency_detail) {
                    wateringDetail = kbData.watering_frequency_detail;
                    const detail = wateringDetail;
                    let intervalDisplay = '';
                    if (detail.typical_interval_days === 1) {
                        intervalDisplay = "매일";
                    } else if (detail.typical_interval_days) {
                        intervalDisplay = `${detail.typical_interval_days}일마다`;
                    } else if (detail.interval_text) {
                        intervalDisplay = detail.interval_text;
                    } else {
                        intervalDisplay = '정보 없음';
                    }

                    if (detail.condition_text) {
                        intervalDisplay += ` (${detail.condition_text})`;
                    } else if (detail.typical_interval_days && detail.typical_interval_days > 1) {
                         intervalDisplay += ` (흙 마름 확인 후)`;
                    }
                    wateringFrequencyText = intervalDisplay;
                }
            } else {
                console.warn(`Failed to fetch detailed info for ${crop.crop_id_from_kb}. Using general water amount.`);
                wateringFrequencyText = crop.water_amount || '정보 없음';
            }
        } catch (e) {
            console.error("Error fetching watering details:", e);
            wateringFrequencyText = crop.water_amount || '정보 없음';
        }
        detailWateringFrequencySpan.textContent = wateringFrequencyText;

        detailSoilTypeSpan.textContent = crop.soil_type || '정보 없음';

        const progress = parseFloat(crop.progress_percent) || 0;
        detailProgressSpan.textContent = `${progress.toFixed(2)}%`;
        detailProgressBarFill.style.width = `${progress.toFixed(2)}%`;

        if (harvestStatusText) {
            if (progress >= 100) {
                harvestStatusText.textContent = '수확 시기입니다. 수확을 하신 후 수확 완료 버튼을 클릭해주세요.';
                harvestCropBtn.style.display = 'block';
                if (checklistSection) checklistSection.style.display = 'none';
                if (diagnosisSection) diagnosisSection.style.display = 'none';
            } else {
                if (crop.days_remaining !== null && crop.days_remaining !== undefined) {
                    harvestStatusText.textContent = `수확까지: ${crop.days_remaining}일 남음`;
                } else {
                    statusTextInList = '진행 중';
                }
                harvestCropBtn.style.display = 'none';
                if (checklistSection) checklistSection.style.display = 'block';
            }
        }
        if (diagnosisImageUploadInput) diagnosisImageUploadInput.value = '';
        if (diagnosisResultArea) diagnosisResultArea.innerHTML = '<p>진단 결과가 여기에 표시됩니다.</p>';

        // 진단 섹션의 가시성 조건 (진단 버튼 활성/비활성화)
        if (diagnosisSection) {
            const currentProgress = parseFloat(currentSelectedCropData.progress_percent) || 0;
            if (currentProgress >= 15) {
                diagnosisSection.style.display = 'block';
            } else {
                diagnosisSection.style.display = 'none';
            }
        }

        // ⭐⭐ 버튼 클릭 이벤트 리스너 재연결 (onclick 사용) ⭐⭐
        if (viewSelectedCropGuideBtn) viewSelectedCropGuideBtn.onclick = handleViewGuideClick;
        if (deleteSelectedCropBtn) deleteSelectedCropBtn.onclick = handleDeleteCropClick;
        if (harvestCropBtn) harvestCropBtn.onclick = handleHarvestCropClick;
        if (runDiagnosisBtn) runDiagnosisBtn.onclick = handleRunDiagnosisClick;


        await generateDailyChecklist(crop, wateringDetail);
    }

    // ⭐⭐ 오늘의 재배 체크리스트 동적 생성 함수 ⭐⭐
    async function generateDailyChecklist(crop, wateringDetail) {
        dailyCareChecklistUl.innerHTML = '';

        let existingChecklistItems = [];
        try {
            // ⭐⭐⭐ URL 수정: /api/user-crops/{user_id}/{user_crop_id}/checklist 로 변경 (FastAPI) ⭐⭐⭐
            const response = await fetch(`http://localhost:8000/api/user-crops/${USER_ID}/${crop.id}/checklist`);
            if (response.ok) {
                existingChecklistItems = await response.json();
                console.log("기존 체크리스트 항목:", existingChecklistItems);
            } else {
                console.warn(`기존 체크리스트 항목을 불러오는 데 실패했습니다: ${response.status} - ${response.statusText}`);
            }
        } catch (error) {
            console.error("기존 체크리스트 항목 로드 중 오류 발생:", error);
        }

        const createChecklistItem = (taskText, taskId) => {
            const listItem = document.createElement('li');
            const existingItem = existingChecklistItems.find(item => item.item_id === taskId);
            const isCompleted = existingItem ? existingItem.is_completed : false;

            listItem.innerHTML = `
                <span class="checklist-item-text">${taskText}</span>
                <button class="btn-checklist-complete" data-task-id="${taskId}">${isCompleted ? '완료됨' : '완료'}</button>
            `;
            if (isCompleted) {
                listItem.classList.add('completed');
                listItem.querySelector('.checklist-item-text').style.textDecoration = 'line-through';
                listItem.querySelector('.checklist-item-text').style.color = '#888';
                listItem.querySelector('.btn-checklist-complete').disabled = true;
            }
            dailyCareChecklistUl.appendChild(listItem);
            listItem.querySelector('.btn-checklist-complete').addEventListener('click', handleChecklistButtonClick);
        };


        // 1. 물 주기 항목 (wateringDetail 활용)
        if (wateringDetail) {
            let waterTaskText = `물 ${wateringDetail.amount_ml || '적당량'}ml 주기`;
            let occurrences = wateringDetail.watering_time_suggestions ? wateringDetail.watering_time_suggestions.length : 1;
            let intervalInfo = '';

            if (wateringDetail.typical_interval_days === 1) { // 매일
                if (wateringDetail.watering_time_suggestions && wateringDetail.watering_time_suggestions.length > 0) {
                    intervalInfo = ` (${wateringDetail.watering_time_suggestions.join(', ')} ${wateringDetail.min_interval_hours ? '간격 ' + wateringDetail.min_interval_hours + '시간' : ''})`;
                } else {
                    intervalInfo = ` (매일)`;
                }
            } else if (wateringDetail.typical_interval_days) { // N일마다
                intervalInfo = ` (${wateringDetail.typical_interval_days}일마다, ${wateringDetail.condition_text || '흙 마름 확인 후'})`;
            } else if (wateringDetail.interval_text) { // 텍스트 설명
                intervalInfo = ` (${wateringDetail.interval_text})`;
            }
            createChecklistItem(`${waterTaskText} (예상: ${occurrences}회)${intervalInfo}`, `water-${crop.id}`);

        } else {
            createChecklistItem(`물 ${crop.water_amount || '적당량'} 주기 (정보 없음)`, `water-${crop.id}`);
        }

        // 2. 기타 재배 가이드 항목 (현재 성장 단계의 detailed_guides_by_stage 활용)
        try {
            const guideResponse = await fetch("http://localhost:8000/api/crops/crop-guide", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ crop_id: crop.crop_id_from_kb, growth_stage: crop.growth_stage }),
            });

            if (guideResponse.ok) {
                const guideData = await guideResponse.json();
                const detailedGuide = guideData.detailed_guide;

                if (detailedGuide && detailedGuide.guide_text && Array.isArray(detailedGuide.guide_text)) {
                    detailedGuide.guide_text.forEach((item, index) => {
                        const lowerCaseItem = item.toLowerCase();
                        if (
                            !lowerCaseItem.includes("물 주") &&
                            !lowerCaseItem.includes("물 관") &&
                            !lowerCaseItem.includes("흙이 마르면") &&
                            !lowerCaseItem.includes("햇빛") &&
                            !lowerCaseItem.includes("솎아") &&
                            !lowerCaseItem.includes("순지르기") &&
                            !lowerCaseItem.includes("비료") &&
                            !lowerCaseItem.includes("지지대") &&
                            !lowerCaseItem.includes("화분") &&
                            !lowerCaseItem.includes("온도") &&
                            !lowerCaseItem.includes("습도") &&
                            !lowerCaseItem.includes("파종") &&
                            !lowerCaseItem.includes("수확")
                        ) {
                            createChecklistItem(item, `guide-${crop.id}-${index}`);
                        }
                    });
                } else {
                    dailyCareChecklistUl.innerHTML += `<li><p>해당 성장 단계에 대한 추가 재배 가이드가 없습니다.</p></li>`;
                }
            } else {
                console.warn(`Failed to fetch detailed guide for checklist: ${guideResponse.statusText}`);
                dailyCareChecklistUl.innerHTML += `<li><p>재배 가이드를 불러오는 데 실패했습니다.</p></li>`;
            }
        } catch (error) {
            console.error("Error generating checklist from guide:", error);
            dailyCareChecklistUl.innerHTML = `<li><p>체크리스트 생성 중 오류 발생: ${error.message}</p></li>`;
        }

        createChecklistItem(`햇빛 8시간 이상 쬐기`, `sunlight-${crop.id}`);

        checkAllTasksCompleted();
    }

    // ⭐⭐ 체크리스트 항목 변경 핸들러 (버튼 클릭용) ⭐⭐
    async function handleChecklistButtonClick(event) {
        const button = event.target;
        const listItem = button.closest('li');
        const itemTextSpan = listItem.querySelector('.checklist-item-text');
        const taskId = button.dataset.taskId;
        const isCompleted = !listItem.classList.contains('completed');

        if (!currentSelectedCropData || !currentSelectedCropData.id) {
            alert("작물 정보가 없어 체크리스트 상태를 저장할 수 없습니다.");
            return;
        }

        try {
            const response = await fetch(`http://localhost:8000/api/user-crops/checklist/update`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    user_id: USER_ID,
                    user_crop_id: currentSelectedCropData.id,
                    item_id: taskId,
                    is_completed: isCompleted
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`체크리스트 업데이트 실패: ${response.status} - ${errorData.detail || response.statusText}`);
            }

            // UI 업데이트
            if (isCompleted) {
                listItem.classList.add('completed');
                itemTextSpan.style.textDecoration = 'line-through';
                itemTextSpan.style.color = '#888';
                button.textContent = '완료됨';
                button.disabled = true;
            } else {
                listItem.classList.remove('completed');
                itemTextSpan.style.textDecoration = 'none';
                itemTextSpan.style.color = '#333';
                button.textContent = '완료';
                button.disabled = false;
            }
            // 메시지 표시 로직은 checkAllTasksCompleted로 이동합니다.
            checkAllTasksCompleted(true); // 모든 항목 완료 여부 확인 후 메시지 표시
        }
        catch (error) { // 이 catch 블록은 유지됩니다.
            console.error("체크리스트 상태 업데이트 실패:", error);
            alert(`체크리스트 상태 저장 중 오류 발생: ${error.message || '알 수 없는 오류'}`);
        }
    }

    // ⭐⭐ 모든 체크박스 완료 여부 확인 및 진행률 상승 (임시) ⭐⭐
    // showMessage 인자 추가
    async function checkAllTasksCompleted(showMessage = false) {
        const checklistItems = dailyCareChecklistUl.querySelectorAll('li');
        if (checklistItems.length === 0) {
            if (diagnosisSection) diagnosisSection.style.display = 'none';
            return;
        }

        let completedCount = 0;
        checklistItems.forEach(item => {
            if (item.classList.contains('completed')) {
                completedCount++;
            }
        });

        const allCompleted = (completedCount === checklistItems.length);

        if (allCompleted) {
            let currentProgress = parseFloat(currentSelectedCropData.progress_percent) || 0;
            if (currentProgress < 100) {
                let newProgress = Math.min(100, currentProgress + 0.5);
                detailProgressSpan.textContent = `${newProgress.toFixed(2)}%`;
                detailProgressBarFill.style.width = `${newProgress.toFixed(2)}%`;
                currentSelectedCropData.progress_percent = newProgress;

                // ⭐ 진행률 변경 사항을 DB에 저장하는 API 호출 (새로 추가) ⭐
                try {
                    const progressUpdateResponse = await fetch(`http://localhost:8000/api/crops/user-crops/${currentSelectedCropData.id}`, {
                        method: "PATCH",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            progress_percent: newProgress
                        })
                    });
                    if (!progressUpdateResponse.ok) {
                        console.error("진행률 업데이트 DB 저장 실패:", progressUpdateResponse.statusText);
                    } else {
                        console.log("진행률 DB 저장 성공!");
                        // DB 저장 성공 후, 메인 리스트의 해당 항목 진행률 업데이트 (깜빡임 없이)
                        const currentCropLi = myMainCropsListUl.querySelector(`li[data-user-crop-id="${currentSelectedCropData.id}"]`);
                        if (currentCropLi) {
                            currentCropLi.querySelector('.progress-percent').textContent = `${newProgress.toFixed(2)}%`;
                            currentCropLi.querySelector('.progress-fill').style.width = `${newProgress.toFixed(2)}%`;
                        }
                        // loadMyMainCrops()는 전체 새로고침이므로, 위처럼 특정 li만 업데이트하는 것이 UI/UX에 더 좋습니다.
                    }
                } catch (error) {
                    console.error("진행률 DB 저장 중 오류 발생:", error);
                }

                if (showMessage) {
                    alert("오늘 할 일을 완료하셨군요! 작물이 잘 자라고 있나 이미지 진단을 한번 해보세요. (진행률이 소폭 상승했습니다.)");
                }
            } else if (showMessage && currentProgress >= 100) {
                 alert("모든 체크리스트를 완료했습니다. 이미 작물은 100% 진행되었습니다!");
            }

            if (diagnosisSection) {
                const progress = parseFloat(currentSelectedCropData.progress_percent) || 0;
                if (progress >= 15) {
                    diagnosisSection.style.display = 'block';
                } else {
                    diagnosisSection.style.display = 'none';
                }
            }
        } else {
            if (diagnosisSection) diagnosisSection.style.display = 'none';
        }
    }


    // ⭐⭐ 식물 진단 실행 함수 (img.js에서 가져옴) ⭐⭐
    async function runPlantDiagnosis(file, plantName, targetResultArea) {
        if (!file) {
            targetResultArea.innerHTML = '<p style="color: red;">진단할 사진을 선택해주세요.</p>';
            return;
        }

        targetResultArea.innerHTML = '<p>사진을 분석하고 있습니다. 잠시만 기다려 주세요...</p>';
        const reader = new FileReader();
        reader.readAsDataURL(file);

        reader.onload = async function() {
            const base64Image = reader.result.split(',')[1];
            const mimeType = file.type;

            if (typeof USER_ID === 'undefined' || USER_ID === null || isNaN(USER_ID)) {
                targetResultArea.innerHTML = '<p style="color: red;">사용자 정보를 불러오지 못했습니다. 다시 로그인해주세요.</p>';
                return;
            }

            try {
                const response = await fetch("http://localhost:8000/diagnose/plant", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        image_base64: base64Image,
                        mime_type: mimeType,
                        prompt: `이 식물 사진을 보고, 식물에 질병이 있는지 여부와 건강 상태를 알려주세요. 만약 질병이 있다면 어떤 질병으로 추정되며, 어떻게 관리해야 할지 간략하게 설명해주세요. 작물명은 ${plantName}입니다.`,
                        user_id: USER_ID
                    }),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(`진단 실패: ${response.status} - ${errorData.detail || response.statusText}`);
                }

                const result = await response.json();
                console.log("진단 결과:", result);

                const detailsText = result.diagnosis_details || '';
                const featureMatch = detailsText.match(/특징:\s*(.*?)(?:\n\n원인:|\n원인:|$)/s);
                const causeMatch = detailsText.match(/원인:\s*(.*?)(?:\n\n해결 방안:|\n해결 방안:|$)/s);
                const solutionMatch = detailsText.match(/해결 방안:\s*(.*)/s);

                const parsedFeature = featureMatch && featureMatch[1] ? featureMatch[1].trim() : '정보 없음';
                const parsedCause = causeMatch && causeMatch[1] ? causeMatch[1].trim() : '정보 없음';
                const parsedSolution = solutionMatch && solutionMatch[1] ? solutionMatch[1].trim() : '정보 없음';

                targetResultArea.innerHTML = `
                    <h4>진단 결과: ${result.diagnosis_result || '정보 없음'}</h4>
                    <p><strong>특징:</strong> ${parsedFeature}</p>
                    <p><strong>원인:</strong> ${parsedCause}</p>
                    <p><strong>해결 방안:</strong> ${parsedSolution}</p>
                    <p><strong>심각도:</strong> ${result.severity || '알 수 없음'}</p>
                    <p><strong>진단된 작물명:</strong> ${result.plant_name || '알 수 없음'}</p>
                    ${result.image_url ? `<img src="http://localhost:8000${result.image_url}" alt="진단 이미지" style="max-width: 100%; height: auto; margin-top: 10px;">` : ''}
                `;
                alert("오늘 진단을 완료했습니다! 더 필요하시다면 이미지 진단 페이지에서 이용해주세요.");

            } catch (error) {
                console.error("식물 진단 중 오류 발생:", error);
                targetResultArea.innerHTML = `<p style="color: red;">진단 오류: ${error.message}</p>`;
            }
        };

        reader.onerror = function(error) {
            console.error("파일 읽기 오류:", error);
            targetResultArea.innerHTML = '<p style="color: red;">사진을 읽는 중 오류가 발생했습니다. 예상치 못한 오류가 발생했습니다.</p>';
        };
    }


    // --- 선택 작물 상세 가이드 보기 함수 (가이드 모달 표시) ---
    async function fetchCropGuideAndShowModal(cropKbId, cropName, growthStage) {
        if (!guideModal || !modalGuideTitle || !guideContentDiv) {
            alert("가이드 모달 요소가 현재 페이지에 없습니다. (main.html에 정의된 모달을 사용합니다.)");
            console.error("Guide modal elements not found in main.html. Please ensure guide-modal is correctly added.");
            return;
        }

        guideContentDiv.innerHTML = '<p>재배 가이드를 불러오는 중...</p>';
        guideModal.style.display = "flex";

        try {
            const response = await fetch("http://localhost:8000/api/crops/crop-guide", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ crop_id: cropKbId, growth_stage: growthStage }),
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`가이드 로드 실패: ${response.status} - ${errorText}`);
            }

            const guideData = await response.json();
            console.log("가이드 데이터:", guideData);

            const guideContent = guideData.detailed_guide;

            modalGuideTitle.textContent = `${cropName} 재배 가이드 (${guideContent.title || growthStage} 단계)`;
            guideContentDiv.innerHTML = "";

            let basicInfoHtml = `
                <div class="guide-section">
                    <h4>기본 재배 정보</h4>
                    <ul>
                        <li><strong>화분 크기:</strong> ${currentSelectedCropData.pot_size || '정보 없음'}</li>
                        <li><strong>물의 양:</strong> ${currentSelectedCropData.water_amount || '정보 없음'}</li>
                        <li><strong>흙 종류:</strong> ${currentSelectedCropData.soil_type || '정보 없음'}</li>
                        <li><strong>난이도:</strong> ${currentSelectedCropData.difficulty || '정보 없음'}</li>
                    </ul>
                </div>
            `;
            guideContentDiv.innerHTML += basicInfoHtml;


            let checklistSectionHtml = `
                <div class="guide-section">
                    <h4>오늘의 재배 체크리스트 (참고)</h4>
                    <ul id="modal-daily-care-checklist">
                        </ul>
                    <h4>단계별 주요 관리 (${guideContent.title || growthStage} 단계)</h4>
                    <ul id="modal-stage-guide-items"></ul>
                </div>
            `;
            guideContentDiv.innerHTML += checklistSectionHtml;

            const modalDailyCareChecklistUl = guideContentDiv.querySelector('#modal-daily-care-checklist');
            const modalStageGuideItemsUl = guideContentDiv.querySelector('#modal-stage-guide-items');

            const kbResponseForChecklist = await fetch(`http://localhost:8000/api/crops/crop-info/${cropKbId}`);
            if (kbResponseForChecklist.ok) {
                const kbDataForChecklist = await kbResponseForChecklist.json();
                const wateringDetailForModal = kbDataForChecklist.watering_frequency_detail;
                if (wateringDetailForModal) {
                    let waterTaskText = `물 ${wateringDetailForModal.amount_ml || '적당량'}ml 주기`;
                    let occurrences = wateringDetailForModal.watering_time_suggestions ? wateringDetailForModal.watering_time_suggestions.length : 1;
                    let intervalInfo = '';

                    if (wateringDetailForModal.typical_interval_days === 1) {
                        if (wateringDetailForModal.watering_time_suggestions && wateringDetailForModal.watering_time_suggestions.length > 0) {
                            intervalInfo = ` (${wateringDetailForModal.watering_time_suggestions.join(', ')} ${wateringDetailForModal.min_interval_hours ? '간격 ' + wateringDetailForModal.min_interval_hours + '시간' : ''})`;
                        } else {
                            intervalInfo = ` (매일)`;
                        }
                    } else if (wateringDetailForModal.typical_interval_days) {
                        intervalInfo = ` (${wateringDetailForModal.typical_interval_days}일마다, ${wateringDetailForModal.condition_text || '흙 마름 확인 후'})`;
                    } else if (wateringDetailForModal.interval_text) {
                        intervalInfo = ` (${wateringDetailForModal.interval_text})`;
                    }
                    modalDailyCareChecklistUl.innerHTML += `<li>${waterTaskText} (예상: ${occurrences}회)${intervalInfo}</li>`;
                }
            }
            modalDailyCareChecklistUl.innerHTML += `<li>햇빛 8시간 이상 쬐기</li>`;

            if (guideContent.guide_text && Array.isArray(guideContent.guide_text)) {
                guideContent.guide_text.forEach(step => {
                    const li = document.createElement("li");
                    li.textContent = step;
                    modalStageGuideItemsUl.appendChild(li);
                });
            } else if (guideContent.guide_text) {
                const p = document.createElement("p");
                p.textContent = guideContent.guide_text;
                modalStageGuideItemsUl.appendChild(p);
            } else {
                modalStageGuideItemsUl.innerHTML = '<li><p>해당 단계에 대한 상세 가이드가 없습니다.</p></li>';
            }

            if (guideContent.image_tip) {
                const img = document.createElement('img');
                img.src = `http://localhost:8000${guideContent.image_tip}`;
                img.alt = `${cropName} ${guideContent.title} 이미지`;
                img.style.maxWidth = '100%';
                img.style.height = 'auto';
                img.style.marginTop = '15px';
                guideContentDiv.appendChild(img);
            }

        } catch (err) {
            console.error("재배 가이드 로드 실패:", err);
            guideContentDiv.innerHTML = `<p>재배 가이드를 불러올 수 없습니다: ${err.message || '알 수 없는 오류'}</p>`;
        }
    }


    // --- 선택 작물 삭제 함수 ---
    async function deleteUserCrop(userCropIdToDelete) {
        try {
            const response = await fetch(`http://localhost:8000/api/crops/user-crops/${USER_ID}/${userCropIdToDelete}`, {
                method: "DELETE",
                headers: { "Content-Type": "application/json" }
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`작물 삭제 실패: ${response.status} - ${errorText}`);
            }

            const result = await response.json();
            alert(result.message);
            loadMyMainCrops();
            hideCropDetails();
        } catch (err) {
            console.error("작물 삭제 실패:", err);
            alert(`작물 삭제 중 오류 발생: ${err.message || '알 수 없는 오류'}`);
        }
    }


    // --- 페이지 초기 로드 시 나의 농장 작물 불러오기 ---
    loadMyMainCrops();

    if (diagnosisImageUploadInput) {
        diagnosisImageUploadInput.addEventListener('change', handleDiagnosisImageChange);
    }
}); // DOMContentLoaded end