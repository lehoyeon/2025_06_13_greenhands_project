// src/main/java/com/grrenhand/greenhand/config/WebConfig.java

package com.grrenhand.greenhand.config; // 프로젝트의 주 설정 패키지

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration // 이 클래스가 Spring 설정 클래스임을 명시
public class WebConfig implements WebMvcConfigurer { // WebMvcConfigurer 인터페이스 구현

    // application.yml에서 정의한 file.upload-dir 값을 주입받습니다.
    @Value("${file.upload-dir}")
    private String uploadDir;

    /**
     * 웹 애플리케이션에 정적 리소스 핸들러를 추가합니다.
     * /uploads/** 로 시작하는 URL 요청을 파일 시스템의 실제 경로에 매핑합니다.
     */
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        // "/uploads/**" URL 패턴으로 들어오는 요청을 처리합니다.
        // 예를 들어, http://localhost:8080/uploads/img-diagnoses/abc.jpg 로 요청이 오면
        // 실제로는 ./uploads/img-diagnoses/abc.jpg 파일을 찾게 됩니다.
        registry.addResourceHandler("/uploads/**")
                // addResourceLocations("file:" + uploadDir + "/") 는 로컬 파일 시스템 경로를 지정합니다.
                // 'file:' 접두사가 중요하며, 뒤에 슬래시 '/'를 붙여 디렉토리임을 명시합니다.
                .addResourceLocations("file:" + uploadDir + "/");
    }
}
