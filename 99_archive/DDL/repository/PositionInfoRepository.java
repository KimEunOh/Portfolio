package kr.ntoday.adminsystem.repository.system;

import kr.ntoday.adminsystem.domain.system.PositionInfo;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface PositionInfoRepository extends JpaRepository<PositionInfo, String> {
}