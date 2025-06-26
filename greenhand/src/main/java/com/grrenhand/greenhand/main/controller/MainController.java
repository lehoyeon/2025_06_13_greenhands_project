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
        String username = null; // 일반 로그인 유저의 username 또는 OAuth2User의 name(socialId)
        String nickname = null;
        String email = null;
        Long userId = null; // DB에서 조회된 user_id (Long 타입)

        if (principal instanceof UserDetails) { // 일반 로그인 사용자 (폼 로그인)
            username = ((UserDetails) principal).getUsername();
            Optional<User> userOptional = userService.findByUsername(username);
            if(userOptional.isPresent()){
                User user = userOptional.get();
                userId = user.getUserId();
                nickname = user.getNickname();
                email = user.getEmail();
            } else {
                // DB에서 찾지 못했을 경우 (예외 처리 또는 기본값 설정)
                System.err.println("MainController: UserDetails로부터 사용자 정보를 찾았으나 DB에서 찾지 못함. Username: " + username);
            }

        } else if (principal instanceof OAuth2User) { // OAuth2 로그인 사용자 (카카오)
            OAuth2User oauth2User = (OAuth2User) principal;
            // CustomOAuth2UserService에서 Attributes에 추가한 정보를 직접 사용합니다.
            // OAuth2User.getName()은 카카오 고유 ID (숫자)입니다.
            username = oauth2User.getName(); // 혹은 oauth2User.getAttribute("socialId");

            // CustomOAuth2UserService에서 이미 attributes에 넣어준 닉네임, 이메일, userId를 가져옵니다.
            nickname = (String) oauth2User.getAttribute("nickname");
            email = (String) oauth2User.getAttribute("email");
            userId = (Long) oauth2User.getAttribute("userId"); // <--- CustomOAuth2UserService에서 추가한 userId 가져오기

            // 로그 추가: 어떤 값이 넘어왔는지 확인
            System.out.println("MainController - OAuth2User Info: username=" + username + ", nickname=" + nickname + ", email=" + email + ", userId=" + userId);

            // userId가 null인 경우를 대비하여 DB에서 한번 더 조회 시도 (선택 사항, CustomOAuth2UserService가 잘 작동하면 필요 없음)
            if (userId == null) {
                System.out.println("MainController - userId가 OAuth2User attributes에 없어 DB에서 재조회 시도: " + username);
                Optional<User> userOptional = userService.findByUsername(username); // 카카오 ID로 DB 조회
                if(userOptional.isPresent()){
                    User user = userOptional.get();
                    userId = user.getUserId(); // DB에서 가져온 실제 userId
                    System.out.println("MainController - DB 재조회 성공! userId: " + userId);
                } else {
                    System.err.println("MainController - DB 재조회 실패! Username: " + username);
                }
            }


        } else {
            return new ResponseEntity<>(Map.of("message", "사용자 정보를 가져올 수 없습니다."), HttpStatus.INTERNAL_SERVER_ERROR);
        }

        // 최종 사용자 정보 맵 생성 (클라이언트에 반환)
        Map<String, Object> userInfo = new HashMap<>(); // Long 타입의 userId를 위해 Object로 변경
        userInfo.put("username", username);
        // 클라이언트에서 'null' 문자열을 처리하지 않도록 명확하게 null 처리
        userInfo.put("nickname", (nickname != null && !nickname.isEmpty() && !"null".equals(nickname)) ? nickname : (username != null && !username.isEmpty() ? username : "사용자"));
        userInfo.put("email", email);
        userInfo.put("userId", userId); // Long 타입 그대로 전달

        return new ResponseEntity<>(userInfo, HttpStatus.OK);
    }
}