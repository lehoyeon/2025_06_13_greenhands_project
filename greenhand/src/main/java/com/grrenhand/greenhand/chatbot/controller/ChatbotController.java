package com.grrenhand.greenhand.chatbot.controller;

// 필요한 임포트들은 그대로 유지

import com.grrenhand.greenhand.login.domain.User;
import com.grrenhand.greenhand.login.service.UserService;
import com.grrenhand.greenhand.login.config.CustomUser; // CustomUser 임포트
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Controller; // @Controller 유지 (필요하다면)
import org.springframework.ui.Model; // Model 임포트
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

import com.grrenhand.greenhand.chatbot.dto.ChatbotRequestDTO;


// 이 컨트롤러는 API 엔드포인트만 제공하는 것이 좋으므로 @RestController로 변경하거나,
// HTML 서빙을 하지 않는다면 아예 @RequestMapping을 제거하고 특정 API에만 @RequestMapping을 붙이는 게 좋습니다.
@RestController // API 컨트롤러로 변경하는 것을 강력히 권장
@RequestMapping("/api/chatbot") // 챗봇 관련 API의 기본 경로를 /api/chatbot으로 설정
public class ChatbotController {

    private final RestTemplate restTemplate;
    private final UserService userService;

    public ChatbotController(RestTemplate restTemplate, UserService userService) {
        this.restTemplate = restTemplate;
        this.userService = userService;
    }

    // 챗봇 HTML 페이지를 렌더링하는 엔드포인트는 이 컨트롤러에서 제거합니다.
    // /chatbot.html (또는 /chatbot/chatbot.html)은 정적 리소스로 Spring이 직접 서빙합니다.
    // 따라서 이 @GetMapping("/chatbot.html") 메소드는 제거해야 합니다!
    /*
    @GetMapping("/chatbot.html")
    public String getChatbotPage(Model model) {
        // 이 메소드 자체가 필요 없습니다.
        // Spring이 resources/static/chatbot/chatbot.html을 직접 서빙할 것입니다.
        // 만약 user_id를 HTML에 직접 심어야 한다면, Thymeleaf/JSP 같은 템플릿 엔진을 사용하거나
        // JavaScript에서 /api/main/user/me를 호출하는 기존 방식을 사용해야 합니다.
        return "chatbot"; // 이 뷰 이름을 반환하면 templates 폴더를 찾습니다.
    }
    */

    // 챗봇에게 질문 보내기 API (이것은 기존 RestController와 동일하게 API 역할)
    // URL: /api/chatbot/ask (프론트엔드 JavaScript에서 fetch로 호출하는 URL)
    @PostMapping("/ask") // @RequestMapping이 /api/chatbot으로 설정되었으므로, /ask만 붙이면 됩니다.
    public ResponseEntity<?> askChatbot(@RequestBody ChatbotRequestDTO requestDTO) {
        // 이 부분의 userId 가져오는 로직은 이전과 동일하게 유지됩니다.
        // Spring Security의 Principal에서 userId를 가져오는 로직은 이미 최적화되어 있습니다.
        Long userId = null;
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

        if (authentication != null && authentication.isAuthenticated() && !"anonymousUser".equals(authentication.getPrincipal())) {
            Object principal = authentication.getPrincipal();
            if (principal instanceof CustomUser) {
                userId = ((CustomUser) principal).getUserId();
            } else if (principal instanceof OAuth2User) {
                String oauth2Id = ((OAuth2User) principal).getName();
                Optional<User> userOptional = userService.findByUsername(oauth2Id);
                if (userOptional.isPresent()) {
                    userId = userOptional.get().getUserId();
                }
            } else if (principal instanceof UserDetails) {
                String username = ((UserDetails) principal).getUsername();
                Optional<User> userOptional = userService.findByUsername(username);
                if (userOptional.isPresent()) {
                    userId = userOptional.get().getUserId();
                }
            }
        }

        if (userId == null) {
            return new ResponseEntity<>(Map.of("message", "사용자 정보를 확인할 수 없습니다. 다시 로그인해주세요."), HttpStatus.UNAUTHORIZED);
        }

        try {
            String pythonChatbotServiceUrl = "http://localhost:8000/chatbot/ask";

            Map<String, Object> pythonRequestBody = new HashMap<>();
            pythonRequestBody.put("user_id", userId);
            pythonRequestBody.put("user_query", requestDTO.getUserQuery());
            pythonRequestBody.put("context", requestDTO.getContext());

            System.out.println("DEBUG: Sending to Python - user_id: " + userId + ", user_query: " + requestDTO.getUserQuery());

            ResponseEntity<Map> pythonResponse = restTemplate.postForEntity(pythonChatbotServiceUrl, pythonRequestBody, Map.class);

            if (pythonResponse.getStatusCode().is2xxSuccessful() && pythonResponse.getBody() != null) {
                return new ResponseEntity<>(pythonResponse.getBody(), HttpStatus.OK);
            } else {
                return new ResponseEntity<>(Map.of("message", "챗봇 서버 오류: " + pythonResponse.getStatusCode() + " " + pythonResponse.getBody()), HttpStatus.BAD_GATEWAY);
            }
        } catch (Exception e) {
            e.printStackTrace();
            return new ResponseEntity<>(Map.of("message", "챗봇 통신 중 오류가 발생했습니다."), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    // 챗봇 이력 가져오기 API 엔드포인트
    // URL: /api/chatbot/history/{userId} (프론트엔드 JavaScript에서 fetch로 호출하는 URL)
    @GetMapping("/history/{userId}") // @RequestMapping이 /api/chatbot으로 설정되었으므로, /history/{userId}만 붙이면 됩니다.
    public ResponseEntity<?> getChatHistory(@PathVariable Long userId) { // userId를 PathVariable로 받음
        // 이 부분의 userId는 이미 PathVariable로 받았으므로, Principal에서 가져오는 로직은 불필요합니다.
        // 하지만 보안을 위해 PathVariable로 받은 userId와 로그인된 유저의 userId가 일치하는지 확인하는 로직을 추가하는 것이 좋습니다.
        Long authenticatedUserId = null;
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

        if (authentication != null && authentication.isAuthenticated() && !"anonymousUser".equals(authentication.getPrincipal())) {
            Object principal = authentication.getPrincipal();
            if (principal instanceof CustomUser) {
                authenticatedUserId = ((CustomUser) principal).getUserId();
            } else if (principal instanceof OAuth2User) {
                String oauth2Id = ((OAuth2User) principal).getName();
                Optional<User> userOptional = userService.findByUsername(oauth2Id);
                if (userOptional.isPresent()) {
                    authenticatedUserId = userOptional.get().getUserId();
                }
            } else if (principal instanceof UserDetails) {
                String username = ((UserDetails) principal).getUsername();
                Optional<User> userOptional = userService.findByUsername(username);
                if (userOptional.isPresent()) {
                    authenticatedUserId = userOptional.get().getUserId();
                }
            }
        }

        // 보안 검사: 요청된 userId와 현재 로그인된 userId가 다르면 접근 거부
        if (authenticatedUserId == null || !authenticatedUserId.equals(userId)) {
            return new ResponseEntity<>(Map.of("message", "접근 권한이 없습니다."), HttpStatus.FORBIDDEN);
        }


        try {
            String pythonChatbotHistoryUrl = "http://localhost:8000/chatbot/history/" + userId;
            System.out.println("DEBUG: Requesting chat history from Python for user_id: " + userId);

            // FastAPI가 반환하는 응답이 String[] (질문 문자열 배열)일 수도 있고
            // 또는 [{"user_query": "...", "timestamp": "..."}, ...] 같은 객체 배열일 수도 있습니다.
            // 스크린샷에서 [object Object]가 떴었으므로, 객체 배열일 가능성이 큽니다.
            // 따라서 Map[] 또는 List<Map<String, Object>> 등으로 받는 것이 안전합니다.
            ResponseEntity<Object[]> pythonResponse = restTemplate.getForEntity(pythonChatbotHistoryUrl, Object[].class);


            if (pythonResponse.getStatusCode().is2xxSuccessful() && pythonResponse.getBody() != null) {
                return new ResponseEntity<>(pythonResponse.getBody(), HttpStatus.OK);
            } else {
                return new ResponseEntity<>(Map.of("message", "챗봇 기록 서버 오류: " + pythonResponse.getStatusCode() + " " + pythonResponse.getBody()), HttpStatus.BAD_GATEWAY);
            }
        } catch (Exception e) {
            e.printStackTrace();
            return new ResponseEntity<>(Map.of("message", "챗봇 기록 통신 중 오류가 발생했습니다."), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
}