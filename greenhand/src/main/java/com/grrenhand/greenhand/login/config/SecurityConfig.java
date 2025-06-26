package com.grrenhand.greenhand.login.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
// import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder; // 제거
// import org.springframework.security.crypto.password.PasswordEncoder; // 제거
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
                                "/css/login/**", "/js/login/**", "/images/**",
                                "/login/login.html", "/login/signup.html", "/register",
                                "/main/**", "/css/main.css", "/js/main.js",
                                "/chatbot/**", "/css/chatbot.css", "/js/chatbot.js",
                                "/imgdiagnostics/**",
                                "/", "/1.html", "/2.html", "/3.html", "/5.html", "/7.html", "/8.html",
                                "/api/find-id", "/api/reset-password", "/oauth2/**"
                        ).permitAll()
                        .requestMatchers("/api/main/user/me").hasRole("USER")
                        .requestMatchers("/api/chatbot/**").hasRole("USER")
                        .anyRequest().authenticated()
                )
                .formLogin(form -> form
                        .loginPage("/login/login.html")
                        .loginProcessingUrl("/do-login")
                        .defaultSuccessUrl("/main/main.html", true)
                        .failureUrl("/login/login.html?error")
                        .permitAll()
                )
                .logout(logout -> logout
                        .logoutUrl("/logout")
                        .logoutSuccessUrl("/login/login.html?logout")
                        .invalidateHttpSession(true)
                        .deleteCookies("JSESSIONID")
                        .permitAll()
                )
                .oauth2Login(oauth2 -> oauth2
                        .loginPage("/login/login.html")
                        .userInfoEndpoint(userInfo -> userInfo
                                .userService(customOAuth2UserService)
                        )
                        .defaultSuccessUrl("/main/main.html", true)
                        .failureUrl("/login/login.html?oauth2Error")
                );

        return http.build();
    }

    // --- 👇 PasswordEncoder 빈 선언을 이 클래스에서 제거합니다. 👇 ---
    // @Bean
    // public PasswordEncoder passwordEncoder() {
    //     return new BCryptPasswordEncoder();
    // }
    // --- 👆 PasswordEncoder 빈 선언 제거 👆 ---

    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}