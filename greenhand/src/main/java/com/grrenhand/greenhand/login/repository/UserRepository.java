// src/main/java/com/grrenhand/greenhand/login/repository/UserRepository.java
package com.grrenhand.greenhand.login.repository;

import com.grrenhand.greenhand.login.domain.User;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByUsername(String username);
    boolean existsByUsername(String username);
    boolean existsByEmail(String email);

    // 추가: 이메일로 회원 조회
    Optional<User> findByEmail(String email);
}
