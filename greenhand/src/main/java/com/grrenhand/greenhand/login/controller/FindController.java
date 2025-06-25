// src/main/java/com/grrenhand/greenhand/login/controller/FindController.java

package com.grrenhand.greenhand.login.controller;

// 이전 AccountRecoveryController에서 FindController로 이름 변경
// 기존 FindAccountDTO 대신 FindDTO 임포트
import com.grrenhand.greenhand.login.dto.FindDTO; // FindDTO 임포트
import com.grrenhand.greenhand.login.domain.User; // User 엔티티 임포트 (UserService에서 User를 반환할 경우)
import com.grrenhand.greenhand.login.service.UserService; // UserService 임포트

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController; // @RestController 임포트

import java.util.Map;


@RestController // 이 클래스가 RESTful API 컨트롤러임을 명시
public class FindController { // AccountRecoveryController에서 FindController로 클래스명 변경

    private final UserService userService;

    public FindController(UserService userService) { // 생성자명도 FindController로 변경
        this.userService = userService;
    }

    // 아이디 찾기 API (이메일과 전화번호로 찾기)
    @PostMapping("/api/find-id")
    public ResponseEntity<?> findId(@RequestBody FindDTO findDTO) { // FindAccountDTO 대신 FindDTO 사용
        if (findDTO.getEmail() == null || findDTO.getEmail().isEmpty() ||
                findDTO.getPhoneNumber() == null || findDTO.getPhoneNumber().isEmpty()) {
            return new ResponseEntity<>(Map.of("message", "이메일과 전화번호를 모두 입력해주세요."), HttpStatus.BAD_REQUEST);
        }
        String foundUsername = userService.findUserIdByEmailAndPhoneNumber(findDTO.getEmail(), findDTO.getPhoneNumber());
        if (foundUsername != null) {
            return new ResponseEntity<>(Map.of("message", "아이디를 찾았습니다.", "username", foundUsername), HttpStatus.OK);
        } else {
            return new ResponseEntity<>(Map.of("message", "해당 이메일과 전화번호로 가입된 아이디를 찾을 수 없습니다."), HttpStatus.NOT_FOUND);
        }
    }

    // 비밀번호 재설정 API (아이디와 전화번호로 찾기)
    @PostMapping("/api/reset-password")
    public ResponseEntity<?> resetPassword(@RequestBody FindDTO findDTO) { // FindAccountDTO 대신 FindDTO 사용
        if (findDTO.getUsername() == null || findDTO.getUsername().isEmpty() ||
                findDTO.getPhoneNumber() == null || findDTO.getPhoneNumber().isEmpty()) {
            return new ResponseEntity<>(Map.of("message", "아이디와 전화번호를 모두 입력해주세요."), HttpStatus.BAD_REQUEST);
        }

        try {
            boolean userExistsAndInfoMatches = userService.validateUserCredentials(findDTO.getUsername(), findDTO.getPhoneNumber());
            if (userExistsAndInfoMatches) {
                // TODO: 실제 임시 비밀번호 생성 및 이메일 발송 로직 구현
                return new ResponseEntity<>(Map.of("message", "임시 비밀번호가 이메일로 발송되었습니다."), HttpStatus.OK);
            } else {
                return new ResponseEntity<>(Map.of("message", "아이디와 전화번호 정보가 일치하지 않습니다."), HttpStatus.NOT_FOUND);
            }
        } catch (Exception e) {
            e.printStackTrace();
            return new ResponseEntity<>(Map.of("message", "비밀번호 재설정 중 오류가 발생했습니다."), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
}