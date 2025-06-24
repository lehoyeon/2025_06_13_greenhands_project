package com.grrenhand.greenhand.login.config; // 패키지명은 이대로 사용해주세요.

import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.userdetails.User;
import java.util.Collection;

public class CustomUser extends User {

    private final Long userId; // 여기에 사용자의 고유 ID를 저장할 것입니다.

    public CustomUser(String username, String password, Collection<? extends GrantedAuthority> authorities, Long userId) {
        super(username, password, authorities); // 스프링 시큐리티의 기본 User 생성자 호출
        this.userId = userId; // user_id 저장
    }

    public Long getUserId() {
        return userId;
    }
}