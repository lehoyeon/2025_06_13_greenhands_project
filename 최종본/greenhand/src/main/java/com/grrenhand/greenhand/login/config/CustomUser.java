package com.grrenhand.greenhand.login.config;

import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.userdetails.User; // Spring Security의 User 클래스
import org.springframework.security.oauth2.core.user.OAuth2User; // OAuth2User 인터페이스 임포트
import java.util.Collection;
import java.util.Map; // Map 임포트

// CustomUser 클래스는 Spring Security의 User (UserDetails 구현)를 상속받고,
// 동시에 OAuth2User 인터페이스도 구현하여 일반 로그인/소셜 로그인 사용자 정보를 통합 관리합니다.
public class CustomUser extends User implements OAuth2User {

    private final Long userId; // 사용자의 DB 고유 ID
    private final String nickname; // 사용자의 닉네임 필드 추가
    private Map<String, Object> attributes; // OAuth2User의 추가 속성들을 저장할 맵

    // 1. 일반 로그인 사용자를 위한 생성자 (UserDetails 역할)
    // 이 생성자는 CustomUserDetailsService에서 사용될 수 있습니다.
    public CustomUser(String username, String password, Collection<? extends GrantedAuthority> authorities,
                      Long userId, String nickname) {
        super(username, password, authorities); // Spring Security의 기본 User 생성자 호출
        this.userId = userId;
        this.nickname = nickname;
        this.attributes = null; // 일반 로그인 사용자는 attributes가 없음
    }

    // 2. OAuth2 로그인 사용자를 위한 생성자 (OAuth2User 역할)
    // 이 생성자는 CustomOAuth2UserService에서 사용될 것입니다.
    public CustomUser(String username, String password, Collection<? extends GrantedAuthority> authorities,
                      Long userId, String nickname, Map<String, Object> attributes) {
        super(username, password, authorities); // Spring Security의 기본 User 생성자 호출
        this.userId = userId;
        this.nickname = nickname;
        this.attributes = attributes;
    }

    // --- 👇 추가된 Getter 메서드 👇 ---

    @Override
    public Map<String, Object> getAttributes() {
        return attributes;
    }

    // OAuth2User 인터페이스의 getName() 메서드 구현
    // 보통 OAuth2Provider에서 제공하는 고유 ID (카카오의 경우 숫자 ID)를 반환합니다.
    // 여기서는 UserDetails의 username을 재활용합니다.
    @Override
    public String getName() {
        return super.getUsername(); // OAuth2User.getName()은 UserDetails의 username을 사용
    }

    public Long getUserId() {
        return userId;
    }

    // 닉네임 Getter 추가
    public String getNickname() {
        return nickname;
    }

    // --- 👆 추가된 Getter 메서드 👆 ---
}