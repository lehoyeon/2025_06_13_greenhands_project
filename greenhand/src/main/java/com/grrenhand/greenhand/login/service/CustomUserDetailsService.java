// src/main/java/com/grrenhand/greenhand/login/service/CustomUserDetailsService.java

package com.grrenhand.greenhand.login.service; // 패키지 확인

import com.grrenhand.greenhand.login.domain.User; // User 엔티티 경로 확인
import com.grrenhand.greenhand.login.repository.UserRepository; // UserRepository 경로 확인
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.security.core.authority.SimpleGrantedAuthority; // 권한 부여를 위해 임포트
import java.util.Collections; // Collections.singletonList()를 위해 임포트
import java.util.Optional; // Optional을 사용하기 위해 임포트

@Service // 스프링 빈으로 등록하여 Spring Security가 자동으로 찾도록 함
public class CustomUserDetailsService implements UserDetailsService {

    private final UserRepository userRepository;

    public CustomUserDetailsService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @Override
    // 사용자가 로그인 시도 시 Spring Security가 이 메서드를 호출하여 사용자 정보를 로드합니다.
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        // 데이터베이스에서 사용자 이름으로 사용자 정보 조회
        Optional<User> optionalUser = userRepository.findByUsername(username);

        // 사용자가 존재하지 않으면 예외 발생
        User user = optionalUser.orElseThrow(() -> new UsernameNotFoundException("사용자를 찾을 수 없습니다: " + username));

        // 조회된 사용자 정보를 Spring Security의 UserDetails 객체로 변환하여 반환
        // Spring Security의 User 객체는 username, password, authorities(권한)를 필수로 가집니다.
        // 여기서는 모든 사용자에게 "ROLE_USER" 권한을 부여합니다.
        // 실제 애플리케이션에서는 DB에 권한 테이블을 만들고 가져와서 부여해야 합니다.
        return new org.springframework.security.core.userdetails.User(
                user.getUsername(),         // 사용자의 아이디
                user.getPasswordHash(),     // DB에 저장된 암호화된 비밀번호 (Spring Security가 입력 비밀번호와 비교)
                Collections.singletonList(new SimpleGrantedAuthority("ROLE_USER")) // 사용자 권한
                // List.of(new SimpleGrantedAuthority("ROLE_USER")) // Java 9+ 사용 시
        );
    }
}