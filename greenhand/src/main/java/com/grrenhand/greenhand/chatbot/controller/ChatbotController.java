package com.grrenhand.greenhand.chatbot.controller;

import com.grrenhand.greenhand.chatbot.resource.CustomByteArrayResource;
import com.grrenhand.greenhand.login.config.CustomUser; // CustomUser 임포트
import com.grrenhand.greenhand.login.domain.User;
import com.grrenhand.greenhand.login.service.UserService;

import org.springframework.http.*;
import org.springframework.security.core.Authentication; // Authentication 임포트
import org.springframework.security.core.context.SecurityContextHolder; // SecurityContextHolder 임포트
import org.springframework.security.core.userdetails.UserDetails; // UserDetails 임포트
import org.springframework.security.oauth2.core.user.OAuth2User; // OAuth2User 임포트
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.*;

@RestController
@RequestMapping("/api/chatbot")
public class ChatbotController {

    private final RestTemplate restTemplate;
    private final UserService userService;

    public ChatbotController(RestTemplate restTemplate, UserService userService) {
        this.restTemplate = restTemplate;
        this.userService = userService;
    }

    // --- 👇 /ask 메서드 수정 👇 ---
    @PostMapping("/ask")
    public ResponseEntity<?> askChatbot(
            @RequestParam("userQuery") String userQuery,
            // @RequestParam("userId") Long userIdFromRequest, // 프론트엔드에서 userId를 직접 받지 않습니다.
            @RequestPart(value = "imageFile", required = false) MultipartFile imageFile,
            Authentication authentication // Spring Security Authentication 객체를 주입받습니다.
    ) {
        Long authenticatedUserId = null;
        String userNickname = "사용자"; // 챗봇 응답에 사용할 닉네임

        // 1. Authentication 객체로부터 사용자 ID와 닉네임을 안전하게 추출
        if (authentication != null && authentication.isAuthenticated() && !"anonymousUser".equals(authentication.getPrincipal())) {
            Object principal = authentication.getPrincipal();

            if (principal instanceof CustomUser) { // 커스텀 UserDetails/OAuth2User 구현체인 경우
                authenticatedUserId = ((CustomUser) principal).getUserId();
                userNickname = ((CustomUser) principal).getNickname(); // CustomUser에 닉네임이 있다면
            } else if (principal instanceof OAuth2User) { // OAuth2 로그인 사용자 (카카오)
                // CustomOAuth2UserService에서 userId를 attributes에 추가했으므로 바로 가져옵니다.
                authenticatedUserId = (Long) ((OAuth2User) principal).getAttribute("userId");
                userNickname = (String) ((OAuth2User) principal).getAttribute("nickname");
                if (userNickname == null) userNickname = ((OAuth2User) principal).getName(); // 닉네임 없으면 카카오ID 사용
            } else if (principal instanceof UserDetails) { // 일반 로그인 사용자 (Standard UserDetails)
                String username = ((UserDetails) principal).getUsername();
                Optional<User> userOptional = userService.findByUsername(username);
                if (userOptional.isPresent()) {
                    User user = userOptional.get();
                    authenticatedUserId = user.getUserId();
                    userNickname = user.getNickname();
                }
            }
        }

        // 2. 인증된 사용자 ID가 없으면 UNAUTHORIZED 응답
        if (authenticatedUserId == null) {
            System.err.println("ERROR ChatbotController: Authenticated userId is null. Unauthorized access attempt.");
            return new ResponseEntity<>(Map.of("message", "사용자 정보를 확인할 수 없습니다. 다시 로그인해주세요."), HttpStatus.UNAUTHORIZED);
        }

        System.out.println("DEBUG Spring Boot: 챗봇 질문 처리 시작. Authenticated userId: " + authenticatedUserId + ", userQuery: " + userQuery);

        try {
            String pythonChatbotServiceUrl = "http://localhost:8000/chatbot/ask";

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);

            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("user_id", authenticatedUserId); // 백엔드에서 추출한 ID 사용
            body.add("user_query", userQuery);

            if (imageFile != null && !imageFile.isEmpty()) {
                CustomByteArrayResource resource = new CustomByteArrayResource(
                        imageFile.getBytes(),
                        imageFile.getOriginalFilename(),
                        MediaType.parseMediaType(imageFile.getContentType())
                );

                HttpHeaders imageHeaders = new HttpHeaders();
                imageHeaders.setContentType(resource.getCustomContentType());

                HttpEntity<CustomByteArrayResource> filePart = new HttpEntity<>(resource, imageHeaders);
                body.add("image_file", filePart);
            }

            HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

            System.out.println("DEBUG Spring Boot: Sending chatbot request to Python. user_id: " + authenticatedUserId + ", user_query: " + userQuery.substring(0, Math.min(userQuery.length(), 50)) + "...");
            if (imageFile != null && !imageFile.isEmpty()) {
                System.out.println("DEBUG Spring Boot: Image file attached: " + imageFile.getOriginalFilename() + ", size: " + imageFile.getSize() + " bytes, Actual Content-Type: " + imageFile.getContentType());
            }

            ResponseEntity<Map> pythonResponse = restTemplate.postForEntity(pythonChatbotServiceUrl, requestEntity, Map.class);

            if (pythonResponse.getStatusCode().is2xxSuccessful() && pythonResponse.getBody() != null) {
                // 챗봇 응답에 사용자 닉네임을 포함하여 반환 (선택 사항)
                Map<String, Object> responseBody = new HashMap<>(pythonResponse.getBody());
                responseBody.put("user_nickname", userNickname); // 프론트에서 활용할 수 있도록
                return new ResponseEntity<>(responseBody, HttpStatus.OK);
            } else {
                String errorMessage = "챗봇 서버 오류: " + pythonResponse.getStatusCode();
                if (pythonResponse.getBody() != null && pythonResponse.getBody() instanceof Map) {
                    Map<String, Object> errorBody = (Map<String, Object>) pythonResponse.getBody();
                    if (errorBody.containsKey("detail")) {
                        errorMessage += " - " + errorBody.get("detail");
                    } else {
                        errorMessage += " - " + errorBody.toString();
                    }
                } else if (pythonResponse.getBody() != null) {
                    errorMessage += " - " + pythonResponse.getBody().toString();
                }
                System.err.println("ERROR Spring Boot: FastAPI Chatbot Response Error: " + errorMessage);
                return new ResponseEntity<>(Map.of("message", errorMessage), HttpStatus.BAD_GATEWAY);
            }
        } catch (IOException e) {
            e.printStackTrace();
            return new ResponseEntity<>(Map.of("message", "이미지 파일 처리 중 오류가 발생했습니다: " + e.getMessage()), HttpStatus.INTERNAL_SERVER_ERROR);
        } catch (Exception e) {
            e.printStackTrace();
            return new ResponseEntity<>(Map.of("message", "챗봇 통신 중 오류가 발생했습니다: " + e.getMessage()), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    // --- 👇 /history/{userId} 메서드 수정 👇 ---
    @GetMapping("/history/{userIdFromPath}") // PathVariable 이름 변경
    public ResponseEntity<?> getChatHistory(
            @PathVariable("userIdFromPath") Long userIdFromPath, // PathVariable 이름 변경
            Authentication authentication // Authentication 객체 주입
    ) {
        Long authenticatedUserId = null;

        // 1. Authentication 객체로부터 현재 인증된 사용자 ID 추출
        if (authentication != null && authentication.isAuthenticated() && !"anonymousUser".equals(authentication.getPrincipal())) {
            Object principal = authentication.getPrincipal();
            if (principal instanceof CustomUser) {
                authenticatedUserId = ((CustomUser) principal).getUserId();
            } else if (principal instanceof OAuth2User) {
                authenticatedUserId = (Long) ((OAuth2User) principal).getAttribute("userId");
            } else if (principal instanceof UserDetails) {
                String username = ((UserDetails) principal).getUsername();
                Optional<User> userOptional = userService.findByUsername(username);
                if (userOptional.isPresent()) {
                    authenticatedUserId = userOptional.get().getUserId();
                }
            }
        }

        // 2. 인증된 사용자 ID가 없거나, PathVariable ID와 일치하지 않으면 FORBIDDEN
        if (authenticatedUserId == null || !authenticatedUserId.equals(userIdFromPath)) {
            System.err.println("ERROR ChatbotController: History access denied. Authenticated userId: " + authenticatedUserId + ", Path userId: " + userIdFromPath);
            return new ResponseEntity<>(Map.of("message", "사용자 정보가 일치하지 않거나 접근 권한이 없습니다."), HttpStatus.FORBIDDEN);
        }

        System.out.println("DEBUG Spring Boot: Requesting chat history from Python for user_id: " + userIdFromPath);

        try {
            String pythonChatbotHistoryUrl = "http://localhost:8000/chatbot/history/" + userIdFromPath;
            ResponseEntity<List> pythonResponse = restTemplate.getForEntity(pythonChatbotHistoryUrl, List.class);

            if (pythonResponse.getStatusCode().is2xxSuccessful() && pythonResponse.getBody() != null) {
                return new ResponseEntity<>(pythonResponse.getBody(), HttpStatus.OK);
            } else {
                String errorMessage = "챗봇 기록 서버 오류: " + pythonResponse.getStatusCode();
                if (pythonResponse.getBody() != null) {
                    errorMessage += " - " + pythonResponse.getBody().toString();
                }
                System.err.println("ERROR Spring Boot: FastAPI Chatbot History Response Error: " + errorMessage);
                return new ResponseEntity<>(Map.of("message", errorMessage), HttpStatus.BAD_GATEWAY);
            }
        } catch (Exception e) {
            e.printStackTrace();
            return new ResponseEntity<>(Map.of("message", "챗봇 기록 통신 중 오류가 발생했습니다: " + e.getMessage()), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
}