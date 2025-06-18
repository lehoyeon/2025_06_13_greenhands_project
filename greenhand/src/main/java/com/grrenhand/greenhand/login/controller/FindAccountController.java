// src/main/java/com/grrenhand/greenhand/login/controller/FindAccountController.java
package com.grrenhand.greenhand.login.controller;

import com.grrenhand.greenhand.login.service.UserService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/user")
public class FindAccountController {

    private final UserService userService;

    public FindAccountController(UserService userService) {
        this.userService = userService;
    }

    @PostMapping("/find-id")
    public ResponseEntity<String> findId(@RequestParam("email") String email) {
        String userId = userService.findUserIdByEmail(email);
        if (userId != null) {
            return ResponseEntity.ok(userId);
        }
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body("가입된 아이디가 없습니다.");
    }

    @PostMapping("/find-password")
    public ResponseEntity<String> findPassword(
            @RequestParam("userId") String userId,
            @RequestParam("email") String email) {
        boolean valid = userService.validateUserEmail(userId, email);
        if (valid) {
            return ResponseEntity.ok("아이디와 이메일이 일치합니다. 비밀번호 재설정 페이지로 이동하세요.");
        }
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body("아이디 또는 이메일이 일치하지 않습니다.");
    }
}
