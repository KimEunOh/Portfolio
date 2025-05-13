package kr.ntoday.adminsystem.domain.system;

import lombok.Builder;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.util.Objects;

@NoArgsConstructor
@EqualsAndHashCode
public class DeptPosRelKey implements Serializable {
    private Long userPid;
    private String deptCode;

    @Builder
    public DeptPosRelKey(Long userPid, String deptCode) {
        this.userPid = userPid;
        this.deptCode = deptCode;
    }
}