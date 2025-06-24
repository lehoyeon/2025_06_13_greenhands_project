// src/main/java/com/grrenhand/greenhand/img/controller/ImgController.java

package com.grrenhand.greenhand.img.controller; // 정확히 'main'이 없는 패키지명 (grrenhand 오타 유지)

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;

import java.util.Map;

@RestController
@RequestMapping("/api/main") // `img.html`에서 '/api/main/diagnose'로 호출하므로 이 RequestMapping 유지
public class ImgController {

    private final RestTemplate restTemplate;

    public ImgController(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    // 작물 진단 API (Python AI 마이크로서비스 연동)
    @PostMapping("/diagnose") // POST /api/main/diagnose 요청 처리
    public ResponseEntity<?> diagnosePlant(@RequestPart("file") MultipartFile file) {
        if (file.isEmpty()) {
            return new ResponseEntity<>(Map.of("message", "이미지 파일이 비어있습니다."), HttpStatus.BAD_REQUEST);
        }
        if (!file.getContentType().startsWith("image/")) {
            return new ResponseEntity<>(Map.of("message", "이미지 파일만 업로드할 수 있습니다."), HttpStatus.BAD_REQUEST);
        }

        try {
            String pythonAiServiceUrl = "http://localhost:5000/predict";

            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("file", file.getResource());

            HttpHeaders headers = new HttpHeaders();
            HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

            ResponseEntity<Map> pythonResponse = restTemplate.postForEntity(pythonAiServiceUrl, requestEntity, Map.class);

            if (pythonResponse.getStatusCode().is2xxSuccessful() && pythonResponse.getBody() != null) {
                return new ResponseEntity<>(pythonResponse.getBody(), HttpStatus.OK);
            } else {
                return new ResponseEntity<>(Map.of("message", "AI 진단 서버 오류: " + pythonResponse.getStatusCode() + " " + pythonResponse.getBody()), HttpStatus.BAD_GATEWAY);
            }
        } catch (Exception e) {
            e.printStackTrace();
            return new ResponseEntity<>(Map.of("message", "이미지 진단 중 오류가 발생했습니다."), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
}