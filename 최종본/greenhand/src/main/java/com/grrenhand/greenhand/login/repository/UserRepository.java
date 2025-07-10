package com.grrenhand.greenhand.login.repository;

import com.grrenhand.greenhand.login.domain.User;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByUsername(String username);
    boolean existsByUsername(String username);
    boolean existsByEmail(String email);
    boolean existsByNickname(String nickname); // 닉네임 중복 검사용 추가

    // 이메일과 전화번호로 사용자 찾기 (아이디 찾기용)
    Optional<User> findByEmailAndPhoneNumber(String email, String phoneNumber);

    // 아이디와 전화번호로 사용자 찾기 (비밀번호 찾기용)
    Optional<User> findByUsernameAndPhoneNumber(String username, String phoneNumber);
}