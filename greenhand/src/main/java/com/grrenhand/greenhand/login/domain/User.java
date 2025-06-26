// src/main/java/com/grrenhand/greenhand/login/domain/User.java

package com.grrenhand.greenhand.login.domain; // 패키지 확인

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import jakarta.persistence.*; // JPA 관련 어노테이션 임포트
import java.sql.Timestamp; // 또는 java.time.LocalDateTime (선호하는 방식 선택)

@Data // Lombok: getter, setter, equals, hashCode, toString 자동 생성
@NoArgsConstructor // Lombok: 기본 생성자 자동 생성
@AllArgsConstructor // Lombok: 모든 필드를 인자로 받는 생성자 자동 생성
@Entity // JPA 엔티티임을 명시
@Table(name = "users") // 매핑할 DB 테이블 이름
public class User {

    @Id // Primary Key
    @GeneratedValue(strategy = GenerationType.IDENTITY) // Auto Increment (MariaDB/MySQL)
    @Column(name = "user_id") // DB 컬럼명 매핑
    private Long userId;

    @Column(name = "username", nullable = false, unique = true, length = 50)
    private String username;

    // 중요: BCryptPasswordEncoder는 결과 문자열이 60자입니다.
    // DB의 char(64)는 안전하지만, 일반적으로 varchar(255)를 사용하여 유연성을 높입니다.
    // 현재 char(64)면 일단 작동은 합니다.
    @Column(name = "password_hash", nullable = false, length = 64)
    private String passwordHash;

    @Column(name = "nickname", length = 50)
    private String nickname;

    @Column(name = "name", length = 50)
    private String name;

    @Column(name = "email", unique = true, length = 100)
    private String email;

    @Column(name = "address", length = 255)
    private String address;

    @Column(name = "phone_number", length = 20) // <-- DB 컬럼명 'phone_number'와 정확히 일치!
    private String phoneNumber; // <-- Java 컨벤션에 맞게 'phoneNumber'로 변경!

    @Column(name = "created_at", nullable = false)
    private Timestamp createdAt; // DB의 timestamp 타입과 매핑

    @Column(name = "last_login_at")
    private Timestamp lastLoginAt; // DB의 timestamp 타입과 매핑

    // 엔티티가 영속화(저장)되기 전에 호출되는 콜백 메서드
    @PrePersist
    protected void onCreate() {
        createdAt = new Timestamp(System.currentTimeMillis()); // 현재 시간으로 생성 시간 설정
    }

    // 엔티티가 업데이트되기 전에 호출되는 콜백 메서드 (필요 시)
    // @PreUpdate
    // protected void onUpdate() {
    //     // lastLoginAt = new Timestamp(System.currentTimeMillis()); // 로그인 시점에 업데이트 등
    // }
}