// src/main/java/com/grrenhand/greenhand/img/repository/ImgRepository.java

package com.grrenhand.greenhand.img.repository; // 패키지명: img.repository

import com.grrenhand.greenhand.img.domain.Img; // 엔티티 클래스 임포트 변경
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ImgRepository extends JpaRepository<Img, Long> { // 레포지토리 인터페이스명: ImgRepository
    // 특정 사용자의 진단 내역을 최신순으로 가져오는 쿼리 메서드
    List<Img> findByUserIdOrderByDiagnosedAtDesc(Long userId);
}
