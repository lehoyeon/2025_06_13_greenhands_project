package com.grrenhand.greenhand.crop.controller;

import org.springframework.http.*;
import org.springframework.stereotype.Controller; // @Controller로 변경
import org.springframework.web.bind.annotation.*; // RestController 대신 Controller 사용
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;
import java.util.HashMap;

@Controller // 이 컨트롤러는 뷰(HTML)를 반환할 수 있습니다.
@RequestMapping("/") // 기본 경로 설정 (예: /crop으로 직접 접근)
public class CropController {

    private final RestTemplate restTemplate = new RestTemplate();
    // FastAPI API의 기본 URL (이전 Flask API에서 FastAPI로 변경됨)
    private final String FASTAPI_API_BASE_URL = "http://localhost:8000";
    // user_id는 세션이나 인증 시스템에서 받아와야 하지만, 현재 예시에서는 임시로 하드코딩
    private final int TEMP_USER_ID = 1;

    // crop.html 페이지를 제공하는 메서드
    @GetMapping("/crop")
    public String cropPage() {
        return "crop.html"; // templates/crop.html 파일을 렌더링합니다.
    }

    // 1. 작물 추천 API 엔드포인트 (POST /api/crops/recommend-crop)
    @PostMapping("/api/crops/recommend-crop")
    @ResponseBody // 이 메서드는 JSON 데이터를 응답 본문으로 반환합니다.
    public ResponseEntity<?> recommendCrops(@RequestBody Map<String, String> options) {
        // FastAPI의 작물 추천 엔드포인트
        String fastapiApiUrl = FASTAPI_API_BASE_URL + "/api/crops/recommend-crop";

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        // 프론트엔드에서 받은 environment, duration, region을 FastAPI로 전달
        Map<String, String> requestBody = new HashMap<>();
        // requestBody.put("harvest", options.get("harvest")); // harvest는 이제 FastAPI에서 사용되지 않음 (프롬프트에서만 사용하거나 제거)
        requestBody.put("environment", options.get("environment"));
        requestBody.put("duration", options.get("duration"));
        requestBody.put("region", options.get("region"));

        HttpEntity<Map<String, String>> request = new HttpEntity<>(requestBody, headers);

        try {
            // FastAPI API 호출 (응답은 작물 객체의 배열 형태)
            ResponseEntity<List> response = restTemplate.postForEntity(fastapiApiUrl, request, List.class);

            if (response.getStatusCode() == HttpStatus.OK) {
                // FastAPI에서 받은 응답을 클라이언트에 그대로 전달
                return ResponseEntity.ok(response.getBody());
            } else {
                // FastAPI에서 오류 응답을 받은 경우
                return ResponseEntity.status(response.getStatusCode()).body("FastAPI 에러 발생: " + response.getBody());
            }

        } catch (Exception e) {
            System.err.println("FastAPI 연동 실패 (recommend-crop): " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("백엔드 연동 실패: " + e.getMessage());
        }
    }

    // 2. 작물 상세 가이드 API 엔드포인트 (POST /api/crops/crop-guide)
    @PostMapping("/api/crops/crop-guide")
    @ResponseBody
    public ResponseEntity<?> getCropGuide(@RequestBody Map<String, String> requestPayload) {
        String fastapiApiUrl = FASTAPI_API_BASE_URL + "/api/crops/crop-guide";
        String cropId = requestPayload.get("crop_id"); // crop_id로 요청

        if (cropId == null || cropId.isEmpty()) {
            return ResponseEntity.badRequest().body("crop_id가 필요합니다.");
        }

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        Map<String, String> requestBody = new HashMap<>();
        requestBody.put("crop_id", cropId);

        HttpEntity<Map<String, String>> request = new HttpEntity<>(requestBody, headers);

        try {
            // FastAPI API 호출
            ResponseEntity<Map> response = restTemplate.postForEntity(fastapiApiUrl, request, Map.class);

            if (response.getStatusCode() == HttpStatus.OK) {
                return ResponseEntity.ok(response.getBody());
            } else {
                return ResponseEntity.status(response.getStatusCode()).body("FastAPI 에러 발생: " + response.getBody());
            }
        } catch (Exception e) {
            System.err.println("FastAPI 연동 실패 (crop-guide): " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("백엔드 연동 실패: " + e.getMessage());
        }
    }

    // 3. 사용자 작물 재배 리스트에 추가 API 엔드포인트 (POST /api/crops/user-crops/add)
    @PostMapping("/api/crops/user-crops/add")
    @ResponseBody
    public ResponseEntity<?> addUserCrop(@RequestBody Map<String, Object> requestPayload) {
        String fastapiApiUrl = FASTAPI_API_BASE_URL + "/api/crops/user-crops/add";

        // user_id는 현재 임시로 설정
        requestPayload.put("user_id", TEMP_USER_ID);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestPayload, headers);

        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(fastapiApiUrl, request, Map.class);
            if (response.getStatusCode() == HttpStatus.OK) {
                return ResponseEntity.ok(response.getBody());
            } else {
                return ResponseEntity.status(response.getStatusCode()).body("FastAPI 에러 발생: " + response.getBody());
            }
        } catch (Exception e) {
            System.err.println("FastAPI 연동 실패 (add user crop): " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("백엔드 연동 실패: " + e.getMessage());
        }
    }

    // 4. 사용자 작물 재배 리스트 조회 API 엔드포인트 (GET /api/crops/user-crops/{user_id})
    @GetMapping("/api/crops/user-crops/{userId}")
    @ResponseBody
    public ResponseEntity<?> getUserCrops(@PathVariable("userId") int userId) {
        // FastAPI의 사용자 작물 조회 엔드포인트
        String fastapiApiUrl = FASTAPI_API_BASE_URL + "/api/crops/user-crops/" + userId;

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Void> request = new HttpEntity<>(headers); // GET 요청이라 body 없음

        try {
            ResponseEntity<List> response = restTemplate.exchange(fastapiApiUrl, HttpMethod.GET, request, List.class);
            if (response.getStatusCode() == HttpStatus.OK) {
                return ResponseEntity.ok(response.getBody());
            } else {
                return ResponseEntity.status(response.getStatusCode()).body("FastAPI 에러 발생: " + response.getBody());
            }
        } catch (Exception e) {
            System.err.println("FastAPI 연동 실패 (get user crops): " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("백엔드 연동 실패: " + e.getMessage());
        }
    }

    // 5. 사용자 작물 재배 리스트에서 특정 작물 삭제 API 엔드포인트 (DELETE /api/crops/user-crops/{user_id}/{user_crop_id})
    @DeleteMapping("/api/crops/user-crops/{userId}/{userCropId}")
    @ResponseBody
    public ResponseEntity<?> deleteUserCrop(
            @PathVariable("userId") int userId,
            @PathVariable("userCropId") int userCropId) {

        String fastapiApiUrl = FASTAPI_API_BASE_URL + "/api/crops/user-crops/" + userId + "/" + userCropId;

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Void> request = new HttpEntity<>(headers); // DELETE 요청이라 body 없음

        try {
            ResponseEntity<Map> response = restTemplate.exchange(fastapiApiUrl, HttpMethod.DELETE, request, Map.class);
            if (response.getStatusCode() == HttpStatus.OK) {
                return ResponseEntity.ok(response.getBody());
            } else {
                return ResponseEntity.status(response.getStatusCode()).body("FastAPI 에러 발생: " + response.getBody());
            }
        } catch (Exception e) {
            System.err.println("FastAPI 연동 실패 (delete user crop): " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("백엔드 연동 실패: " + e.getMessage());
        }
    }

    // 6. 사용자 작물 재배 리스트 전체 삭제 API 엔드포인트 (DELETE /api/crops/user-crops/all/{user_id})
    @DeleteMapping("/api/crops/user-crops/all/{userId}")
    @ResponseBody
    public ResponseEntity<?> deleteAllUserCrops(@PathVariable("userId") int userId) {
        String fastapiApiUrl = FASTAPI_API_BASE_URL + "/api/crops/user-crops/all/" + userId;

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Void> request = new HttpEntity<>(headers); // DELETE 요청이라 body 없음

        try {
            ResponseEntity<Map> response = restTemplate.exchange(fastapiApiUrl, HttpMethod.DELETE, request, Map.class);
            if (response.getStatusCode() == HttpStatus.OK) {
                return ResponseEntity.ok(response.getBody());
            } else {
                return ResponseEntity.status(response.getStatusCode()).body("FastAPI 에러 발생: " + response.getBody());
            }
        } catch (Exception e) {
            System.err.println("FastAPI 연동 실패 (delete all user crops): " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("백엔드 연동 실패: " + e.getMessage());
        }
    }
}