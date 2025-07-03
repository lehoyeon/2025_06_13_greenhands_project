package com.grrenhand.greenhand.login.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.web.SecurityFilterChain;

import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserService;
import org.springframework.security.oauth2.core.user.OAuth2User;

import org.springframework.web.client.RestTemplate;

import com.grrenhand.greenhand.login.service.CustomOAuth2UserService;


@Configuration
@EnableWebSecurity
public class SecurityConfig {

    private final OAuth2UserService<OAuth2UserRequest, OAuth2User> customOAuth2UserService;

    public SecurityConfig(CustomOAuth2UserService customOAuth2UserService) {
        this.customOAuth2UserService = customOAuth2UserService;
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                .csrf(csrf -> csrf.disable()) // 개발 편의를 위해 CSRF 비활성화 (운영 시에는 활성화 권장)
                .authorizeHttpRequests(authorize -> authorize
                        .requestMatchers(
                                // static 리소스 허용
                                "/css/**", // /resources/static/css/ 아래 모든 파일
                                "/js/**",  // /resources/static/js/ 아래 모든 파일
                                "/images/**", // /resources/static/images/ 아래 모든 파일 (필요시)
                                // HTML 파일들 직접 접근 허용
                                "/", // 루트 경로 (보통 index.html 또는 리다이렉트)
                                "/3.html",
                                "/chatbot.html",
                                "/crop_plus.html",
                                "/img.html",
                                "/main.html",
                                "/login.html", // 로그인 페이지
                                "/signup.html", // <--- 이 부분이 수정되었습니다. 회원가입 페이지 경로
                                // 기존 설정에서 유지된 경로
                                "/register", // 회원가입 처리 URL (POST)
                                "/api/find-id", // 아이디 찾기 API (POST)
                                "/api/reset-password", // 비밀번호 재설정 API (POST)
                                "/oauth2/**" // OAuth2 로그인 관련 URL
                        ).permitAll() // 위에 명시된 경로들은 모두 인증 없이 접근 허용
                        // 특정 API는 인증된 사용자(USER 역할)만 접근 가능
                        .requestMatchers("/api/main/user/me").hasRole("USER")
                        .requestMatchers("/api/chatbot/**").hasRole("USER")
                        .anyRequest().authenticated() // 그 외 모든 요청은 인증 필요
                )
                .formLogin(form -> form
                        .loginPage("/login.html") // 로그인 페이지 지정
                        .loginProcessingUrl("/do-login") // 로그인 처리 URL
                        .defaultSuccessUrl("/main.html", true) // 로그인 성공 시 리다이렉트할 기본 URL
                        .failureUrl("/login.html?error") // 로그인 실패 시 리다이렉트할 URL
                        .permitAll() // 로그인 관련 페이지는 인증 없이 접근 허용
                )
                .logout(logout -> logout
                        .logoutUrl("/logout") // 로그아웃 처리 URL
                        .logoutSuccessUrl("/login.html?logout") // 로그아웃 성공 시 리다이렉트할 URL
                        .invalidateHttpSession(true) // 세션 무효화
                        .deleteCookies("JSESSIONID") // JSESSIONID 쿠키 삭제
                        .permitAll() // 로그아웃 관련 페이지는 인증 없이 접근 허용
                )
                .oauth2Login(oauth2 -> oauth2
                        .loginPage("/login.html") // OAuth2 로그인 페이지 지정 (일반 로그인 페이지와 동일)
                        .userInfoEndpoint(userInfo -> userInfo
                                .userService(customOAuth2UserService) // 사용자 정보 서비스 설정
                        )
                        .defaultSuccessUrl("/main.html", true) // OAuth2 로그인 성공 시 리다이렉트할 기본 URL
                        .failureUrl("/login.html?oauth2Error") // OAuth2 로그인 실패 시 리다이렉트할 URL
                );

        return http.build();
    }

    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate(); // RestTemplate 빈 등록
    }
}
