from pathlib import Path
import unicodedata
import json
import re
# TẦNG 0 : Dọn dẹp ( văn bản tự do CV)
def tien_xu_ly(s: str) -> str:
    # Hàm này chuẩn hóa văn bản: chữ thường, gom khoảng trắng/tab, bỏ dấu tiếng Việt
    s = s.lower()  # chữ thường
    s = s.replace("đ", "d")
    s = " ".join(s.split())  # gom khoảng trắng
    s = unicodedata.normalize("NFD", s)
    ket_qua = ""
    for c in s:
        if unicodedata.combining(c) == 0:
            ket_qua = ket_qua + c
    s = ket_qua
    return s

Skill_link = Path(__file__).parent / "data" / "ky_nang.json"

def doc_tu_dien_nguoc(link) -> dict[str, str]:
    with open(link, encoding="utf-8") as f:
        data = json.load(f)

    tu_dien_nguoc = {}
    for key, value in data.items():
        if key == "_ghi_chu":  # dòng ghi chú, không phải kỹ năng
            continue
        for alias in value:
            tu_dien_nguoc[tien_xu_ly(alias)] = key
    return tu_dien_nguoc

# TẦNG 1 :  Tra bảng , khớp các chuỗi
def khop_chinh_xac(s: str, tu_dien_nguoc: dict) -> str | None:
    return tu_dien_nguoc.get(tien_xu_ly(s))# nó chỉ tra bảng và trả lại kết quả có hoặc None

# TẦNG 2: Tìm biệt danh nằm lẫn trong câu
def mau_ranh_gioi(alias: str) -> str:
    return r"(?<![a-z0-9.])" + re.escape(alias) + r"(?![a-z])"


def co_ranh_gioi_tu(chuoi: str, alias: str) -> bool:
    return re.search(mau_ranh_gioi(alias), chuoi) is not None

def alias_theo_do_dai_giam(tu_dien_nguoc: dict[str, str]) -> list[str]:
    """Danh sach alias sap xep tu DAI nhat den NGAN nhat."""
    return sorted(tu_dien_nguoc, key=len, reverse=True)


def tim_alias_dai_nhat(
    s: str,
    tu_dien_nguoc: dict[str, str],
    danh_sach_alias: list[str] | None = None,) -> str | None:
    """Tang 2: alias DAI NHAT nam trong chuoi s -> ten chuan."""
    if danh_sach_alias is None:
        danh_sach_alias = alias_theo_do_dai_giam(tu_dien_nguoc)
    s_chuan = tien_xu_ly(s)
    for alias in danh_sach_alias:
        if co_ranh_gioi_tu(s_chuan, alias):
            return tu_dien_nguoc[alias]
    return None


def chuan_hoa(
    s: str,
    tu_dien_nguoc: dict[str, str],
    danh_sach_alias: list[str] | None = None,
) -> str | None:
    """Ham tong: tang 1 (khop chinh xac) -> tang 2 (alias dai nhat).

    Tang 3 (embedding) se bo sung sau.
    """
    ten = khop_chinh_xac(s, tu_dien_nguoc)
    if ten is not None:
        return ten
    return tim_alias_dai_nhat(s, tu_dien_nguoc, danh_sach_alias)


def trich_xuat_ky_nang(
    van_ban: str,
    tu_dien_nguoc: dict[str, str],
    danh_sach_alias: list[str] | None = None,) -> list[str]:
    # Quét cả đoạn văn bản, trả về TẤT CẢ kỹ năng tìm được (không trùng).
    # Quét từ alias dài đến ngắn; chỗ nào đã khớp thì "bôi đen" bằng khoảng trắng
    # để alias ngắn hơn không ăn lại miếng đó (vd 'javascript' khớp rồi thì
    # 'java' không được tính thêm).
    # danh_sach_alias: truyền sẵn để khỏi sort lại 93 alias cho MỖI tin.
    if danh_sach_alias is None:
        danh_sach_alias = alias_theo_do_dai_giam(tu_dien_nguoc)

    con_lai = tien_xu_ly(van_ban)
    tim_duoc: list[str] = []

    for alias in danh_sach_alias:
        mau = mau_ranh_gioi(alias)
        vi_tri = [m.span() for m in re.finditer(mau, con_lai)]
        if not vi_tri:
            continue

        ten = tu_dien_nguoc[alias]
        if ten not in tim_duoc:
            tim_duoc.append(ten)

        for bat_dau, ket_thuc in vi_tri:
            con_lai = con_lai[:bat_dau] + " " * (ket_thuc - bat_dau) + con_lai[ket_thuc:]

    return tim_duoc


if __name__ == '__main__':
    import sys
    # Console Windows mac dinh la cp1252 -> print tieng Viet se crash.
    sys.stdout.reconfigure(encoding="utf-8")

    assert tien_xu_ly("React.js") == "react.js"
    assert tien_xu_ly("CI/CD") == "ci/cd"
    assert tien_xu_ly(" K8S \t\n") == "k8s"
    assert tien_xu_ly("") == ""
    # Bỏ dấu
    assert tien_xu_ly("  Lập Trình   Python ") == "lap trinh python"
    assert tien_xu_ly("ĐIỀU PHỐI container") == "dieu phoi container"
    assert tien_xu_ly("Học\tmáy\n") == "hoc may"
    assert tien_xu_ly("Học máy") == "hoc may"
    assert tien_xu_ly("") == ""
    print(" Tầng 0: tất cả assert đều qua!")

    # Tầng 1: khớp alias chính xác
    td = doc_tu_dien_nguoc(Skill_link)
    assert khop_chinh_xac("ReactJS", td) == "react"
    assert khop_chinh_xac("  K8S ", td) == "kubernetes"
    assert khop_chinh_xac("Lập trình Python", td) == "python"
    assert khop_chinh_xac("GitHub Actions", td) == "ci/cd"
    assert khop_chinh_xac("_ghi_chu", td) is None
    assert khop_chinh_xac("React Native", td) == "react native"  # đã thêm vào từ điển
    print(" Tầng 1: tất cả assert đều qua!")

    # Tầng 2: alias dài nhất nằm trong chuỗi
    assert tim_alias_dai_nhat("Kinh nghiệm 3 năm với Docker", td) == "docker"
    assert tim_alias_dai_nhat("Xây dựng pipeline bằng GitHub Actions", td) == "ci/cd"
    assert tim_alias_dai_nhat("Từng làm app bằng React Native", td) == "react native"
    assert tim_alias_dai_nhat("Tôi rất happy với công việc", td) is None
    assert tim_alias_dai_nhat("Thành thạo JavaScript", td) == "javascript"
    assert tim_alias_dai_nhat("Không có kỹ năng nào ở đây", td) is None
    print(" Tầng 2: tất cả assert đều qua!")

    # Hàm tổng
    assert chuan_hoa("ReactJS", td) == "react"
    assert chuan_hoa("Viết script bash trên Ubuntu", td) == "linux"
    assert chuan_hoa("blockchain", td) is None
    print(" chuan_hoa: tất cả assert đều qua!")

    # Trích xuất trên toàn văn bản
    assert trich_xuat_ky_nang("Biết Java và JavaScript", td) == ["javascript", "java"]
    assert trich_xuat_ky_nang("Dùng Docker Compose, Docker Swarm", td) == ["docker"]

    # --- LỖI 2 (rà soát 18/09): alias ngắn chui qua dấu chấm ---
    # Trước khi sửa: cả ba dòng dưới đều trả về ["javascript"] vì alias "js"
    # bám được vào ".js". Vue / Next / D3 bị nuốt mất, còn Node.js thì bị quy
    # thành javascript mà không ai khai báo điều đó trong từ điển.
    assert trich_xuat_ky_nang("Kinh nghiệm Node.js", td) == []
    assert trich_xuat_ky_nang("Xây giao diện bằng Vue.js", td) == []
    assert trich_xuat_ky_nang("Dựng biểu đồ với D3.js", td) == []
    # Nhưng alias CÓ sẵn dấu chấm trong từ điển thì vẫn phải khớp
    assert trich_xuat_ky_nang("Dùng React.js", td) == ["react"]
    # Và dấu chấm cuối câu không được làm mất kỹ năng
    assert trich_xuat_ky_nang("Thành thạo Python.", td) == ["python"]

    # --- LỖI 3 (rà soát 18/09): chữ số dính liền làm mất kỹ năng ---
    # Trước khi sửa: "Java 17" ra java nhưng "Java17" ra [] - viết liền là mất.
    assert trich_xuat_ky_nang("Java17", td) == ["java"]
    assert trich_xuat_ky_nang("python2 va react18", td) == ["python", "react"]
    # Hàng rào phải vẫn phải chặn chữ cái, nếu không "javascript" bị cắt thành "java"
    assert trich_xuat_ky_nang("javascript", td) == ["javascript"]
    assert trich_xuat_ky_nang("Tôi rất happy", td) == []
    print(" Ranh gioi tu (loi 2 & 3): tất cả assert đều qua!")

    thu_muc_data = Path(__file__).parent / "data"
    cv = (thu_muc_data / "cv_mau.txt").read_text(encoding="utf-8")
    jv = (thu_muc_data / "jv_mau.txt").read_text(encoding="utf-8")

    ky_nang_cv = trich_xuat_ky_nang(cv, td)
    ky_nang_jv = trich_xuat_ky_nang(jv, td)
    thieu = [k for k in ky_nang_jv if k not in ky_nang_cv]

    print()
    print("Kỹ năng trong CV :", sorted(ky_nang_cv))
    print("Kỹ năng trong JV :", sorted(ky_nang_jv))
    print("CÒN THIẾU        :", sorted(thieu))
