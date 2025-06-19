// src/main/java/com/greenhand/greenhand/login/controller/LoginController.java

package com.grrenhand.greenhand.login.controller;

import com.grrenhand.greenhand.login.dto.UserDTO;
import com.grrenhand.greenhand.login.service.UserService;
import org.springframework.http.HttpStatus; // HTTP 상태 코드 임포트
import org.springframework.http.ResponseEntity; // JSON 응답과 HTTP 상태 코드를 위해 임포트
import org.springframework.validation.BindingResult; // 유효성 검사 결과 임포트
import org.springframework.validation.FieldError; // 필드 오류 정보 임포트
import org.springframework.web.bind.annotation.PostMapping; // @PostMapping 임포트
import org.springframework.web.bind.annotation.RequestBody; // AJAX 요청 본문(JSON)을 받기 위한 임포트
import org.springframework.web.bind.annotation.RestController; // @RestController 임포트 (가장 중요)

import jakarta.validation.Valid; // @Valid 임포트
import java.util.HashMap; // Map 구현체를 위해 임포트
import java.util.Map; // Map 인터페이스를 위해 임포트

// 아이디/비밀번호 찾기 API 요청을 위한 DTO 임포트
import com.grrenhand.greenhand.login.dto.FindDTO; // FindAccountDTO에서 FindDTO로 이름 변경되었으니 이 DTO를 임포트


@RestController // 이 클래스가 RESTful API 컨트롤러임을 명시
public class LoginController {

    private final UserService userService;

    public LoginController(UserService userService) {
        this.userService = userService;
    }

    // GET /signup 요청은 HTML 파일을 직접 서빙할 것이므로 컨트롤러에서 처리할 필요 없습니다.
    // @GetMapping("/signup")
    // public String showSignupForm() {
    //     return "login/signup.html";
    // }

    // 회원가입 처리 요청 (AJAX로부터 JSON 데이터를 받아서 JSON 응답 반환)
    @PostMapping("/register") // 회원가입 폼 제출 시 이 URL로 POST 요청 (AJAX 요청을 받음)
    public ResponseEntity<?> registerUser(@Valid @RequestBody UserDTO userDTO, BindingResult bindingResult) {

        Map<String, String> errors = new HashMap<>(); // 오류 메시지를 담을 맵

        // 1. @Valid 어노테이션에 의한 기본 유효성 검사 결과 확인 (UserDTO에 정의된 @NotBlank, @Size 등)
        if (bindingResult.hasErrors()) {
            for (FieldError error : bindingResult.getFieldErrors()) {
                errors.put(error.getField(), error.getDefaultMessage());
            }
            // 400 Bad Request 상태 코드와 함께 오류 맵 반환
            return new ResponseEntity<>(errors, HttpStatus.BAD_REQUEST);
        }

        // 2. 비즈니스 로직 유효성 검사 (예: 비밀번호 확인 필드 일치 여부)
        if (!userDTO.getPassword().equals(userDTO.getConfirmPassword())) {
            errors.put("confirmPassword", "비밀번호와 비밀번호 확인이 일치하지 않습니다.");
            return new ResponseEntity<>(errors, HttpStatus.BAD_REQUEST);
        }

        // 3. UserService를 통한 실제 회원가입 처리 및 추가 비즈니스 로직 유효성 검사 (중복 아이디/이메일/닉네임)
        try {
            userService.registerNewUser(userDTO);
            // 200 OK 상태 코드와 함께 성공 메시지 반환
            return new ResponseEntity<>(Map.of("message", "회원가입이 성공적으로 완료되었습니다."), HttpStatus.OK);
        } catch (IllegalArgumentException e) {
            // UserService에서 던진 IllegalArgumentException (아이디/이메일/닉네임 중복 등) 처리
            String field = "";
            String errorMessage = e.getMessage();

            if (errorMessage.contains("아이디")) {
                field = "username";
            } else if (errorMessage.contains("이메일")) {
                field = "email";
            } else if (errorMessage.contains("닉네임")) {
                field = "nickname";
            } else {
                field = "general";
            }
            errors.put(field, errorMessage);
            return new ResponseEntity<>(errors, HttpStatus.BAD_REQUEST);
        } catch (Exception e) {
            e.printStackTrace();
            errors.put("general", "회원가입 중 알 수 없는 서버 오류가 발생했습니다.");
            return new ResponseEntity<>(errors, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    // =========================================================================
    // 아이디/비밀번호 찾기 API 엔드포인트는 이제 FindController에 있습니다.
    // LoginController에서는 관련 메서드를 모두 제거합니다.
    // =========================================================================

    // @PostMapping("/api/find-id")
    // public ResponseEntity<?> findId(@RequestBody FindDTO findDTO) { /* ... */ }

    // @PostMapping("/api/reset-password")
    // public ResponseEntity<?> resetPassword(@RequestBody FindDTO findDTO) { /* ... */ }
}