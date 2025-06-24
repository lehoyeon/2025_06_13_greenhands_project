package com.grrenhand.greenhand.chatbot.controller;

import com.grrenhand.greenhand.login.domain.User;
import com.grrenhand.greenhand.login.service.UserService;
import com.grrenhand.greenhand.login.config.CustomUser; // CustomUser 임포트

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Controller; // ### @RestController 대신 @Controller 사용 ###
import org.springframework.ui.Model; // Model 임포트
import org.springframework.web.bind.annotation.GetMapping; // GET 매핑 임포트
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

import com.grrenhand.greenhand.chatbot.dto.ChatbotRequestDTO;


// ### @RestController 대신 @Controller 사용 ###
@Controller // 이 컨트롤러는 뷰(HTML)를 반환할 수 있습니다.
@RequestMapping // 최상위 경로 설정 (필요에 따라 /api/chatbot 등으로 나눌 수 있습니다)
public class ChatbotController {

    private final RestTemplate restTemplate;
    private final UserService userService;

    public ChatbotController(RestTemplate restTemplate, UserService userService) {
        this.restTemplate = restTemplate;
        this.userService = userService;
    }

    // 챗봇 HTML 페이지를 렌더링하는 엔드포인트
    // URL: /chatbot.html (브라우저에서 직접 접근하는 URL)
    @GetMapping("/chatbot.html")
    public String getChatbotPage(Model model) {
        Long userId = null;

        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

        if (authentication != null && authentication.isAuthenticated() && !"anonymousUser".equals(authentication.getPrincipal())) {
            Object principal = authentication.getPrincipal();

            if (principal instanceof CustomUser) {
                userId = ((CustomUser) principal).getUserId();
                System.out.println("DEBUG: User ID from CustomUser (for HTML): " + userId);
            } else if (principal instanceof OAuth2User) {
                String oauth2Id = ((OAuth2User) principal).getName();
                Optional<User> userOptional = userService.findByUsername(oauth2Id);
                if (userOptional.isPresent()) {
                    userId = userOptional.get().getUserId();
                    System.out.println("DEBUG: OAuth2 User's actual userId from DB (for HTML): " + userId);
                }
            } else if (principal instanceof UserDetails) {
                String username = ((UserDetails) principal).getUsername();
                Optional<User> userOptional = userService.findByUsername(username);
                if (userOptional.isPresent()) {
                    userId = userOptional.get().getUserId();
                    System.out.println("DEBUG: User ID from UserDetails (DB lookup for HTML): " + userId);
                }
            }
        }

        // user_id를 Thymeleaf 템플릿으로 전달합니다.
        model.addAttribute("user_id", userId);

        // "chatbot" 뷰를 반환합니다. 이는 src/main/resources/templates/chatbot.html을 찾습니다.
        return "chatbot";
    }


    // 챗봇에게 질문 보내기 API (이것은 기존 RestController와 동일하게 API 역할)
    // URL: /api/chatbot/ask (프론트엔드 JavaScript에서 fetch로 호출하는 URL)
    @PostMapping("/api/chatbot/ask") // @RequestMapping이 /api/chatbot으로 설정되어 있지 않으므로, 전체 경로를 명시합니다.
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
    // URL: /api/chatbot/history (프론트엔드 JavaScript에서 fetch로 호출하는 URL)
    @GetMapping("/api/chatbot/history") // @RequestMapping이 /api/chatbot으로 설정되어 있지 않으므로, 전체 경로를 명시합니다.
    public ResponseEntity<?> getChatHistory() {
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
            return new ResponseEntity<>(Map.of("message", "사용자 정보를 확인할 수 없어 채팅 기록을 불러올 수 없습니다. 다시 로그인해주세요."), HttpStatus.UNAUTHORIZED);
        }

        try {
            String pythonChatbotHistoryUrl = "http://localhost:8000/chatbot/history/" + userId;
            System.out.println("DEBUG: Requesting chat history from Python for user_id: " + userId);

            ResponseEntity<String[]> pythonResponse = restTemplate.getForEntity(pythonChatbotHistoryUrl, String[].class);

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