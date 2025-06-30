package com.grrenhand.greenhand.config; // SecurityConfig와 동일한 패키지

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

@Configuration // 이 클래스도 스프링 설정 클래스임을 명시
public class AppConfig {

    @Bean // PasswordEncoder 빈을 여기서 정의합니다.
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}