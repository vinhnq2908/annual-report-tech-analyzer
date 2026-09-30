import csv
import io
import ipaddress
import re
import socket
from collections import Counter
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import streamlit as st
from pypdf import PdfReader

st.set_page_config(page_title="Annual Report Tech Analyzer", layout="wide")

ACTION_WORDS = [
    "triển khai", "áp dụng", "sử dụng", "đầu tư", "vận hành", "tích hợp",
    "nâng cấp", "xây dựng", "phát triển", "tự động hóa", "implemented",
    "adopted", "deployed", "used", "invested", "operated", "integrated",
    "upgraded", "developed", "automation",
]


def public_url(raw_url: str) -> str:
    url = raw_url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("URL phải bắt đầu bằng http:// hoặc https://")
    host = parsed.hostname
    try:
        addresses = socket.getaddrinfo(host, None)
        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if not ip.is_global:
                raise ValueError("URL trỏ tới địa chỉ mạng nội bộ, bị từ chối")
    except socket.gaierror as exc:
        raise ValueError(f"Không phân giải được tên miền: {host}") from exc
    return url


def download_pdf(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "AnnualReportTechAnalyzer/1.0"})
    with urlopen(request, timeout=30) as response:
        content_type = (response.headers.get("Content-Type") or "").lower()
        data = response.read(30 * 1024 * 1024 + 1)
    if len(data) > 30 * 1024 * 1024:
        raise ValueError("PDF vượt giới hạn 30 MB")
    if "pdf" not in content_type and not data.startswith(b"%PDF"):
        raise ValueError("URL không trả về file PDF")
    return data


def extract_text(pdf: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def terms_from_input(raw: str) -> list[str]:
    terms = []
    for line in raw.splitlines():
        for term in line.split(","):
            term = term.strip()
            if term and term.casefold() not in {x.casefold() for x in terms}:
                terms.append(term)
    return terms


def count_term(text: str, term: str) -> int:
    return len(re.findall(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text, flags=re.I))


def contexts(text: str, term: str, limit: int = 3) -> list[str]:
    sentences = re.split(r"(?<=[.!?。！？])\s+|\n+", text)
    found = []
    for sentence in sentences:
        if re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", sentence, re.I):
            cleaned = " ".join(sentence.split())
            if cleaned and cleaned not in found:
                found.append(cleaned[:500])
        if len(found) >= limit:
            break
    return found


def analyze(name: str, url: str, text: str, pages: int, terms: list[str]) -> dict:
    lower = text.casefold()
    counts = {term: count_term(text, term) for term in terms}
    total = sum(counts.values())
    mentioned = [term for term, count in counts.items() if count]
    action_hits = sum(lower.count(word.casefold()) for word in ACTION_WORDS)
    adoption = int(total > 0 and action_hits > 0)
    evidence = []
    for term in mentioned:
        evidence.extend(f"[{term}] {item}" for item in contexts(text, term))
    return {
        "document": name,
        "url": url,
        "pages": pages,
        "word_count": len(text.split()),
        "technology_frequency": total,
        "technology_diversity": len(mentioned),
        "action_word_hits": action_hits,
        "tech_adoption": adoption,
        "mentioned_terms": "; ".join(mentioned),
        "evidence": "\n".join(evidence[:10]),
        **{f"count_{term}": count for term, count in counts.items()},
    }


st.title("Annual Report Tech Analyzer")
st.caption("Đếm từ khóa công nghệ, lọc ngữ cảnh triển khai, xuất CSV.")

with st.sidebar:
    st.header("Từ vựng")
    vocabulary = st.text_area(
        "Mỗi dòng một từ/cụm từ; cũng nhận dấu phẩy",
        value="""chuyển đổi số
công nghệ số
trí tuệ nhân tạo
AI
dữ liệu lớn
Big Data
điện toán đám mây
Cloud
ERP
CRM
IoT
tự động hóa
robot
blockchain
phần mềm
digital transformation
artificial intelligence
cloud computing
big data
automation""",
        height=300,
    )
    st.header("Quy tắc áp dụng")
    st.write("Có ít nhất 1 từ khóa công nghệ và 1 từ hành động triển khai/sử dụng.")

links = st.text_area(
    "Link báo cáo PDF",
    placeholder="Mỗi dòng một URL PDF công khai",
    height=160,
)

if st.button("Phân tích", type="primary"):
    terms = terms_from_input(vocabulary)
    urls = [line.strip() for line in links.splitlines() if line.strip()]
    if not terms:
        st.error("Cần ít nhất một từ khóa.")
    elif not urls:
        st.error("Cần ít nhất một link PDF.")
    else:
        rows = []
        progress = st.progress(0)
        for index, raw_url in enumerate(urls, start=1):
            try:
                url = public_url(raw_url)
                pdf = download_pdf(url)
                reader = PdfReader(io.BytesIO(pdf))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
                row = analyze(url.rsplit("/", 1)[-1] or url, url, text, len(reader.pages), terms)
                rows.append(row)
                st.success(f"Đã phân tích: {row['document']}")
            except Exception as exc:
                st.warning(f"Bỏ qua {raw_url}: {exc}")
            progress.progress(index / len(urls))

        if rows:
            st.subheader("Kết quả")
            st.dataframe(rows, use_container_width=True)
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
            st.download_button(
                "Tải kết quả CSV",
                output.getvalue().encode("utf-8-sig"),
                "technology_analysis.csv",
                "text/csv",
            )
