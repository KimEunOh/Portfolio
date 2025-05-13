package kr.ntoday.adminsystem.repository.system;

import kr.ntoday.adminsystem.domain.system.DeptPosRel;
import kr.ntoday.adminsystem.domain.system.DeptPosRelKey;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface DeptPosRelRepository extends JpaRepository<DeptPosRel, DeptPosRelKey> {
}