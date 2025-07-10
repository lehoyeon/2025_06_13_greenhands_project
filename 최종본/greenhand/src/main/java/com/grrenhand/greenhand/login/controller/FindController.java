package com.grrenhand.greenhand.login.controller;

import com.grrenhand.greenhand.login.dto.FindDTO;
import com.grrenhand.greenhand.login.domain.User; // User 엔티티가 필요할 수 있으므로 유지
import com.grrenhand.greenhand.login.service.UserService;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;
import java.util.Random; // 임시 비밀번호 생성을 위한 Random 클래스 import

@RestController
public class FindController {

    private final UserService userService;

    public FindController(UserService userService) {
        this.userService = userService;
    }

    // 아이디 찾기 API (이메일과 전화번호로 찾기)
    @PostMapping("/api/find-id")
    public ResponseEntity<?> findId(@RequestBody FindDTO findDTO) {
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
    public ResponseEntity<?> resetPassword(@RequestBody FindDTO findDTO) {
        if (findDTO.getUsername() == null || findDTO.getUsername().isEmpty() ||
                findDTO.getPhoneNumber() == null || findDTO.getPhoneNumber().isEmpty()) {
            return new ResponseEntity<>(Map.of("message", "아이디와 전화번호를 모두 입력해주세요."), HttpStatus.BAD_REQUEST);
        }

        try {
            boolean userExistsAndInfoMatches = userService.validateUserCredentials(findDTO.getUsername(), findDTO.getPhoneNumber());
            if (userExistsAndInfoMatches) {
                // ⭐⭐⭐ 이 부분 수정 시작: 임시 비밀번호 생성 및 반환 ⭐⭐⭐
                String newTempPassword = generateRandomPassword(); // 임시 비밀번호 생성

                // UserService를 통해 사용자 비밀번호 업데이트
                boolean updateSuccess = userService.updateUserPassword(findDTO.getUsername(), newTempPassword);

                if (updateSuccess) {
                    return new ResponseEntity<>(
                            Map.of("message", "새로운 임시 비밀번호가 발급되었습니다. 로그인 후 변경 권장합니다.", "newPassword", newTempPassword), // 프론트엔드로 임시 비밀번호 직접 전달
                            HttpStatus.OK
                    );
                } else {
                    return new ResponseEntity<>(Map.of("message", "비밀번호 업데이트 중 오류가 발생했습니다."), HttpStatus.INTERNAL_SERVER_ERROR);
                }
                // ⭐⭐⭐ 이 부분 수정 끝 ⭐⭐⭐
            } else {
                return new ResponseEntity<>(Map.of("message", "아이디와 전화번호 정보가 일치하지 않습니다."), HttpStatus.NOT_FOUND);
            }
        } catch (Exception e) {
            e.printStackTrace();
            return new ResponseEntity<>(Map.of("message", "비밀번호 재설정 중 오류가 발생했습니다."), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    // ⭐⭐⭐ 새로운 메서드 추가: 임시 비밀번호 생성 ⭐⭐⭐
    private String generateRandomPassword() {
        int length = 10; // 임시 비밀번호 길이
        String chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()";
        Random random = new Random();
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < length; i++) {
            sb.append(chars.charAt(random.nextInt(chars.length())));
        }
        return sb.toString();
    }
    // ⭐⭐⭐ 새로운 메서드 추가 끝 ⭐⭐⭐
}