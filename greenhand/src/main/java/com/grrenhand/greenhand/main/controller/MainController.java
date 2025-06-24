// src/main/java/com/greenhand/greenhand/main/controller/MainController.java

package com.grrenhand.greenhand.main.controller;

import com.grrenhand.greenhand.login.domain.User;
import com.grrenhand.greenhand.login.service.UserService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/main")
public class MainController {

    private final UserService userService;

    public MainController(UserService userService) {
        this.userService = userService;
    }

    // 로그인된 사용자 정보 반환 API
    @GetMapping("/user/me")
    public ResponseEntity<?> getCurrentUser() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

        if (authentication == null || !authentication.isAuthenticated() || "anonymousUser".equals(authentication.getPrincipal())) {
            return new ResponseEntity<>(Map.of("message", "인증되지 않은 사용자입니다."), HttpStatus.UNAUTHORIZED);
        }

        Object principal = authentication.getPrincipal();
        String username = null;
        String nickname = null;
        String email = null;
        Long userId = null; // user_id 추가 (Long 타입)

        if (principal instanceof UserDetails) {
            username = ((UserDetails) principal).getUsername();
            Optional<User> userOptional = userService.findByUsername(username);
            if(userOptional.isPresent()){
                User user = userOptional.get();
                userId = user.getUserId(); // user_id 가져오기
                nickname = user.getNickname();
                email = user.getEmail();
            }

        } else if (principal instanceof OAuth2User) {
            OAuth2User oauth2User = (OAuth2User) principal;
            username = oauth2User.getName(); // OAuth ID (카카오의 'id' 속성)

            // 카카오에서 제공하는 사용자 정보(attributes)에서 닉네임, 이메일 등 추출
            Map<String, Object> kakaoAccount = oauth2User.getAttribute("kakao_account");
            if (kakaoAccount != null) {
                Map<String, Object> profile = (Map<String, Object>) kakaoAccount.get("profile");
                if (profile != null) {
                    nickname = (String) profile.get("nickname");
                }
                email = (String) kakaoAccount.get("email");
            }
            // DB에 저장된 사용자 정보로 닉네임/이메일 보충 (소셜 로그인 시 모든 정보를 가져오지 못할 수 있음)
            Optional<User> userOptional = userService.findByUsername(username);
            if(userOptional.isPresent()){
                User user = userOptional.get();
                userId = user.getUserId(); // user_id 가져오기
                if (nickname == null || nickname.isEmpty()) {
                    nickname = user.getNickname();
                }
                if (email == null || email.isEmpty()) {
                    email = user.getEmail();
                }
            }


        } else {
            return new ResponseEntity<>(Map.of("message", "사용자 정보를 가져올 수 없습니다."), HttpStatus.INTERNAL_SERVER_ERROR);
        }

        // 최종 사용자 정보 맵 생성 (클라이언트에 반환)
        Map<String, String> userInfo = new HashMap<>();
        userInfo.put("username", username);
        userInfo.put("nickname", (nickname != null && !nickname.isEmpty() && !"null".equals(nickname)) ? nickname : (username != null && !username.isEmpty() ? username : "사용자"));
        userInfo.put("email", email);
        userInfo.put("userId", String.valueOf(userId)); // user_id를 문자열로 변환하여 추가

        return new ResponseEntity<>(userInfo, HttpStatus.OK);
    }
}