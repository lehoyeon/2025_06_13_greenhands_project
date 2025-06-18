// src/main/java/com/grrenhand/greenhand/login/controller/LoginController.java

package com.grrenhand.greenhand.login.controller;

import com.grrenhand.greenhand.login.dto.UserDTO;
import com.grrenhand.greenhand.login.service.UserService;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import jakarta.validation.Valid; // @Valid 어노테이션을 위한 임포트
import org.springframework.validation.BindingResult; // 유효성 검사 결과를 받기 위한 임포트
import org.springframework.validation.FieldError; // 필드 오류 정보를 위한 임포트

import java.util.List; // List 타입을 위한 임포트
import java.util.stream.Collectors; // 스트림 API의 Collectors를 위한 임포트


@Controller
public class LoginController {
    private final UserService userService;

    public LoginController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping("/signup") // 회원가입 폼을 보여주는 URL
    public String showSignupForm() {
        return "login/signup.html"; // resources/static/login/signup.html로 연결
    }

    // 회원가입 처리 요청
    @PostMapping("/register") // 회원가입 폼 제출 시 이 URL로 POST 요청
    // @Valid 어노테이션을 UserDTO 앞에 추가하여 유효성 검사를 트리거하고,
    // BindingResult 객체를 매개변수로 추가하여 유효성 검사 결과를 받습니다.
    public String registerUser(@Valid UserDTO userDTO, BindingResult bindingResult, RedirectAttributes redirectAttributes) {

        // 1. @Valid 어노테이션에 의한 기본 유효성 검사 결과 확인 (UserDTO에 정의된 @NotBlank, @Size 등)
        if (bindingResult.hasErrors()) {
            // 유효성 검사 오류가 있다면
            // 오류 메시지들을 직접 URL 파라미터로 넘기지 않고, 'validationError' 코드만 넘깁니다.
            // (Flash Attribute로 상세 오류를 넘겨도 정적 HTML에서 직접 받을 수 없기 때문)
            redirectAttributes.addFlashAttribute("error", true);
            redirectAttributes.addFlashAttribute("errorText", "validationError");

            // 또한, 상세한 유효성 검사 오류 메시지를 콘솔에 출력하여 개발 시 디버깅을 돕습니다.
            bindingResult.getFieldErrors().forEach(error ->
                    System.out.println("Validation Error on field '" + error.getField() + "': " + error.getDefaultMessage())
            );

            // 유효성 검사 실패 시 회원가입 페이지로 리다이렉트
            return "redirect:/login/signup.html?error=true&errorText=validationError";
        }

        // 2. 비즈니스 로직 유효성 검사 (예: 비밀번호 확인 일치 여부, DTO에 @AssertTrue 등으로도 가능)
        if (!userDTO.getPassword().equals(userDTO.getConfirmPassword())) {
            redirectAttributes.addFlashAttribute("error", true);
            redirectAttributes.addFlashAttribute("errorText", "passwordMismatch"); // 비밀번호 불일치 에러 코드
            return "redirect:/login/signup.html?error=true&errorText=passwordMismatch";
        }

        // 3. UserService를 통한 실제 회원가입 처리 및 DB 저장
        try {
            userService.registerNewUser(userDTO);
            redirectAttributes.addFlashAttribute("signupSuccess", true); // 회원가입 성공 시 플래시 어트리뷰트
            return "redirect:/login/login.html?signupSuccess=true"; // 로그인 페이지로 리다이렉트
        } catch (IllegalArgumentException e) {
            // UserService에서 던진 IllegalArgumentException 처리 (아이디/이메일/닉네임 중복 등)
            String errorKey;
            if (e.getMessage().contains("이미 존재하는 아이디")) {
                errorKey = "usernameExists";
            } else if (e.getMessage().contains("이미 사용 중인 이메일")) {
                errorKey = "emailExists";
            } else if (e.getMessage().contains("이미 사용 중인 닉네임")) { // 닉네임 중복 에러 추가
                errorKey = "nicknameExists";
            }
            else {
                errorKey = "unknownSignupError"; // 예상치 못한 IllegalArgumentException
            }
            redirectAttributes.addFlashAttribute("error", true);
            redirectAttributes.addFlashAttribute("errorText", errorKey);
            return "redirect:/login/signup.html?error=true&errorText=" + errorKey;
        } catch (Exception e) {
            // 그 외 예상치 못한 서버 오류 (예: DB 연결 문제, 기타 런타임 오류)
            redirectAttributes.addFlashAttribute("error", true);
            redirectAttributes.addFlashAttribute("errorText", "serverError");
            // 디버깅을 위해 콘솔에 예외 스택 트레이스 출력
            e.printStackTrace();
            return "redirect:/login/signup.html?error=true&errorText=serverError";
        }
    }
}