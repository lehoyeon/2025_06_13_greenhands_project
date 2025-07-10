package com.grrenhand.greenhand.login.service;

import com.grrenhand.greenhand.login.domain.User; // User 엔티티 임포트
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.client.userinfo.DefaultOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserService;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.user.DefaultOAuth2User;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Service;

import java.sql.Timestamp;
import java.time.LocalDateTime; // LocalDateTime 임포트 (Timestamp 대신 사용 권장)
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

@Service
public class CustomOAuth2UserService implements OAuth2UserService<OAuth2UserRequest, OAuth2User> {

    private final DefaultOAuth2UserService defaultOAuth2UserService = new DefaultOAuth2UserService();
    private final UserService userService; // UserService 주입

    public CustomOAuth2UserService(UserService userService) {
        this.userService = userService;
    }

    @Override
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        OAuth2User oauth2User = defaultOAuth2UserService.loadUser(userRequest);

        String registrationId = userRequest.getClientRegistration().getRegistrationId();
        String userNameAttributeName = userRequest.getClientRegistration().getProviderDetails().getUserInfoEndpoint().getUserNameAttributeName();

        String nickname = null;
        String email = null;
        // OAuth2User.getName()이 카카오의 고유 ID(숫자)를 반환합니다.
        // 이를 socialId로 사용하고 User 엔티티의 username 필드에 저장합니다.
        String socialId = oauth2User.getName();

        if ("kakao".equals(registrationId)) {
            Map<String, Object> attributes = oauth2User.getAttributes();
            if (attributes.containsKey("kakao_account")) {
                Map<String, Object> kakaoAccount = (Map<String, Object>) attributes.get("kakao_account");
                if (kakaoAccount != null) {
                    Map<String, Object> profile = (Map<String, Object>) kakaoAccount.get("profile");
                    if (profile != null && profile.containsKey("nickname")) {
                        nickname = (String) profile.get("nickname");
                    }
                    if (kakaoAccount.containsKey("email")) {
                        email = (String) kakaoAccount.get("email");
                    }
                }
            }
            System.out.println("[CustomOAuth2UserService] Extracted Kakao Nickname: " + nickname);
            System.out.println("[CustomOAuth2UserService] Kakao Social ID: " + socialId);
            System.out.println("[CustomOAuth2UserService] Extracted Kakao Email: " + email);
        }

        // DB에 사용자 정보 저장/업데이트 로직
        Optional<User> existingUser = userService.findByUsername(socialId); // socialId로 사용자 조회
        User user;

        if (existingUser.isPresent()) {
            user = existingUser.get();
            // 닉네임과 이메일은 카카오에서 받은 최신 정보로 업데이트
            user.setNickname(nickname != null ? nickname : user.getNickname());
            user.setEmail(email != null ? email : user.getEmail());
            user.setLastLoginAt(Timestamp.valueOf(LocalDateTime.now())); // 마지막 로그인 시간 업데이트
            System.out.println("[CustomOAuth2UserService] 기존 사용자 업데이트: ID=" + user.getUserId() + ", Username=" + user.getUsername());
        } else {
            user = new User();
            user.setUsername(socialId); // 카카오 고유 ID를 username 필드에 저장
            user.setNickname(nickname != null ? nickname : socialId); // 닉네임 저장
            user.setEmail(email); // 이메일 저장
            user.setCreatedAt(Timestamp.valueOf(LocalDateTime.now())); // 생성 시간
            user.setLastLoginAt(Timestamp.valueOf(LocalDateTime.now())); // 마지막 로그인 시간
            user.setPasswordHash(null); // 소셜 로그인 사용자는 비밀번호 없음
            user.setName(nickname); // 이름 필드가 있다면 닉네임으로 채움 (선택 사항)
            user.setAddress(null); // 기본값 null
            user.setPhoneNumber(null); // 기본값 null
            System.out.println("[CustomOAuth2UserService] 새 사용자 생성: Username=" + user.getUsername() + ", Nickname=" + user.getNickname());
        }
        user = userService.saveUser(user); // DB에 저장 또는 업데이트하고, 저장된 User 객체를 다시 받음 (userId 포함)
        System.out.println("[CustomOAuth2UserService] 사용자 DB 저장/업데이트 완료: UserID=" + user.getUserId());

        // SecurityContext에 저장할 속성 맵 생성 (OAuth2User 객체가 사용할 속성)
        Map<String, Object> newAttributes = new HashMap<>(oauth2User.getAttributes()); // 기존 속성 복사
        newAttributes.put("socialId", socialId); // 카카오 고유 ID
        newAttributes.put("nickname", nickname != null ? nickname : socialId); // 추출한 닉네임
        newAttributes.put("email", email); // 이메일
        newAttributes.put("userId", user.getUserId()); // DB에서 받은 실제 Long 타입 userId 추가

        // 최종 DefaultOAuth2User 객체 생성 및 반환
        return new DefaultOAuth2User(
                Collections.singletonList(new SimpleGrantedAuthority("ROLE_USER")), // 권한
                newAttributes, // 업데이트된 속성 맵
                userNameAttributeName // 사용자 고유 ID (카카오 ID)를 나타내는 속성 이름
        );
    }
}