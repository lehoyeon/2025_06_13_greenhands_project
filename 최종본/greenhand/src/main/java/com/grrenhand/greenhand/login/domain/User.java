// src/main/java/com/grrenhand/greenhand/login/domain/User.java

package com.grrenhand.greenhand.login.domain;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import jakarta.persistence.*;
import java.sql.Timestamp;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "users")
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "user_id")
    private Long userId;

    @Column(name = "username", nullable = false, unique = true, length = 50)
    private String username;

    // 중요: nullable = false를 제거하여 null을 허용하도록 변경했습니다.
    // 이는 소셜 로그인 사용자의 경우 password_hash가 없을 수 있기 때문입니다.
    @Column(name = "password_hash", length = 64)
    private String passwordHash;

    @Column(name = "nickname", length = 50)
    private String nickname;

    @Column(name = "name", length = 50)
    private String name;

    @Column(name = "email", unique = true, length = 100)
    private String email;

    @Column(name = "address", length = 255)
    private String address;

    @Column(name = "phone_number", length = 20)
    private String phoneNumber;

    @Column(name = "created_at", nullable = false)
    private Timestamp createdAt;

    @Column(name = "last_login_at")
    private Timestamp lastLoginAt;

    @PrePersist
    protected void onCreate() {
        createdAt = new Timestamp(System.currentTimeMillis());
    }
}