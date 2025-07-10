document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('signupForm');
    const inputs = form.querySelectorAll('input'); // 모든 input 요소
    const modal = document.getElementById('validationModal'); // 유효성 오류 팝업 모달
    const successModal = document.getElementById('successModal'); // 성공 팝업 모달
    const modalErrorList = document.getElementById('modalErrorList'); // 오류 목록을 표시할 ul

    // 유효성 검사 규칙 (서버 DTO 규칙과 동일하게 맞춰야 함)
    const validationRules = {
        username: {
            required: true,
            min: 6,
            max: 20,
            pattern: /^[a-zA-Z0-9]+$/,
            messages: {
                required: "아이디는 필수 입력 값입니다.",
                min: "아이디는 6자 이상 20자 이하로 입력해주세요.",
                max: "아이디는 20자 이하로 입력해주세요.",
                pattern: "아이디는 영문과 숫자만 가능합니다."
            }
        },
        password: {
            required: true,
            min: 8,
            max: 16,
            pattern: /^(?=.*[a-zA-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]).*$/,
            messages: {
                required: "비밀번호는 필수 입력 값입니다.",
                min: "비밀번호는 8자 이상 16자 이하로 입력해주세요.",
                max: "비밀번호는 16자 이하로 입력해주세요.",
                pattern: "비밀번호는 영문, 숫자, 특수문자를 포함해야 합니다."
            }
        },
        confirmPassword: {
            required: true,
            matches: 'password', // 'password' 필드와 일치해야 함
            messages: {
                required: "비밀번호 확인은 필수 입력 값입니다.",
                matches: "비밀번호가 일치하지 않습니다."
            }
        },
        nickname: {
            required: true,
            min: 2,
            max: 10,
            messages: {
                required: "닉네임은 필수 입력 값입니다.",
                min: "닉네임은 2자 이상 10자 이하로 입력해주세요.",
                max: "닉네임은 10자 이하로 입력해주세요."
            }
        },
        name: {
            // 이름은 서버에서 @NotNull이 아닌 @Size 등으로만 유효성 검사를 한다면 required: false로 간주.
            // 현재 코드에서는 required 속성이 없으므로 선택사항으로 처리됩니다.
            min: 2,
            max: 20,
            pattern: /^[a-zA-Z가-힣]+$/,
            messages: {
                min: "이름은 2자 이상 20자 이하로 입력해주세요.",
                max: "이름은 20자 이하로 입력해주세요.",
                pattern: "이름은 한글 또는 영문만 가능합니다."
            }
        },
        email: {
            // 이메일은 서버에서 @NotNull이 아닌 @Email 등으로만 유효성 검사를 한다면 required: false로 간주.
            // 현재 코드에서는 required 속성이 없으므로 선택사항으로 처리됩니다.
            pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
            max: 100,
            messages: {
                pattern: "유효한 이메일 주소를 입력해주세요.",
                max: "이메일은 100자 이하로 입력해주세요."
            }
        },
        address: {
            max: 255,
            messages: {
                max: "주소는 255자 이하로 입력해주세요."
            }
        },
        phoneNumber: {
            pattern: /^[0-9-]+$/,
            max: 20,
            messages: {
                pattern: "전화번호는 숫자와 하이픈(-)만 가능합니다.",
                max: "전화번호는 20자 이하로 입력해주세요."
            }
        }
    };

    // 페이지 로드 시 URL 파라미터 처리 (성공 팝업 방지 및 이전 입력 값 복원)
    // 이 부분은 URL 정리 역할만 하며, 팝업을 띄우지 않습니다.
    const params = new URLSearchParams(window.location.search);
    if (params.has('signupSuccess') || params.has('error') || params.has('errorText')) {
        const newUrl = new URL(window.location.href);
        newUrl.searchParams.delete('signupSuccess');
        newUrl.searchParams.delete('error');
        newUrl.searchParams.delete('errorText');
        window.history.replaceState({}, document.title, newUrl.toString());
    }

    // 이전 입력 값 복원 (서버에서 유효성 검사 실패 후 리다이렉트 시)
    const formDataFromLocalStorage = localStorage.getItem('signupFormData');
    if (formDataFromLocalStorage) {
        const data = JSON.parse(formDataFromLocalStorage);
        for (const key in data) {
            const input = document.getElementById(key);
            if (input) {
                input.value = data[key];
            }
        }
        localStorage.removeItem('signupFormData'); // 사용 후 삭제
        inputs.forEach(validateField); // 데이터 복원 후 필드 유효성 재검사
    }


    // 폼 제출 이벤트 리스너 (AJAX 통신)
    form.addEventListener('submit', async function(event) {
        event.preventDefault(); // 폼의 기본 제출 동작 방지

        let allClientValid = true;
        const clientErrors = [];
        const formData = {}; // 서버로 보낼 데이터 객체

        // 1. 클라이언트 측 유효성 검사 수행 및 데이터 수집
        inputs.forEach(input => {
            const fieldValid = validateField(input); // 실시간 검사 함수 호출
            formData[input.name] = input.value.trim(); // 모든 필드 값 수집
            if (!fieldValid) {
                allClientValid = false;
                const errorSpan = document.getElementById(input.id + '-error');
                if (errorSpan && errorSpan.textContent) {
                    // 필드 에러 메시지를 수집하여 팝업에 표시
                    clientErrors.push(
                        (document.querySelector(`label[for="${input.id}"]`)?.textContent || input.name).trim()
                        + ": " + errorSpan.textContent
                    );
                }
            }
        });

        // 2. 클라이언트 유효성 검사 실패 시 팝업 표시 및 제출 방지
        if (!allClientValid) {
            showModal(clientErrors); // 클라이언트 유효성 검사 오류 팝업 표시
            return; // 서버로 제출하지 않고 여기서 종료
        }

        // 3. 클라이언트 유효성 검사를 통과했을 경우, 서버로 AJAX 요청
        try {
            const response = await fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json', // JSON 형태로 데이터 전송
                },
                body: JSON.stringify(formData), // JSON 문자열로 변환하여 전송
            });

            if (response.ok) { // HTTP 상태 코드 200-299 범위 (성공)
                const data = await response.json();
                console.log("회원가입 성공:", data.message);
                showSuccessModal(); // 성공 팝업 표시
            } else { // HTTP 상태 코드 400, 500 등 (오류)
                const errorData = await response.json(); // 서버에서 보낸 JSON 오류 응답 파싱
                console.error("회원가입 실패:", errorData);

                const serverErrors = [];
                // 서버에서 필드별 오류를 보낸 경우 (예: Spring의 @Valid 오류)
                for (const fieldName in errorData) {
                    if (errorData.hasOwnProperty(fieldName)) {
                        let labelText = document.querySelector(`label[for="${fieldName}"]`)?.textContent || fieldName;
                        labelText = labelText.trim(); // HTML에서 ' (고유)' 등 제거했으므로 여기서 추가 처리 필요 없음

                        // 특정 필드에 대한 오류 메시지를 해당 필드 옆에 표시
                        const inputElement = document.getElementById(fieldName);
                        const errorSpanElement = document.getElementById(fieldName + '-error');
                        // 오류가 있는 필드만 invalid 클래스 추가 및 메시지 표시
                        if (inputElement) inputElement.classList.add('is-invalid');
                        if (errorSpanElement) errorSpanElement.textContent = errorData[fieldName];

                        // 아이콘도 invalid로 변경
                        const iconElement = document.getElementById(fieldName + '-icon');
                        if (iconElement) {
                            iconElement.classList.remove('valid');
                            iconElement.classList.add('invalid');
                            iconElement.textContent = 'cancel'; // X 아이콘
                        }

                        serverErrors.push(`${labelText}: ${errorData[fieldName]}`);
                    }
                }
                // 모든 오류 메시지를 팝업으로 표시
                if (serverErrors.length > 0) {
                    showModal(serverErrors);
                } else {
                    showModal(["알 수 없는 오류가 발생했습니다."]); // 예기치 않은 오류 형식에 대한 폴백
                }
            }
        } catch (error) {
            console.error('네트워크 오류 또는 서버 응답 없음:', error);
            showModal(["네트워크 오류가 발생했거나 서버에 연결할 수 없습니다."]);
        }
    });

    // 실시간 유효성 검사를 위한 이벤트 리스너 (input과 blur)
    inputs.forEach(input => {
        input.addEventListener('input', () => validateField(input));
        input.addEventListener('blur', () => validateField(input));
    });

    function validateField(input) {
        const fieldName = input.name;
        const value = input.value.trim();
        const rules = validationRules[fieldName];
        const errorSpan = document.getElementById(input.id + '-error');
        const iconElement = document.getElementById(input.id + '-icon'); // 아이콘 요소 가져오기

        let isValid = true;
        let errorMessage = '';

        // 초기화: 유효성 검사 전에 클래스, 메시지, 아이콘 모두 초기화
        input.classList.remove('is-valid', 'is-invalid');
        if (errorSpan) errorSpan.textContent = '';
        if (iconElement) {
            iconElement.classList.remove('valid', 'invalid');
            iconElement.textContent = ''; // 아이콘 내용 지우기
        }

        // 해당 필드에 유효성 규칙이 없거나 (예: address, phoneNumber가 비어있는 경우),
        // required가 아니고 값이 비어있는 경우 (즉, 입력 자체가 선택사항인 필드가 입력되지 않은 경우)
        // 유효한 것으로 처리하고 함수를 종료
        if (!rules || (!rules.required && value === '')) {
            return true;
        }

        // required 검사
        if (rules.required && value === '') {
            isValid = false;
            errorMessage = rules.messages.required;
        }

        // 값이 있을 때만 다른 유효성 규칙 적용
        if (isValid && value !== '') {
            // 최소 길이 검사
            if (rules.min && value.length < rules.min) {
                isValid = false;
                errorMessage = rules.messages.min;
            }
            // 최대 길이 검사
            if (isValid && rules.max && value.length > rules.max) {
                isValid = false;
                errorMessage = rules.messages.max;
            }
            // 정규식 패턴 검사
            if (isValid && rules.pattern && !rules.pattern.test(value)) {
                isValid = false;
                errorMessage = rules.messages.pattern;
            }
            // 비밀번호 일치 검사 (confirmPassword 전용)
            if (isValid && fieldName === 'confirmPassword' && rules.matches) {
                const passwordInput = document.getElementById(rules.matches);
                if (passwordInput && value !== passwordInput.value) {
                    isValid = false;
                    errorMessage = rules.messages.matches;
                }
                // 비밀번호 변경 시 확인 비밀번호 재검사 트리거
                if (passwordInput) {
                    // 이벤트 리스너가 중복 추가되는 것을 방지
                    passwordInput.removeEventListener('input', revalidateConfirmPassword);
                    passwordInput.addEventListener('input', revalidateConfirmPassword);
                }
            }
        }

        function revalidateConfirmPassword() {
            validateField(document.getElementById('confirmPassword'));
        }

        // 최종 상태 반영: 유효성 검사 결과에 따라 클래스와 아이콘 업데이트
        if (isValid) { // 유효한 경우
            input.classList.add('is-valid');
            if (iconElement) {
                iconElement.classList.add('valid');
                iconElement.textContent = 'check_circle'; // Material Icons 체크 아이콘
            }
        } else { // 유효성 검사 실패 시
            input.classList.add('is-invalid');
            if (errorSpan) errorSpan.textContent = errorMessage;
            if (iconElement) {
                iconElement.classList.add('invalid');
                iconElement.textContent = 'cancel'; // Material Icons X 아이콘
            }
        }
        return isValid;
    }


    // 모달 관련 함수
    window.showModal = function (errors) { // 전역으로 노출하여 HTML에서 직접 호출 가능하게 함
        modalErrorList.innerHTML = ''; // 기존 오류 목록 지우기
        if (errors && errors.length > 0) {
            errors.forEach(error => {
                const li = document.createElement('li');
                li.textContent = error;
                modalErrorList.appendChild(li);
            });
            modal.style.display = 'flex'; // flex로 설정하여 중앙 정렬 활성화
        }
    }

    window.closeModal = function () { // 전역으로 노출하여 HTML에서 직접 호출 가능하게 함
        modal.style.display = 'none'; // 모달 숨김
        // 모달 닫을 때 모든 필드의 유효성 상태 초기화 (선택 사항)
        inputs.forEach(input => {
            input.classList.remove('is-valid', 'is-invalid');
            const errorSpan = document.getElementById(input.id + '-error');
            if (errorSpan) errorSpan.textContent = '';
            const iconElement = document.getElementById(input.id + '-icon');
            if (iconElement) {
                iconElement.classList.remove('valid', 'invalid');
                iconElement.textContent = '';
            }
        });
    }

    // 성공 모달 관련 함수
    function showSuccessModal() {
        successModal.style.display = 'flex';
    }
});