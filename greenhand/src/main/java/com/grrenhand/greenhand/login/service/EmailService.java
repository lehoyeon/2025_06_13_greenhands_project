// src/main/java/com/grrenhand/greenhand/login/service/EmailService.java
package com.grrenhand.greenhand.login.service;

/**
 * 비밀번호 재설정 등에서 이메일을 발송하기 위한 서비스 인터페이스
 */
public interface EmailService {
    /**
     * 이메일 발송
     * @param to      받는 사람 이메일 주소
     * @param subject 이메일 제목
     * @param body    이메일 본문
     */
    void sendEmail(String to, String subject, String body);
}
