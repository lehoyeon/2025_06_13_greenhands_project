package com.grrenhand.greenhand.crop_recommend.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

@Entity
@Getter
@Setter
@Table(name = "crops")
public class Crop {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;            // 작물명
    private String nickname;        // 사용자 작물 별명
    private String userId;          // 사용자 ID
    private String region;          // 지역
    private String difficulty;      // 재배 난이도
    private String description;     // 작물 설명
    private String registeredAt;    // 등록 시각
}
