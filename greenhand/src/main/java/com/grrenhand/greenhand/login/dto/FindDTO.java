// src/main/java/com/grrenhand/greenhand/login/dto/FindDTO.java

package com.grrenhand.greenhand.login.dto;

import lombok.Data;

@Data
public class FindDTO {
    private String username;    // 비밀번호 찾기에 사용
    private String email;       // 아이디 찾기에 사용
    private String phoneNumber; // 아이디/비밀번호 찾기에 사용
}