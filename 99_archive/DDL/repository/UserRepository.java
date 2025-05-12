package kr.ntoday.adminsystem.repository.system;

import kr.ntoday.adminsystem.domain.system.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {
}