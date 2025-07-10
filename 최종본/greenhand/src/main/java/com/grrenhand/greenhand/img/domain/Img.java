// src/main/java/com/grrenhand/greenhand/img/domain/Img.java

package com.grrenhand.greenhand.img.domain; // 패키지명: img.domain

import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "img_logs") // DB 테이블명: img_logs (로그 기록의 의미)
@Getter
@Setter
@NoArgsConstructor
@Builder
public class Img { // 클래스명: Img

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId; // 사용자 ID

    @Column(name = "image_url") // 서버에 저장된 이미지 파일의 상대 URL 경로
    private String imageUrl;

    @Column(name = "diagnosis_result", nullable = false, columnDefinition = "TEXT")
    private String diagnosisResult; // AI 진단 결과 요약 (예: "정상", "병충해 발견")

    @Column(name = "diagnosis_details", columnDefinition = "TEXT")
    private String diagnosisDetails; // 상세 진단 내용 (병명, 원인, 해결책 등)

    @Column(name = "diagnosed_at", nullable = false)
    private LocalDateTime diagnosedAt; // 진단 요청 시간

    @Column(name = "severity", length = 50)
    private String severity; // 심각도 (예: "경미", "보통", "심각")

    @Column(name = "plant_name", length = 100)
    private String plantName; // 진단된 작물 이름 (AI가 반환하는 경우)

    // Lombok @Builder 사용 시 이 생성자는 자동으로 생성되지만, 명시적으로 포함 가능
    public Img(Long id, Long userId, String imageUrl, String diagnosisResult,
               String diagnosisDetails, LocalDateTime diagnosedAt, String severity, String plantName) {
        this.id = id;
        this.userId = userId;
        this.imageUrl = imageUrl;
        this.diagnosisResult = diagnosisResult;
        this.diagnosisDetails = diagnosisDetails;
        this.diagnosedAt = diagnosedAt;
        this.severity = severity;
        this.plantName = plantName;
    }

    @PrePersist
    protected void onCreate() {
        if (diagnosedAt == null) {
            diagnosedAt = LocalDateTime.now(); // 진단 시간 자동 설정
        }
    }
}
