// src/main/java/com/grrenhand/greenhand/img/controller/ImgController.java

package com.grrenhand.greenhand.img.controller; // 패키지명: img.controller

import com.grrenhand.greenhand.img.domain.Img; // 엔티티 임포트 변경
import com.grrenhand.greenhand.img.service.ImgService; // 서비스 임포트 변경
import com.grrenhand.greenhand.img.service.FileStorageService; // 파일 저장 서비스 임포트
import com.grrenhand.greenhand.login.config.CustomUser;
import com.grrenhand.greenhand.login.domain.User;
import com.grrenhand.greenhand.login.service.UserService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException; // IOException 임포트 추가
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/diagnose") // URL: /api/diagnose로 시작 (기존과 동일)
public class ImgController { // 컨트롤러 이름: ImgController (기존과 동일)

    private final RestTemplate restTemplate;
    private final UserService userService;
    private final ImgService imgService; // ImgService 주입
    private final FileStorageService fileStorageService; // FileStorageService 주입

    public ImgController(RestTemplate restTemplate, UserService userService,
                         ImgService imgService, FileStorageService fileStorageService) {
        this.restTemplate = restTemplate;
        this.userService = userService;
        this.imgService = imgService;
        this.fileStorageService = fileStorageService;
    }

    /**
     * 작물 진단 요청 (AI 마이크로서비스 연동) 및 진단 결과 DB 저장
     * POST /api/diagnose/plant
     *
     * @param imageFile 진단할 이미지 파일 (프론트엔드에서 FormData로 전송)
     * @param prompt    AI 진단에 사용될 프롬프트/쿼리 텍스트
     * @param userIdStr 프론트엔드에서 전송한 사용자 ID (인증 확인용)
     * @return AI 진단 결과 및 DB 저장 성공 여부 (AI 응답 JSON에 저장된 이미지 URL 포함)
     */
    @PostMapping("/plant")
    public ResponseEntity<?> diagnosePlantAndSave(
            @RequestParam("imageFile") MultipartFile imageFile,
            @RequestParam("prompt") String prompt,
            @RequestParam("userId") String userIdStr
    ) {
        // 1. 사용자 ID 파싱 및 유효성 검사
        Long userId;
        try {
            userId = Long.parseLong(userIdStr);
        } catch (NumberFormatException e) {
            return new ResponseEntity<>(Map.of("message", "유효하지 않은 사용자 ID 형식입니다."), HttpStatus.BAD_REQUEST);
        }

        if (imageFile.isEmpty()) {
            return new ResponseEntity<>(Map.of("message", "이미지 파일이 비어 있습니다."), HttpStatus.BAD_REQUEST);
        }
        if (!imageFile.getContentType().startsWith("image/")) {
            return new ResponseEntity<>(Map.of("message", "파일이 이미지 형식이 아닙니다."), HttpStatus.BAD_REQUEST);
        }

        // 2. 보안 검사: 요청된 userId와 현재 로그인된 userId가 일치하는지 확인
        Long authenticatedUserId = getAuthenticatedUserId(); // 별도 헬퍼 함수로 추출
        if (authenticatedUserId == null || !authenticatedUserId.equals(userId)) {
            return new ResponseEntity<>(Map.of("message", "접근 권한이 없거나 사용자 정보가 일치하지 않습니다."), HttpStatus.FORBIDDEN);
        }

        String storedImageUrl = null; // 서버에 저장된 이미지 URL (DB에 저장될 경로)
        Map<String, Object> aiResponseMap = null; // AI 서비스로부터 받은 응답

        try {
            // 3. 이미지 파일 서버에 저장 (실제 파일 경로 얻기)
            // 'img-diagnoses'는 uploads 디렉토리 내의 서브디렉토리 이름입니다.
            // 필요에 따라 이 이름을 다른 것으로 변경할 수 있습니다 (예: 'img-logs').
            storedImageUrl = fileStorageService.storeFile(imageFile, "img-diagnoses");

            // 4. 저장된 이미지 URL을 포함하여 AI 서비스로 전송할 데이터 준비
            // Spring이 Base64로 인코딩하여 FastAPI로 전송하는 기존 방식을 유지합니다.
            String base64Image = java.util.Base64.getEncoder().encodeToString(imageFile.getBytes());
            String mimeType = imageFile.getContentType();

            String pythonAiServiceUrl = "http://localhost:8000/diagnose/plant"; // FastAPI 엔드포인트 (기존과 동일)

            Map<String, Object> pythonRequestBody = new HashMap<>();
            pythonRequestBody.put("image_base64", base64Image);
            pythonRequestBody.put("mime_type", mimeType);
            pythonRequestBody.put("prompt", prompt);
            pythonRequestBody.put("user_id", userId);

            System.out.println("DEBUG: Sending diagnosis request to Python for user_id: " + userId + ", prompt: " + prompt.substring(0, Math.min(prompt.length(), 50)) + "...");

            // 5. RestTemplate을 사용하여 FastAPI로 POST 요청 전송
            ResponseEntity<Map> pythonResponse = restTemplate.postForEntity(pythonAiServiceUrl, pythonRequestBody, Map.class);

            if (pythonResponse.getStatusCode().is2xxSuccessful() && pythonResponse.getBody() != null) {
                aiResponseMap = pythonResponse.getBody();

                // 6. AI 진단 결과와 저장된 이미지 URL을 DB에 저장
                String diagnosisResult = (String) aiResponseMap.getOrDefault("diagnosis_result", "정보 없음");
                String diagnosisDetails = (String) aiResponseMap.get("diagnosis_details");
                String severity = (String) aiResponseMap.get("severity");
                String plantName = (String) aiResponseMap.get("plant_name");

                // FastAPI가 이미지 처리 후 반환하는 이미지 URL (FastAPI가 새로운 URL을 반환했다면 그 값을 사용)
                // 만약 FastAPI가 저장하지 않고 단순히 결과만 준다면, Spring이 저장한 storedImageUrl을 사용
                String finalImageUrlForDb = storedImageUrl; // 기본적으로 Spring이 저장한 URL 사용
                if (aiResponseMap.containsKey("image_url") && aiResponseMap.get("image_url") != null) {
                    // FastAPI가 자체적으로 이미지를 저장하고 새로운 URL을 반환했다면 그것을 사용
                    // (이 경우 FastAPI가 반환하는 URL도 /uploads/ 형태로 Spring이 제공하는 정적 리소스 경로와 일치해야 함)
                    finalImageUrlForDb = (String) aiResponseMap.get("image_url");
                }


                Img imgLog = Img.builder() // Img 엔티티 사용
                        .userId(userId)
                        .imageUrl(finalImageUrlForDb) // DB에는 Spring이 저장한 URL 또는 FastAPI가 반환한 URL
                        .diagnosisResult(diagnosisResult)
                        .diagnosisDetails(diagnosisDetails)
                        .severity(severity)
                        .plantName(plantName)
                        .diagnosedAt(LocalDateTime.now()) // 현재 시간으로 설정
                        .build();

                imgService.saveImgLog(imgLog); // ImgService의 saveImgLog 메서드 사용
                System.out.println("DEBUG: 진단 결과가 DB에 성공적으로 저장되었습니다. userId: " + userId);

                // FastAPI에서 받은 응답에 저장된 이미지 URL (Spring이 저장한 URL)을 추가하여 프론트엔드로 전달
                // 이 URL은 클라이언트가 이미지를 표시할 때 사용합니다.
                aiResponseMap.put("image_url", finalImageUrlForDb); // 프론트엔드가 이미지 표시할 때 사용할 URL
                return new ResponseEntity<>(aiResponseMap, HttpStatus.OK);

            } else {
                // FastAPI 서버에서 오류 발생 시
                String errorMessage = "AI 진단 서버 오류: " + pythonResponse.getStatusCode();
                if (pythonResponse.getBody() != null && pythonResponse.getBody().containsKey("detail")) {
                    errorMessage += " - " + pythonResponse.getBody().get("detail");
                }
                // AI 진단 실패 시, Spring이 저장한 이미지는 삭제하는 것이 좋습니다.
                if (storedImageUrl != null) {
                    fileStorageService.deleteFile(storedImageUrl);
                }
                return new ResponseEntity<>(Map.of("message", errorMessage), HttpStatus.BAD_GATEWAY);
            }
        } catch (IOException e) { // MultipartFile.getBytes()에서 발생 가능
            e.printStackTrace();
            return new ResponseEntity<>(Map.of("message", "이미지 파일 처리 중 오류가 발생했습니다: " + e.getMessage()), HttpStatus.INTERNAL_SERVER_ERROR);
        }
        catch (Exception e) {
            e.printStackTrace();
            // 오류 발생 시, Spring이 저장한 이미지는 삭제하는 것이 좋습니다.
            if (storedImageUrl != null) {
                try {
                    fileStorageService.deleteFile(storedImageUrl);
                } catch (IOException ioException) {
                    System.err.println("오류 발생 시 이미지 삭제 실패: " + ioException.getMessage());
                }
            }
            return new ResponseEntity<>(Map.of("message", "이미지 진단 통신 중 오류가 발생했습니다: " + e.getMessage()), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    /**
     * 특정 사용자의 이미지 진단 내역을 조회하는 엔드포인트
     * GET /api/diagnose/history/{userId}
     *
     * @param userId 사용자 ID
     * @return 해당 사용자의 이미지 진단 내역 리스트
     */
    @GetMapping("/history/{userId}")
    public ResponseEntity<List<Img>> getImgHistory(@PathVariable Long userId) { // 메서드명: getImgHistory
        // 보안 검사: 요청된 userId와 현재 로그인된 userId가 일치하는지 확인
        Long authenticatedUserId = getAuthenticatedUserId();
        if (authenticatedUserId == null || !authenticatedUserId.equals(userId)) {
            return new ResponseEntity<>(HttpStatus.FORBIDDEN);
        }

        try {
            List<Img> history = imgService.getImgHistoryByUserId(userId); // ImgService의 getImgHistoryByUserId 사용
            return ResponseEntity.ok(history);
        } catch (Exception e) {
            System.err.println("진단 내역 조회 중 오류 발생: " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * 현재 인증된 사용자의 userId를 가져오는 헬퍼 메서드
     * @return 인증된 사용자의 userId 또는 null
     */
    private Long getAuthenticatedUserId() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

        if (authentication != null && authentication.isAuthenticated() && !"anonymousUser".equals(authentication.getPrincipal())) {
            Object principal = authentication.getPrincipal();
            if (principal instanceof CustomUser) {
                return ((CustomUser) principal).getUserId();
            } else if (principal instanceof OAuth2User) {
                String oauth2Id = ((OAuth2User) principal).getName();
                Optional<User> userOptional = userService.findByUsername(oauth2Id);
                return userOptional.map(User::getUserId).orElse(null);
            } else if (principal instanceof UserDetails) {
                String username = ((UserDetails) principal).getUsername();
                Optional<User> userOptional = userService.findByUsername(username);
                return userOptional.map(User::getUserId).orElse(null);
            }
        }
        return null;
    }
}
