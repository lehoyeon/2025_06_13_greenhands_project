package com.grrenhand.greenhand.login.config; // grrenhand 오타 유지

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

// RestTemplate 임포트 추가
import org.springframework.web.client.RestTemplate;


@Configuration // 이 클래스가 스프링 설정 클래스임을 명시
@EnableWebSecurity // 스프링 시큐리티 활성화
public class SecurityConfig {

    private final OAuth2UserService<OAuth2UserRequest, OAuth2User> customOAuth2UserService;

    public SecurityConfig(OAuth2UserService<OAuth2UserRequest, OAuth2User> customOAuth2UserService) {
        this.customOAuth2UserService = customOAuth2UserService;
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                .csrf(csrf -> csrf.disable()) // 개발 편의상 CSRF 보호 비활성화 (실제 배포 시에는 적절히 설정)
                .authorizeHttpRequests(authorize -> authorize
                        // --- 로그인 및 정적 리소스 허용 경로 업데이트 ---
                        .requestMatchers(
                                // 로그인 관련 페이지 및 리소스
                                "/css/login/**",     // /static/css/login/ 아래의 모든 CSS 파일 허용
                                "/js/login/**",      // /static/js/login/ 아래의 모든 JS 파일 허용
                                "/images/**",        // 이미지 파일 허용 (static/images/ 에 있다고 가정)
                                "/login/login.html", // login.html 페이지 허용
                                "/login/signup.html",// signup.html 페이지 허용
                                "/register",         // 회원가입 요청 처리 URL 허용

                                // 메인 페이지 관련 (새로운 경로 포함)
                                "/main/**",          // /static/main/ 아래의 모든 파일 (main.html 포함) 허용
                                "/css/main.css",     // /static/css/main.css 파일 허용
                                "/js/main.js",       // /static/js/main.js 파일 허용

                                // 챗봇 페이지 관련 (새로운 경로 포함)
                                "/chatbot/**",       // /static/chatbot/ 아래의 모든 파일 (chatbot.html 포함) 허용
                                "/css/chatbot.css",  // /static/css/chatbot.css 파일 허용
                                "/js/chatbot.js",    // /static/js/chatbot.js 파일 허용

                                // 작물 진단 페이지 관련 (새로운 imgdiagnostics 폴더 포함)
                                "/imgdiagnostics/**",// /static/imgdiagnostics/ 아래의 모든 파일 (img.html 포함) 허용

                                // 기타 정적 HTML 파일들 (static 루트에 있는 1.html, 2.html 등)
                                // Spring Boot는 기본적으로 static/*.* 에 대해 permitAll 하므로,
                                // 명시적으로 html 파일들을 추가하거나, 더 넓은 범위의 정적 리소스 패턴을 사용 가능합니다.
                                // 예: "/" 패턴을 permitAll()하면 모든 정적 리소스가 허용됩니다.
                                "/",                 // 루트 경로 (예: index.html)
                                "/1.html",
                                "/2.html",
                                "/3.html",
                                "/5.html",
                                "/7.html",
                                "/8.html",

                                // API 관련 (필요에 따라 permitAll로 설정)
                                "/api/find-id",      // 아이디 찾기 API 허용
                                "/api/reset-password",// 비밀번호 재설정 API 허용
                                "/oauth2/**"         // OAuth2 로그인 관련 URL 허용 (카카오 로그인 흐름에 필요)
                                // "/api/chatbot/ask",   // 챗봇 API는 인증된 사용자만 접근하도록 anyRequest().authenticated()로 보호
                                // "/api/chatbot/history/**" // 챗봇 기록 API도 인증된 사용자만 접근하도록 보호
                        ).permitAll() // 위의 경로들은 인증 없이 접근 허용
                        .anyRequest().authenticated() // 그 외 모든 요청은 인증 필요 (API 포함)
                )
                .formLogin(form -> form
                        .loginPage("/login/login.html") // 커스텀 로그인 페이지 URL (static/login/login.html)
                        .loginProcessingUrl("/do-login") // 로그인 폼이 제출될 URL (HTML 폼의 action="/do-login"과 일치)
                        .defaultSuccessUrl("/main/main.html", true) // 로그인 성공 시 이동할 URL (static/main/main.html)
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
                        .defaultSuccessUrl("/main/main.html", true) // OAuth2 로그인 성공 시 이동할 URL (static/main/main.html)
                        .failureUrl("/login/login.html?oauth2Error") // OAuth2 로그인 실패 시 이동할 URL (로그인 페이지로 돌아감)
                );

        return http.build();
    }

    // 비밀번호 암호화를 위한 BCryptPasswordEncoder 빈 등록
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    // RestTemplate 빈 등록 (HTTP 통신용) - ImgController 등에서 사용
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}
