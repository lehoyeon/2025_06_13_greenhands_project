(() => {
  let currentUserId = localStorage.getItem("user_id") || null;

  const $ = (selector) => document.querySelector(selector);
  const alertContainer = $("#alert-container");
  const submitBtn = $("#submit-btn");
  const recommendationsSection = $("#recommendations-section");
  const otherOptionsSection = $("#other-options-section");
  const recommendedCropsContainer = $("#recommended-crops");
  const otherCropsContainer = $("#other-crops");
  const addedCropsTbody = $("#added-crops-table tbody");
  const currentUserDisplay = $("#current-user");

  window.onload = () => {
    if (currentUserDisplay) setCurrentUserId(currentUserId);
    loadMyCrops();
  };

  function setCurrentUserId(id) {
    currentUserId = id;
    if (id) {
      localStorage.setItem("user_id", id);
      if (currentUserDisplay) currentUserDisplay.textContent = id;
    } else {
      localStorage.removeItem("user_id");
      if (currentUserDisplay) currentUserDisplay.textContent = "없음";
    }
  }

  function showAlert(message, type = "success") {
    alertContainer.innerHTML = `<div class="alert ${type}">${message}</div>`;
    setTimeout(() => (alertContainer.innerHTML = ""), 5000);
  }

  function showLoading(show = true) {
    if (show) {
      recommendedCropsContainer.innerHTML = '<div class="loading">추천 작물을 찾는 중입니다...</div>';
      recommendationsSection.style.display = "block";
      otherOptionsSection.style.display = "none";
    }
  }

  $("#crop-recommendation-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!currentUserId) return showAlert("사용자 ID를 먼저 설정해주세요.", "error");

    const harvestPeriod = $("#harvest-period").value;
    const region = $("#region").value;
    const scale = $("#scale").value;

    if (!harvestPeriod || !region || !scale) return showAlert("모든 필드를 선택해주세요.", "error");

    submitBtn.disabled = true;
    submitBtn.textContent = "추천 중...";
    showLoading();

    try {
      const res = await fetch("http://localhost:5000/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ harvest_period: harvestPeriod, region, scale }),
      });

      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);

      const data = await res.json();
      if (!data.success) throw new Error(data.error || "추천 실패");

      renderCrops(recommendedCropsContainer, data.recommended, true, recommendationsSection);
      renderCrops(otherCropsContainer, data.other_options, false, otherOptionsSection);
      showAlert(`${data.total_recommendations}개의 작물을 추천받았습니다!`, "success");
    } catch (error) {
      console.error(error);
      showAlert("작물 추천 중 오류가 발생했습니다: " + error.message, "error");
      recommendedCropsContainer.innerHTML = "";
      otherCropsContainer.innerHTML = "";
      recommendationsSection.style.display = "none";
      otherOptionsSection.style.display = "none";
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "🌱 작물 추천받기";
    }
  });

  function renderCrops(container, crops, isRecommended, section) {
    if (!crops?.length) {
      section.style.display = "none";
      container.innerHTML = "";
      return;
    }
    section.style.display = "block";
    container.innerHTML = "";
    crops.forEach((crop) => container.appendChild(createCropCard(crop, isRecommended)));
  }

  function createCropCard(crop, isRecommended) {
    const card = document.createElement("div");
    card.className = "crop-card";
    card.innerHTML = `<h3>${isRecommended ? "⭐ " : ""}${crop.name}</h3><p>${crop.description || "설명이 없습니다."}</p>`;
    card.onclick = () => showCropPopup(crop);
    return card;
  }

  function removePopup() {
    document.querySelectorAll(".popup-overlay, .popup").forEach((el) => el.remove());
  }

  function showCropPopup(crop) {
    removePopup();

    const overlay = document.createElement("div");
    overlay.className = "popup-overlay";
    overlay.addEventListener("click", removePopup);

    const popup = document.createElement("div");
    popup.className = "popup";

    popup.innerHTML = `
      <h3>🌱 ${crop.name}</h3>
      <p><strong>설명:</strong> ${crop.description || "설명이 없습니다."}</p>
      <div class="popup-buttons">
        <button class="popup-btn add">➕ 내 작물에 추가</button>
        <button class="popup-btn guide">📖 재배 가이드</button>
        <button class="popup-btn close">닫기</button>
      </div>
    `;

    document.body.append(overlay, popup);

    // 버튼별 이벤트 리스너 등록
    popup.querySelector(".popup-btn.add").addEventListener("click", () => {
      addCropToMyList(crop.name, crop.description || "");
    });
    popup.querySelector(".popup-btn.guide").addEventListener("click", () => {
      getCropGuide(crop.name);
    });
    popup.querySelector(".popup-btn.close").addEventListener("click", removePopup);
  }

  async function getCropGuide(cropName) {
    try {
      const res = await fetch(`http://localhost:5000/guide?name=${encodeURIComponent(cropName)}`);
      const data = await res.json();
      if (!data.success) throw new Error(data.error || "가이드 불러오기 실패");
      removePopup();
      showGuidePopup(cropName, data.guide);
    } catch (e) {
      console.error(e);
      showAlert("가이드 조회 중 오류가 발생했습니다.", "error");
    }
  }

  function showGuidePopup(cropName, guide) {
    removePopup();

    const overlay = document.createElement("div");
    overlay.className = "popup-overlay";
    overlay.addEventListener("click", removePopup);

    const popup = document.createElement("div");
    popup.className = "popup";
    popup.style.maxWidth = "700px";
    popup.style.maxHeight = "80vh";
    popup.style.overflowY = "auto";

    popup.innerHTML = `
      <h3>📖 ${cropName} 재배 가이드</h3>
      <div style="margin: 20px 0; line-height: 1.8; white-space: pre-line;">${guide}</div>
      <div class="popup-buttons">
        <button class="popup-btn close">닫기</button>
      </div>
    `;

    document.body.append(overlay, popup);

    popup.querySelector(".popup-btn.close").addEventListener("click", removePopup);
  }

  async function loadMyCrops() {
    if (!currentUserId) {
      addedCropsTbody.innerHTML = `<tr><td colspan="4" style="text-align:center;color:#666;">사용자 ID를 설정하면 등록된 작물을 볼 수 있습니다.</td></tr>`;
      return;
    }
    try {
      const res = await fetch(`http://localhost:5000/crops/${currentUserId}`);
      const data = await res.json();
      if (!data.success) throw new Error(data.error || "내 작물 목록 조회 실패");
      renderMyCrops(data.crops);
    } catch (e) {
      console.error(e);
      showAlert("내 작물 목록 조회 중 오류가 발생했습니다.", "error");
    }
  }

  function renderMyCrops(crops) {
    if (!crops?.length) {
      addedCropsTbody.innerHTML = `<tr><td colspan="4" style="text-align:center;color:#666;">등록된 작물이 없습니다. 작물을 추가해보세요!</td></tr>`;
      return;
    }
    addedCropsTbody.innerHTML = "";
    crops.forEach(({ id, name, description, created_at }) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${name}</strong></td>
        <td>${description ? (description.length > 100 ? description.slice(0, 100) + "..." : description) : "-"}</td>
        <td>${created_at ? new Date(created_at).toLocaleDateString("ko-KR") : "-"}</td>
        <td><button class="delete-btn">🗑️ 삭제</button></td>
      `;
      // 삭제 버튼에 이벤트 리스너 연결
      tr.querySelector(".delete-btn").addEventListener("click", () => {
        deleteCrop(id, name);
      });
      addedCropsTbody.appendChild(tr);
    });
  }

  window.addCropToMyList = async (name, description) => {
    if (!currentUserId) return showAlert("사용자 ID를 먼저 설정해야 합니다.", "error");
    try {
      const res = await fetch("http://localhost:5000/crop/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, description, user_id: currentUserId }),
      });
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      if (!data.success) throw new Error(data.error || "작물 추가 실패");
      showAlert(`'${name}' 작물이 내 목록에 추가되었습니다!`, "success");
      removePopup();
      loadMyCrops();
    } catch (e) {
      console.error(e);
      showAlert("작물 추가 중 오류가 발생했습니다: " + e.message, "error");
    }
  };

  window.deleteCrop = async (cropId, cropName) => {
    if (!confirm(`'${cropName}' 작물을 삭제하시겠습니까?`)) return;

    try {
      const res = await fetch(`http://localhost:5000/crop/delete/${cropId}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      if (!data.success) throw new Error(data.error || "삭제 실패");
      showAlert(`'${cropName}' 작물이 삭제되었습니다.`, "success");
      loadMyCrops();
    } catch (e) {
      console.error(e);
      showAlert("삭제 중 오류가 발생했습니다: " + e.message, "error");
    }
  };

  document.getElementById('go-myfarm-btn').addEventListener('click', function() {
          window.location.href = '/myfarm';
      });

})();
