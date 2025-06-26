package com.grrenhand.greenhand.main.controller;

import com.grrenhand.greenhand.login.domain.User; // User 엔티티 임포트 (로그인 모듈의 User 사용)
import com.grrenhand.greenhand.login.service.UserService; // UserService 임포트 (로그인 모듈의 UserService 사용)
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication; // 현재 인증 정보 가져오기 위함
import org.springframework.security.core.context.SecurityContextHolder; // SecurityContextHolder 가져오기 위함
import org.springframework.security.core.userdetails.UserDetails; // 일반 UserDetails 가져오기 위함
import org.springframework.security.oauth2.core.user.OAuth2User; // OAuth2User 가져오기 위함
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/main") // 이 컨트롤러의 모든 API는 /api/main으로 시작합니다.
public class MainController { // UserController에서 MainController로 이름 변경됨

    private final UserService userService; // UserService를 주입받아 사용자 상세 정보를 가져올 수 있음

    public MainController(UserService userService) {
        this.userService = userService;
    }

    // 로그인된 사용자 정보 반환 API
    @GetMapping("/user/me") // GET /api/main/user/me 요청 처리
    public ResponseEntity<?> getCurrentUser() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

        // 1. 인증되지 않은 사용자 체크
        if (authentication == null || !authentication.isAuthenticated() || "anonymousUser".equals(authentication.getPrincipal())) {
            // 인증되지 않은 사용자 (로그인하지 않은 경우)
            // Spring Security가 보호하는 엔드포인트이므로, 실제로는 이 코드가 실행되기 전에
            // 로그인 페이지로 리다이렉트될 가능성이 높습니다.
            return new ResponseEntity<>(Map.of("message", "인증되지 않은 사용자입니다."), HttpStatus.UNAUTHORIZED);
        }

        // 2. 인증된 사용자 정보 가져오기
        Object principal = authentication.getPrincipal();
        String username = null;
        String nickname = null;
        String email = null;

        if (principal instanceof UserDetails) {
            // 일반 로그인 사용자 (CustomUserDetailsService에서 반환하는 UserDetails)
            username = ((UserDetails) principal).getUsername();

            // DB에서 User 엔티티를 찾아 닉네임, 이메일 등 추가 정보 가져오기
            Optional<User> userOptional = userService.findByUsername(username);
            if(userOptional.isPresent()){
                User user = userOptional.get();
                nickname = user.getNickname();
                email = user.getEmail();
            }

        } else if (principal instanceof OAuth2User) {
            // OAuth2 (소셜) 로그인 사용자 (CustomOAuth2UserService에서 반환하는 OAuth2User)
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
                if (nickname == null || nickname.isEmpty()) { // 카카오에서 닉네임 못 가져왔다면 DB 닉네임 사용
                    nickname = user.getNickname();
                }
                if (email == null || email.isEmpty()) { // 카카오에서 이메일 못 가져왔다면 DB 이메일 사용
                    email = user.getEmail();
                }
            }


        } else {
            // 그 외 알 수 없는 Principal 타입 (예: 익명 사용자 등)
            return new ResponseEntity<>(Map.of("message", "사용자 정보를 가져올 수 없습니다."), HttpStatus.INTERNAL_SERVER_ERROR);
        }

        // 최종 사용자 정보 맵 생성 (클라이언트에 반환)
        Map<String, String> userInfo = new HashMap<>();
        userInfo.put("username", username);
        // 닉네임이 유효하면 닉네임 사용, 없으면 아이디 사용
        userInfo.put("nickname", (nickname != null && !nickname.isEmpty() && !"null".equals(nickname)) ? nickname : (username != null && !username.isEmpty() ? username : "사용자"));
        userInfo.put("email", email);

        return new ResponseEntity<>(userInfo, HttpStatus.OK);
    }
    // TODO: 앞으로 /api/main/user/me 외에 메인 페이지와 관련된 다른 API들을 이곳에 추가합니다.
    // 예를 들어, /api/main/crops/my 등 (현재는 구현 범위 아님)
}