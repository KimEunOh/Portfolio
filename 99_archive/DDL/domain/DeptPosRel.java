package kr.ntoday.adminsystem.domain.system;

import jakarta.persistence.*;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDate;

@Getter
@NoArgsConstructor
@Entity
@Table(name = "tbl_dept_pos_rel")
@IdClass(DeptPosRelKey.class)
public class DeptPosRel {
    @Id
    @Column(name = "user_pid")
    private Long userPid;

    @Id
    @Column(name = "dept_code")
    private String deptCode;

    @Column(name = "pst_code")
    private String pstCode;

    @Column(name = "gnfd_ymd")
    private LocalDate gnfdYmd;

    @Column(name = "prrk")
    private Integer prrk;

    @Builder
    public DeptPosRel(Long userPid, String deptCode, String pstCode, LocalDate gnfdYmd, Integer prrk) {
        this.userPid = userPid;
        this.deptCode = deptCode;
        this.pstCode = pstCode;
        this.gnfdYmd = gnfdYmd;
        this.prrk = prrk;
    }
}