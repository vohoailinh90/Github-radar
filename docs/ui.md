# Trang quét theo yêu cầu (`docs/ui/index.html`)

Một trang HTML duy nhất để bạn chọn điều kiện, xem ước tính, bấm một nút và theo dõi lượt chạy, thay vì mở Actions và điền form. Trang **không quét gì**: nó chỉ gửi lệnh chạy workflow `radar.yml` (cùng lệnh *Run workflow* trên GitHub). Việc quét, gọi model, ghi `digests/` và mở PR nháp vào studio vẫn do GitHub Actions làm, với các key đã nằm trong Secrets. Trang không thấy và không cần key của model.

## Mở trang

- **Cách đơn giản nhất:** tải file `docs/ui/index.html` về máy và mở bằng trình duyệt. Không cài gì, không máy chủ.
- **Hoặc dùng GitHub Pages:** Settings → Pages → *Deploy from a branch* → `main` / thư mục `/docs`. Trang nằm ở `https://<chủ>.github.io/<repo>/ui/`. Lưu ý: Pages công khai mọi thứ trong `/docs` (kể cả khi repo riêng tư, trừ gói Enterprise Cloud có Pages riêng tư). Trang này không chứa bí mật, nhưng nếu bạn muốn giữ kín bộ điều kiện và danh sách topic thì dùng cách tải file.

Trang chỉ nói chuyện với `api.github.com` (điều này được ép bằng Content-Security-Policy trong trang, không phải chỉ lời hứa). Không có thư viện, font, ảnh hay script nào tải từ nơi khác.

## Tạo token (một lần, rồi thay định kỳ)

GitHub → Settings → Developer settings → *Personal access tokens* → **Fine-grained tokens** → *Generate new token*:

| Mục | Chọn |
|---|---|
| Resource owner | tài khoản chứa repo |
| Repository access | **Only select repositories** → chỉ `Github-radar` |
| Repository permissions | **Actions: Read and write**. Không chọn quyền nào khác (`Metadata: Read` được thêm sẵn) |
| Expiration | ngắn (7 đến 30 ngày) |

**Đừng** dùng chung token này với `RADAR_PR_TOKEN` (cái có quyền ghi code và PR, nằm trong Environment secrets của môi trường `radar`, xem [`branch-protection.md`](branch-protection.md)). Token của trang chỉ có quyền chạy workflow: không đọc được code, không ghi được code, không đọc được Secrets. Có token này mà không có quyền ghi code thì cũng không thể đẩy một nhánh có `radar.yml` đã sửa để đọc Secrets.

Dán token vào ô *Token* rồi bấm **Kiểm tra token**: trang gọi GitHub đọc repo và đọc workflow `radar.yml`, và báo rõ nếu token sai hay không đúng repo. Việc này chỉ chứng minh token **đọc** được; quyền *ghi* Actions chỉ lộ ra ở lượt gửi đầu tiên (nếu thiếu, GitHub trả 403 và trang báo cần Actions: Read and write). Trang nói thẳng điều đó thay vì báo "dùng được".

## Dùng

1. **Kết nối:** tên repo (`chủ/tên`) và token.
2. **Điều kiện:** chọn một bộ đã lưu (điền sẵn mọi ô), rồi sửa từng ô nếu muốn: số bài, sàn sao, ngày commit, ngôn ngữ, lượt tìm repo trẻ, nhóm và topic. Hoặc điền một repo bạn chọn (`chủ/tên`) để quét đúng repo đó: lúc này ước tính tính cho đúng một repo (không tìm kiếm, bỏ qua số bài), và danh sách nhóm chỉ còn những nhóm đang được giữ (workflow từ chối một nhóm đã bị điều kiện loại). Lỗi hiện ngay (ví dụ topic `llm stars:>0` bị từ chối, vì topic được ghép vào câu truy vấn tìm kiếm). Dòng *Ước tính* in cùng con số với `python3 radar.py presets` cho một lượt quét thật; với *Quét thử* (mặc định) nó vẫn tính phần tìm kiếm nhưng ghi rõ không gọi model và không nghỉ giữa bài. Khung JSON bên dưới là điều kiện đã chọn; dán vào `radar/presets.json` nếu muốn lưu thành bộ mới.
3. **Quét:** mặc định là **quét thử** (chỉ xếp hạng, không gọi model, không ghi gì). Bỏ chọn để **quét thật**: trang đòi bạn gõ `QUET` rồi mới mở nút, vì quét thật dùng hạn mức model và ghi vào `main`.
4. **Các lượt chạy gần đây:** bảng tự làm mới mỗi 10 giây khi có lượt đang chạy; mỗi dòng có link mở lượt chạy trên GitHub. Kết quả quét thử nằm trong *Summary* của lượt chạy.

Trang chỉ gửi những gì khác với bộ đã chọn (hoặc `radar.yaml` nếu không chọn bộ nào), nên điều kiện nhập thêm vẫn nằm trong khoảng workflow chấp nhận. **Người quyết định cuối cùng vẫn là workflow**: nó kiểm lại mọi thứ trước khi gọi GitHub hay model (`radar/conditions.py`), nên trang không thể gửi điều kiện mà `radar.yaml` và `CLAUDE.md` cấm.

Các lần quét không chạy chồng (`concurrency: radar`): gửi thêm khi đang có một lượt chờ thì GitHub **thay** lượt chờ cũ, lượt cũ hiện là "Đã hủy (có thể bị thay bằng một yêu cầu mới hơn)". Trang không cho gửi tiếp khi lượt bạn vừa gửi còn đang chạy hay chờ, và cả trong lúc GitHub chưa liệt kê lượt đó (thường vài giây, tối đa chờ 2 phút).

Trang nhận ra "lượt bạn vừa gửi" không bằng đồng hồ mà bằng số thứ tự: ngay trước khi gửi nó đọc danh sách lượt chạy, rồi coi lượt có số lớn hơn mọi lượt đã thấy là lượt của mình (số của GitHub chỉ tăng). Vì vậy đồng hồ máy lệch bao nhiêu cũng không ảnh hưởng. Hệ quả: không đọc được danh sách đó thì trang **không gửi** (báo "Chưa gửi") thay vì gửi mà không theo dõi được. Khi trang không chắc, nó chọn bên an toàn (không gửi thêm): nếu không đọc được danh sách lượt chạy thì giữ nguyên khóa của lượt đã thấy đang chạy (không biết thì chưa coi là xong) và hỏi lại mỗi 10 giây; muốn mở khóa ngay thì bấm *Quên token* hoặc tải lại trang. Nếu mất kết nối đúng lúc gửi, hoặc GitHub trả lỗi 5xx, lệnh có thể đã tới nơi: trang báo "chưa biết lệnh đã tới GitHub chưa", đợi tối đa 2 phút xem có lượt mới hiện ra và không cho gửi lại ngay.

Trang nhớ lượt đã gửi **theo từng repo** (kể cả khi bạn gửi sang repo khác rồi quay lại): gõ sang repo khác thì nút mở cho repo đó, gõ lại repo cũ thì khóa trở lại (và trang tự hỏi lại xem lượt ấy đang ở đâu). Nếu hai lần đọc danh sách chồng nhau, chỉ câu trả lời của lần đọc mới nhất được dùng; câu trả lời cũ về muộn bị bỏ.

Giới hạn còn lại: nếu một người hay công cụ khác gửi một lượt đúng trong khoảng một giây giữa lúc trang đọc danh sách và lúc trang gửi, và lượt đó bị hủy ngay (nhóm đồng thời thay nó bằng lượt của bạn), trang có thể coi lượt bị hủy là lượt của mình và mở nút sớm vài giây, nên một lần bấm thật nhanh nữa có thể thay lượt của bạn đang chờ. Repo một chủ thì gần như không xảy ra; phân biệt được cần thêm một mã riêng vào đầu vào của workflow, chưa đáng.

## Giữ trang đúng với mã

Trang không import được Python, nên giữ một bản chép của vài giá trị (bộ đã lưu, giới hạn, cấu hình gốc, chi phí) và hai mã băm CSP. Sau khi sửa `radar/presets.json`, `radar.yaml`, `radar/conditions.py` hay chính trang, chạy:

```bash
python3 scripts/ui_sync.py          # ghi lại khối dữ liệu và hai mã băm
python3 scripts/ui_sync.py --check  # thoát 1 nếu lệch (test cũng kiểm)
```

Sửa script trong trang mà quên chạy lệnh trên thì CSP chặn chính script của trang (trang không chạy), và test báo lỗi.

## An toàn

- Token chỉ nằm trong ô mật khẩu của trang: không `localStorage`, `sessionStorage`, cookie, IndexedDB; không nằm trong URL; mất khi đóng hoặc rời trang; có nút *Quên token*. Mọi yêu cầu gửi với `credentials: omit` và `referrerPolicy: no-referrer`, chỉ tới `https://api.github.com`.
- Không dùng `innerHTML`, `eval`, `document.write`; mọi chữ từ GitHub (thông báo lỗi, tên kết luận) đưa vào bằng `textContent`. Link tới lượt chạy chỉ ghép từ tên repo đã kiểm (`chủ/tên`) và số id nguyên; có `rel="noopener noreferrer"`.
- Trang từ chối chạy trong khung nhúng (`<iframe>`), để trang khác không dụ bạn bấm nút.
- Quét thật cần gõ `QUET`; quét thử là mặc định.
- Giới hạn còn lại, không tránh được: ai chạy được JavaScript trên máy bạn, hay trình duyệt đã cài tiện ích độc, đọc được ô mật khẩu. Vì vậy token chỉ có quyền Actions, chỉ một repo, và hết hạn sớm.

## Kiểm bằng máy và những gì chưa kiểm trên GitHub thật

Đã kiểm bằng máy (`tests/test_ui.py` luôn chạy, cần Node; `tests/test_ui_browser.py` chạy khi có Playwright và Chromium, nếu không thì bỏ qua):

- Khối dữ liệu và mã băm CSP đúng với mã hiện tại; không có API nguy hiểm, địa chỉ lạ, hay chỗ nào ngoài ô mật khẩu giữ token.
- Phần tính của trang (gộp bộ với điều kiện nhập thêm, ước tính có làm tròn kiểu Python, luật "tối đa một nửa số bài cho repo trẻ", điều kiện hợp lệ) chạy dưới Node và so với `radar/conditions.py` trên hàng trăm tổ hợp. Một điều kiện mà trang chấp nhận thì Python cũng chấp nhận, và ngược lại.
- Trong Chromium, với `api.github.com` do test trả lời: nội dung lệnh gửi đi, yêu cầu gõ `QUET`, token không được lưu ở đâu, chữ lạ từ GitHub chỉ hiện thành chữ, tên repo/nhánh sai không tạo yêu cầu nào, trang không chạy trong khung nhúng, CSP chặn script chèn thêm.

Môi trường dựng trang không nối được GitHub thật, nên **chưa kiểm trên GitHub thật**. Bạn thử một lần (5 phút):

1. Mở trang, dán token, *Kiểm tra token*: phải hiện "Token đọc được repo và workflow radar.yml…". Nếu báo "Không kết nối được api.github.com" khi mở từ file, thử mở qua GitHub Pages (CORS từ `file://` chưa được thử).
2. Chọn `quet-nhanh`, giữ *Quét thử*, bấm *Quét thử*: phải hiện một dòng mới trong bảng ("lượt bạn vừa gửi"), rồi "Xong". Mở link, vào *Summary* xem `conditions.label` là `quet-nhanh`.
3. Gửi hai lượt liền nhau: lượt đầu có thể hiện "Đã hủy (có thể bị thay…)" (cách GitHub xử lý nhóm đồng thời, chưa thử ở repo này).
4. Chỉ khi hai bước trên ổn: quét thật với `quet-nhanh` (1 bài).
