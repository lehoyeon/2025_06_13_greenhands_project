// src/main/java/com/grrenhand/greenhand/login/dto/UserDTO.java

package com.grrenhand.greenhand.login.dto;

import lombok.Data;
import jakarta.validation.constraints.Email;     // 이메일 유효성 검사 임포트
import jakarta.validation.constraints.NotBlank;  // 빈 문자열/공백만 있는 문자열 검사 임포트
import jakarta.validation.constraints.Pattern;   // 정규 표현식 검사 임포트
import jakarta.validation.constraints.Size;      // 문자열 길이 검사 임포트

@Data // Lombok: getter, setter, equals, hashCode, toString 자동 생성
public class UserDTO {

    // V3: 아이디 (영문/숫자 조합, 6~20자)
    @NotBlank(message = "아이디는 필수 입력 값입니다.")
    @Size(min = 6, max = 20, message = "아이디는 6자 이상 20자 이하로 입력해주세요.")
    @Pattern(regexp = "^[a-zA-Z0-9]+$", message = "아이디는 영문과 숫자만 가능합니다.")
    private String username;

    // V4: 비밀번호 (영문/숫자/특수문자 포함, 8~16자)
    @NotBlank(message = "비밀번호는 필수 입력 값입니다.")
    @Size(min = 8, max = 16, message = "비밀번호는 8자 이상 16자 이하로 입력해주세요.")
    @Pattern(regexp = "^(?=.*[a-zA-Z])(?=.*\\d)(?=.*[!@#$%^&*()_+-=\\[\\]{};':\"\\\\|,.<>/?]).*$",
            message = "비밀번호는 영문, 숫자, 특수문자를 포함해야 합니다.")
    private String password;

    // V5: 비밀번호 확인 (V4 비밀번호와 일치 여부 - 이 부분은 Controller/Service에서 직접 검증)
    @NotBlank(message = "비밀번호 확인은 필수 입력 값입니다.")
    private String confirmPassword;

    // V1: 닉네임 (문자열 형식, 2~10자)
    @NotBlank(message = "닉네임은 필수 입력 값입니다.")
    @Size(min = 2, max = 10, message = "닉네임은 2자 이상 10자 이하로 입력해주세요.")
    private String nickname;

    // V2: 이름 (한글/영문, 2~20자 이내)
    // @NotBlank는 없으므로 선택 입력
    @Size(min = 2, max = 20, message = "이름은 2자 이상 20자 이하로 입력해주세요.")
    @Pattern(regexp = "^[a-zA-Z가-힣]+$", message = "이름은 한글 또는 영문만 가능합니다.")
    private String name;

    // V6: 이메일 주소 (유효한 이메일 형식)
    @NotBlank(message = "이메일은 필수 입력 값입니다.") // 이메일 필수로 가정
    @Email(message = "유효한 이메일 주소를 입력해주세요.")
    @Size(max = 100, message = "이메일은 100자 이하로 입력해주세요.")
    private String email;

    // 주소는 길이에 대한 제한만
    @Size(max = 255, message = "주소는 255자 이하로 입력해주세요.")
    private String address;

    // V7: 전화번호 (숫자 형식)
    // @NotBlank는 없으므로 선택 입력
    @Size(max = 20, message = "전화번호는 20자 이하로 입력해주세요.")
    @Pattern(regexp = "^[0-9-]+$", message = "전화번호는 숫자와 하이픈(-)만 가능합니다.")
    private String phoneNumber; // Java 컨벤션에 맞춰 'phoneNumber'로 사용

    // userId, passwordHash, createdAt, lastLoginAt 등은 DTO에 포함하지 않습니다.
    // 이는 User 엔티티에서 직접 관리되거나 서비스 계층에서 처리됩니다.
}