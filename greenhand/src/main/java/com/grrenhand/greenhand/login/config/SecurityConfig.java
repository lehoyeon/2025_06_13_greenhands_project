// src/main/java/com/grrenhand/greenhand/login/config/SecurityConfig.java

package com.grrenhand.greenhand.login.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;

// OAuth2 로그인 처리용 임포트
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserService;
import org.springframework.security.oauth2.core.user.OAuth2User;


@Configuration // 이 클래스가 스프링 설정 클래스임을 명시
@EnableWebSecurity // 스프링 시큐리티 활성화
public class SecurityConfig {

    // CustomOAuth2UserService를 주입받아 사용 (Spring이 @Service 어노테이션이 붙은 CustomOAuth2UserService 빈을 찾아 자동으로 주입해줍니다.)
    private final OAuth2UserService<OAuth2UserRequest, OAuth2User> customOAuth2UserService;

    // 생성자에 customOAuth2UserService를 주입받습니다.
    public SecurityConfig(OAuth2UserService<OAuth2UserRequest, OAuth2User> customOAuth2UserService) {
        this.customOAuth2UserService = customOAuth2UserService;
    }


    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                .csrf(csrf -> csrf.disable()) // 개발 편의상 CSRF 보호 비활성화 (실제 배포 시에는 적절히 설정)
                .authorizeHttpRequests(authorize -> authorize
                        .requestMatchers(
                                "/css/login/**",     // /static/css/login/ 아래의 모든 CSS 파일 허용
                                "/js/login/**",      // /static/js/login/ 아래의 모든 JS 파일 허용 (만약 있다면)
                                "/images/**",        // 이미지 파일 허용
                                "/login/login.html", // login.html 페이지 허용
                                "/login/signup.html",// signup.html 페이지 허용
                                "/register",         // 회원가입 요청 처리 URL 허용
                                "/oauth2/**",        // OAuth2 로그인 관련 URL 허용
                                "/api/**"           // 모든 /api/ 경로 허용 (더 넓은 범위)
                        ).permitAll() // 위의 경로들은 인증 없이 접근 허용
                        .anyRequest().authenticated() // 그 외 모든 요청은 인증 필요
                )
                .formLogin(form -> form
                        .loginPage("/login/login.html") // 커스텀 로그인 페이지 URL (static/login/login.html)
                        .loginProcessingUrl("/do-login") // 로그인 폼이 제출될 URL (HTML 폼의 action="/do-login"과 일치)
                        .defaultSuccessUrl("/main.html", true) // 로그인 성공 시 이동할 URL (static/main.html)
                        .failureUrl("/login/login.html?error") // 로그인 실패 시 이동할 URL (에러 파라미터 추가)
                        .permitAll() // 로그인 관련 페이지는 모두 접근 허용
                )
                .logout(logout -> logout
                        .logoutUrl("/logout") // 로그아웃 URL
                        .logoutSuccessUrl("/login/login.html?logout") // 로그아웃 성공 시 이동할 URL
                        .invalidateHttpSession(true) // 세션 무효화
                        .deleteCookies("JSESSIONID") // 쿠키 삭제
                        .permitAll()
                )
                // =========================================================
                // OAuth2 로그인 설정 (CustomOAuth2UserService 빈을 사용하도록 지정)
                // =========================================================
                .oauth2Login(oauth2 -> oauth2
                        .loginPage("/login/login.html") // OAuth2 로그인 시작 페이지
                        .userInfoEndpoint(userInfo -> userInfo
                                .userService(customOAuth2UserService) // 주입받은 customOAuth2UserService 필드를 사용합니다.
                        )
                        .defaultSuccessUrl("/main.html", true) // OAuth2 로그인 성공 시 이동할 URL
                        .failureUrl("/login/login.html?oauth2Error") // OAuth2 로그인 실패 시 이동할 URL (로그인 페이지로 돌아감)
                );

        return http.build();
    }

    // 비밀번호 암호화를 위한 BCryptPasswordEncoder 빈 등록
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    // CustomUserDetailsService 구현체는 별도로 @Service 어노테이션으로 등록됩니다. (CustomUserDetailsService.java)
    // CustomOAuth2UserService 구현체도 별도로 @Service 어노테이션으로 등록됩니다. (CustomOAuth2UserService.java)
    // Spring은 @Service가 붙은 클래스를 자동으로 빈으로 찾아 주입합니다.
}