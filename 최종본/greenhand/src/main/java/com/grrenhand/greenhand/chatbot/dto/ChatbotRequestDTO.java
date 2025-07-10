// src/main/java/com/greenhand/greenhand/chatbot/dto/ChatbotRequestDTO.java

package com.grrenhand.greenhand.chatbot.dto;

import lombok.Data;

@Data
public class ChatbotRequestDTO {
    private String userQuery; // 사용자 질문
    private String context;   // 챗봇 대화 컨텍스트 (선택 사항)
    // user_id는 Spring Boot 백엔드에서 자동으로 가져오므로 DTO에는 필요 없습니다.
}