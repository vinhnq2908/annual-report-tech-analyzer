# Annual Report Tech Analyzer

Ứng dụng Streamlit nhận danh sách từ khóa và link PDF báo cáo thường niên. Ứng dụng tải PDF, trích xuất chữ, đếm từ khóa, lấy câu bằng chứng, rồi xuất CSV.

## Chạy trên máy

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Publish miễn phí bằng Streamlit Community Cloud

1. Tạo repository public trên GitHub.
2. Upload `app.py` và `requirements.txt` vào repository.
3. Mở [share.streamlit.io](https://share.streamlit.io).
4. Chọn repository, branch, file `app.py`.
5. Bấm Deploy.
6. Gửi URL ứng dụng cho người khác.

## Lưu ý phương pháp

`tech_adoption=1` hiện dùng quy tắc heuristic: có từ khóa công nghệ và có từ hành động. Cần đọc lại cột `evidence` trước khi dùng dữ liệu nghiên cứu. Báo cáo scan ảnh cần OCR; bản hiện tại xử lý PDF có lớp text.
