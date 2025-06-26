// src/main/java/com/grrenhand/greenhand/login/service/CustomOAuth2UserService.java

package com.grrenhand.greenhand.login.service;

import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.client.userinfo.DefaultOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserService;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.user.DefaultOAuth2User;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.HashMap; // Map을 만들기 위해 임포트

@Service // 스프링 빈으로 등록
public class CustomOAuth2UserService implements OAuth2UserService<OAuth2UserRequest, OAuth2User> {

    // UserRepository 주입 부분을 제거합니다.
    // private final UserRepository userRepository;

    // DefaultOAuth2UserService는 내부적으로 생성하거나, 생성자 주입을 없앱니다.
    // 여기서는 간단히 내부에서 생성합니다.
    private final DefaultOAuth2UserService defaultOAuth2UserService = new DefaultOAuth2UserService();

    // 생성자를 변경하여 UserRepository를 주입받지 않도록 합니다.
    public CustomOAuth2UserService() {
        // 기본 생성자
    }

    @Override
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        // 1. 기본 OAuth2UserService를 사용하여 사용자 정보 로드 (이것만 남김)
        OAuth2User oauth2User = defaultOAuth2UserService.loadUser(userRequest);

        // 2. 최소한의 정보로 DefaultOAuth2User 객체 반환
        // 실제 유저 정보는 아직 처리하지 않습니다. 빈이 생성되는지만 확인합니다.
        String userNameAttributeName = userRequest.getClientRegistration().getProviderDetails().getUserInfoEndpoint().getUserNameAttributeName();

        // 임시로 사용할 속성 맵 (실제 데이터는 없음)
        HashMap<String, Object> attributes = new HashMap<>();
        attributes.put(userNameAttributeName, oauth2User.getAttribute(userNameAttributeName)); // 기본 ID만 복사

        return new DefaultOAuth2User(
                Collections.singletonList(new SimpleGrantedAuthority("ROLE_USER")), // 임시 권한
                attributes, // 최소한의 속성
                userNameAttributeName // 사용자 고유 ID를 나타내는 속성 이름
        );
    }
}