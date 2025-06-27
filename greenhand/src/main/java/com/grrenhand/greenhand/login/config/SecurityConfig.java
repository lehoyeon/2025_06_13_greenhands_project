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
                .csrf(csrf -> csrf.disable())
                .authorizeHttpRequests(authorize -> authorize
                        .requestMatchers(
                                // static 리소스 허용
                                "/css/**", // /resources/static/css/ 아래 모든 파일
                                "/js/**",  // /resources/static/js/ 아래 모든 파일
                                // HTML 파일들 직접 접근 허용 (스크린샷 기반)
                                "/", // 루트 경로 (보통 index.html 또는 리다이렉트)
                                "/1.html",
                                "/3.html",
                                "/chatbot.html",
                                "/crop_plus.html",
                                "/img.html",
                                "/login.html",
                                "/main.html",
                                "/signup.html",
                                "/images/**", // 만약 images 폴더가 static 아래 있다면 추가 (스크린샷에 없지만 기존 설정에 있었음)

                                // 기존 설정에서 유지된 경로
                                "/register", // 회원가입 처리 URL
                                "/api/find-id",
                                "/api/reset-password",
                                "/oauth2/**" // OAuth2 로그인 관련 URL
                        ).permitAll()
                        // 특정 API는 인증된 사용자(USER 역할)만 접근 가능
                        .requestMatchers("/api/main/user/me").hasRole("USER")
                        .requestMatchers("/api/chatbot/**").hasRole("USER")
                        .anyRequest().authenticated() // 그 외 모든 요청은 인증 필요
                )
                .formLogin(form -> form
                        .loginPage("/login.html") // 변경된 로그인 페이지 경로
                        .loginProcessingUrl("/do-login")
                        .defaultSuccessUrl("/main.html", true) // 변경된 메인 페이지 경로
                        .failureUrl("/login.html?error")
                        .permitAll()
                )
                .logout(logout -> logout
                        .logoutUrl("/logout")
                        .logoutSuccessUrl("/login.html?logout") // 변경된 로그인 페이지 경로
                        .invalidateHttpSession(true)
                        .deleteCookies("JSESSIONID")
                        .permitAll()
                )
                .oauth2Login(oauth2 -> oauth2
                        .loginPage("/login.html") // 변경된 로그인 페이지 경로
                        .userInfoEndpoint(userInfo -> userInfo
                                .userService(customOAuth2UserService)
                        )
                        .defaultSuccessUrl("/main.html", true) // 변경된 메인 페이지 경로
                        .failureUrl("/login.html?oauth2Error")
                );

        return http.build();
    }

    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}