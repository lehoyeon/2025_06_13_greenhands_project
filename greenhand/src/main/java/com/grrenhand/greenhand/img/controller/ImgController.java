package com.grrenhand.greenhand.img.controller; // 패키지명 변경: imgdiagnostics로 통일

import com.grrenhand.greenhand.login.config.CustomUser; // CustomUser 임포트
import com.grrenhand.greenhand.login.domain.User; // User 임포트
import com.grrenhand.greenhand.login.service.UserService; // UserService 임포트
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication; // Authentication 임포트
import org.springframework.security.core.context.SecurityContextHolder; // SecurityContextHolder 임포트
import org.springframework.security.core.userdetails.UserDetails; // UserDetails 임포트
import org.springframework.security.oauth2.core.user.OAuth2User; // OAuth2User 임포트
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody; // @RequestBody 임포트
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional; // Optional 임포트

@RestController
@RequestMapping("/api/diagnose") // URL: /api/diagnose로 시작
public class ImgController { // 컨트롤러 이름도 ImgDiagnosticsController 등으로 변경하는 것이 일관성 있음 (현재는 ImgController 유지)

    private final RestTemplate restTemplate;
    private final UserService userService; // 사용자 서비스 주입 (userId 확인용)

    public ImgController(RestTemplate restTemplate, UserService userService) {
        this.restTemplate = restTemplate;
        this.userService = userService;
    }

    // 작물 진단 API (FastAPI AI 마이크로서비스 연동)
    @PostMapping("/plant") // POST /api/diagnose/plant 요청 처리
    public ResponseEntity<?> diagnosePlant(@RequestBody Map<String, String> requestPayload) {
        // 프론트엔드에서 JSON으로 전송한 데이터 추출
        String base64Image = requestPayload.get("image");
        String mimeType = requestPayload.get("mimeType");
        String prompt = requestPayload.get("prompt");
        String userIdStr = requestPayload.get("userId"); // 프론트에서 받은 userId (문자열)

        // 필수 파라미터 유효성 검사
        if (base64Image == null || mimeType == null || prompt == null || userIdStr == null) {
            return new ResponseEntity<>(Map.of("message", "필수 요청 파라미터가 누락되었습니다 (image, mimeType, prompt, userId)."), HttpStatus.BAD_REQUEST);
        }
        if (!mimeType.startsWith("image/")) {
            return new ResponseEntity<>(Map.of("message", "이미지 MIME 타입이 유효하지 않습니다."), HttpStatus.BAD_REQUEST);
        }

        Long userId = null;
        try {
            userId = Long.parseLong(userIdStr);
        } catch (NumberFormatException e) {
            return new ResponseEntity<>(Map.of("message", "유효하지 않은 사용자 ID 형식입니다."), HttpStatus.BAD_REQUEST);
        }

        // 보안 검사: 요청된 userId와 현재 로그인된 userId가 일치하는지 확인
        Long authenticatedUserId = null;
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

        if (authentication != null && authentication.isAuthenticated() && !"anonymousUser".equals(authentication.getPrincipal())) {
            Object principal = authentication.getPrincipal();
            if (principal instanceof CustomUser) { // 커스텀 UserDetails 구현체를 사용하는 경우
                authenticatedUserId = ((CustomUser) principal).getUserId();
            } else if (principal instanceof OAuth2User) { // OAuth2 로그인 사용자 (카카오 등)
                String oauth2Id = ((OAuth2User) principal).getName();
                Optional<User> userOptional = userService.findByUsername(oauth2Id); // DB에서 실제 사용자 ID 조회
                if (userOptional.isPresent()) {
                    authenticatedUserId = userOptional.get().getUserId();
                }
            } else if (principal instanceof UserDetails) { // 일반 UserDetails 사용자
                String username = ((UserDetails) principal).getUsername();
                Optional<User> userOptional = userService.findByUsername(username); // DB에서 실제 사용자 ID 조회
                if (userOptional.isPresent()) {
                    authenticatedUserId = userOptional.get().getUserId();
                }
            }
        }

        if (authenticatedUserId == null || !authenticatedUserId.equals(userId)) {
            return new ResponseEntity<>(Map.of("message", "접근 권한이 없거나 사용자 정보가 일치하지 않습니다."), HttpStatus.FORBIDDEN);
        }

        try {
            // FastAPI 백엔드의 이미지 진단 엔드포인트 URL
            String pythonAiServiceUrl = "http://localhost:8000/diagnose/plant"; // FastAPI의 새로운 엔드포인트

            // FastAPI로 전송할 JSON 요청 본문
            Map<String, Object> pythonRequestBody = new HashMap<>();
            pythonRequestBody.put("image_base64", base64Image);
            pythonRequestBody.put("mime_type", mimeType);
            pythonRequestBody.put("prompt", prompt);
            pythonRequestBody.put("user_id", userId); // FastAPI로 userId 전달

            System.out.println("DEBUG: Sending diagnosis request to Python for user_id: " + userId + ", prompt: " + prompt.substring(0, Math.min(prompt.length(), 50)) + "...");

            // RestTemplate을 사용하여 FastAPI로 POST 요청 전송
            ResponseEntity<Map> pythonResponse = restTemplate.postForEntity(pythonAiServiceUrl, pythonRequestBody, Map.class);

            if (pythonResponse.getStatusCode().is2xxSuccessful() && pythonResponse.getBody() != null) {
                // FastAPI에서 받은 응답을 그대로 프론트엔드로 전달
                return new ResponseEntity<>(pythonResponse.getBody(), HttpStatus.OK);
            } else {
                // FastAPI 서버에서 오류 발생 시
                String errorMessage = "AI 진단 서버 오류: " + pythonResponse.getStatusCode();
                if (pythonResponse.getBody() != null && pythonResponse.getBody().containsKey("detail")) {
                    errorMessage += " - " + pythonResponse.getBody().get("detail");
                }
                return new ResponseEntity<>(Map.of("message", errorMessage), HttpStatus.BAD_GATEWAY);
            }
        } catch (Exception e) {
            e.printStackTrace();
            return new ResponseEntity<>(Map.of("message", "이미지 진단 통신 중 오류가 발생했습니다: " + e.getMessage()), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
}
