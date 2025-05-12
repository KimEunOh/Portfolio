package kr.ntoday.adminsystem.domain.system;

import jakarta.persistence.*;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Getter
@NoArgsConstructor
@Entity
@Table(name = "tbl_department_info")
public class DepartmentInfo {
    @Id
    @Column(name = "dept_code")
    private String deptCode;

    @Column(name = "dept_nm")
    private String deptNm;

    @Column(name = "reg_ps_id")
    private String regPsId;

    @Column(name = "reg_dtm")
    private LocalDateTime regDtm;

    @Column(name = "upd_ps_id")
    private String updPsId;

    @Column(name = "upd_dtm")
    private LocalDateTime updDtm;

    @Column(name = "del_at")
    private String delAt;

    @Column(name = "prnt_dept_code")
    private String prntDeptCode;

    @Builder
    public DepartmentInfo(String deptCode, String deptNm, String regPsId, LocalDateTime regDtm,
                          String updPsId, LocalDateTime updDtm, String delAt, String prntDeptCode) {
        this.deptCode = deptCode;
        this.deptNm = deptNm;
        this.regPsId = regPsId;
        this.regDtm = regDtm;
        this.updPsId = updPsId;
        this.updDtm = updDtm;
        this.delAt = delAt;
        this.prntDeptCode = prntDeptCode;
    }
}