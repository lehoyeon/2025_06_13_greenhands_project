// src/main/java/com/grrenhand/greenhand/img/service/ImgService.java

package com.grrenhand.greenhand.img.service; // 패키지명: img.service

import com.grrenhand.greenhand.img.domain.Img; // 엔티티 클래스 임포트 변경
import com.grrenhand.greenhand.img.repository.ImgRepository; // 레포지토리 임포트 변경
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ImgService { // 클래스명: ImgService

    private final ImgRepository imgRepository;

    @Autowired
    public ImgService(ImgRepository imgRepository) {
        this.imgRepository = imgRepository;
    }

    /**
     * 진단 기록을 DB에 저장합니다.
     * @param img 저장할 Img 엔티티
     * @return 저장된 Img 엔티티
     */
    public Img saveImgLog(Img img) { // 메서드명: saveImgLog
        return imgRepository.save(img);
    }

    /**
     * 특정 사용자의 진단 내역을 조회합니다.
     * @param userId 사용자 ID
     * @return 해당 사용자의 진단 내역 리스트 (최신순)
     */
    public List<Img> getImgHistoryByUserId(Long userId) { // 메서드명: getImgHistoryByUserId
        return imgRepository.findByUserIdOrderByDiagnosedAtDesc(userId);
    }
}
