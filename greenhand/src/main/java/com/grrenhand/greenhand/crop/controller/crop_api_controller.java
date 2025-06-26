package com.grrenhand.greenhand.crop.controller;

import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@RestController
@RequestMapping("/api/crops")
public class crop_api_controller {

    private final RestTemplate restTemplate = new RestTemplate();

    @PostMapping("/recommend")
    public ResponseEntity<?> recommendCrops(@RequestBody Map<String, String> options) {
        String flaskApiUrl = "http://localhost:5000/api/recommend-crop"; // Flask API 주소

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        HttpEntity<Map<String, String>> request = new HttpEntity<>(options, headers);

        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(flaskApiUrl, request, Map.class);

            if (response.getStatusCode() == HttpStatus.OK) {
                return ResponseEntity.ok(response.getBody());
            } else {
                return ResponseEntity.status(response.getStatusCode()).body("Flask API 에러 발생");
            }

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("연동 실패: " + e.getMessage());
        }
    }
}
