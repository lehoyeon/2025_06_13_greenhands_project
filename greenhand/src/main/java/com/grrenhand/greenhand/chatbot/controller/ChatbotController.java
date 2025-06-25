package com.grrenhand.greenhand.chatbot.controller;

import com.grrenhand.greenhand.chatbot.resource.CustomByteArrayResource;
import com.grrenhand.greenhand.login.config.CustomUser;
import com.grrenhand.greenhand.login.domain.User;
import com.grrenhand.greenhand.login.service.UserService;

import org.springframework.http.*;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.oauth2.core.user.OAuth2User;
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

    @PostMapping("/ask")
    public ResponseEntity<?> askChatbot(
            @RequestParam("userQuery") String userQuery,
            @RequestParam("userId") Long userIdFromRequest,
            @RequestPart(value = "imageFile", required = false) MultipartFile imageFile
    ) {
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

        if (authenticatedUserId == null || !authenticatedUserId.equals(userIdFromRequest)) {
            return new ResponseEntity<>(Map.of("message", "사용자 정보가 일치하지 않거나 접근 권한이 없습니다."), HttpStatus.UNAUTHORIZED);
        }

        try {
            String pythonChatbotServiceUrl = "http://localhost:8000/chatbot/ask";

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);

            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("user_id", authenticatedUserId);
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
                return new ResponseEntity<>(pythonResponse.getBody(), HttpStatus.OK);
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

    @GetMapping("/history/{userId}")
    public ResponseEntity<?> getChatHistory(@PathVariable Long userId) {
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

        if (authenticatedUserId == null || !authenticatedUserId.equals(userId)) {
            return new ResponseEntity<>(Map.of("message", "접근 권한이 없습니다."), HttpStatus.FORBIDDEN);
        }

        try {
            String pythonChatbotHistoryUrl = "http://localhost:8000/chatbot/history/" + userId;
            System.out.println("DEBUG Spring Boot: Requesting chat history from Python for user_id: " + userId);

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
