# Trang quét theo yêu cầu (`docs/ui/index.html`)

Một trang HTML duy nhất để bạn chọn điều kiện, xem ước tính, bấm một nút và theo dõi lượt chạy, thay vì mở Actions và điền form. Trang **không quét gì**: nó chỉ gửi lệnh chạy workflow `radar.yml` (cùng lệnh *Run workflow* trên GitHub). Việc quét, gọi model, ghi `digests/` và mở PR nháp vào studio vẫn do GitHub Actions làm, với các key đã nằm trong Secrets. Trang không thấy và không cần key của model.

## Mở trang

- **Cách đơn giản nhất:** tải file `docs/ui/index.html` về máy và mở bằng trình duyệt. Không cài gì, không máy chủ.
- **Nếu trình duyệt không cho trang gọi GitHub từ file** (chưa thử, xem phần kiểm tra bên dưới): chạy `python3 -m http.server 8123 --directory docs/ui` rồi mở `http://localhost:8123`. Origin đó (máy bạn, cổng đó) không dùng chung với trang nào khác.
- **Không dùng GitHub Pages của tài khoản (`<chủ>.github.io`).** Mọi trang của cùng một chủ ở đó dùng chung **một origin**: script của một trang khác (ví dụ một trang bị chèn mã) có thể mở trang này bằng `window.open` rồi đọc ô token sau khi bạn dán, và CSP hay kiểm tra khung nhúng của trang không chặn được việc đó. Vì thế trang tự từ chối nhận token khi chạy trên `*.github.io` (hiện cảnh báo, khóa ô token). Một tên miền riêng chỉ dành cho trang này thì an toàn về điểm này, nhưng chưa được thử ở đây.

Trang chỉ nói chuyện với `api.github.com` (điều này được ép bằng Content-Security-Policy trong trang, không phải chỉ lời hứa). Không có thư viện, font, ảnh hay script nào tải từ nơi khác.

## Tạo token (một lần, rồi thay định kỳ)

GitHub → Settings → Developer settings → *Personal access tokens* → **Fine-grained tokens** → *Generate new token*:

| Mục | Chọn |
|---|---|
| Resource owner | tài khoản chứa repo |
| Repository access | **Only select repositories** → chỉ `Github-radar` |
| Repository permissions | **Actions: Read and write**. Không chọn quyền nào khác (`Metadata: Read` được thêm sẵn) |
| Expiration | ngắn (7 đến 30 ngày) |

**Đừng** dùng chung token này với `RADAR_PR_TOKEN` (cái có quyền ghi code và PR, nằm trong Environment secrets của môi trường `radar`, xem [`branch-protection.md`](branch-protection.md)). Quyền *Actions: Read and write* rộng hơn "chạy workflow": với repo này, token có thể chạy, **hủy**, chạy lại và **xóa** các lượt chạy cùng nhật ký của chúng, **tắt hoặc bật** workflow, và xóa cache/artifact. Nó **không** đọc hay ghi code, không đọc hay ghi Secrets và biến, không sửa được file workflow. Vì không ghi được code, nó không thể đẩy một nhánh có `radar.yml` đã sửa; nhưng nếu một nhánh như thế đã có sẵn trong repo, token này (gọi API trực tiếp, không qua trang, vì trang chỉ chạy nhánh mặc định) chạy được nó. Đó là lý do khóa Environment `radar` vào nhánh `main` như trong `branch-protection.md`. Nếu token lộ, kẻ cầm nó phá được lịch sử lượt chạy và tắt được lịch quét; vì vậy một repo, hạn ngắn, và thu hồi ngay khi nghi ngờ.

Dán token vào ô *Token* rồi bấm **Kiểm tra token**: trang gọi GitHub đọc repo và đọc workflow `radar.yml`, và báo rõ nếu token sai hay không đúng repo. Việc này chỉ chứng minh token **đọc** được; quyền *ghi* Actions chỉ lộ ra ở lượt gửi đầu tiên (nếu thiếu, GitHub trả 403 và trang báo cần Actions: Read and write). Trang nói thẳng điều đó thay vì báo "dùng được".

## Dùng

1. **Kết nối:** tên repo (`chủ/tên`) và token.
2. **Điều kiện:** chọn một bộ đã lưu (điền sẵn mọi ô), rồi sửa từng ô nếu muốn: số bài, sàn sao, ngày commit, ngôn ngữ, lượt tìm repo trẻ, nhóm và topic. Hoặc điền một repo bạn chọn (`chủ/tên`) để quét đúng repo đó: lúc này ước tính tính cho đúng một repo (không tìm kiếm, bỏ qua số bài), và danh sách nhóm chỉ còn những nhóm đang được giữ (workflow từ chối một nhóm đã bị điều kiện loại). Lỗi hiện ngay (ví dụ topic `llm stars:>0` bị từ chối, vì topic được ghép vào câu truy vấn tìm kiếm). Dòng *Ước tính* in cùng con số với `python3 radar.py presets` cho một lượt quét thật; với *Quét thử* (mặc định) nó vẫn tính phần tìm kiếm nhưng ghi rõ không gọi model và không nghỉ giữa bài. Khung JSON bên dưới là điều kiện đã chọn; dán vào `radar/presets.json` nếu muốn lưu thành bộ mới.
3. **Quét:** mặc định là **quét thử** (chỉ xếp hạng, không gọi model, không ghi gì). Bỏ chọn để **quét thật**: trang đòi bạn gõ `QUET` rồi mới mở nút, vì quét thật dùng hạn mức model và ghi vào `main`.
4. **Các lượt chạy gần đây:** bảng tự làm mới mỗi 10 giây khi có lượt đang chạy; mỗi dòng có link mở lượt chạy trên GitHub. Kết quả quét thử nằm trong *Summary* của lượt chạy.
5. **Chạy trên máy bạn (không cần token Actions):** mục 5 của trang viết sẵn lệnh `radar.py` tương đương với điều kiện đã chọn, kèm nút *Sao chép lệnh*. Trang không tự chạy được Python; bạn dán lệnh vào cửa sổ lệnh đang mở trong thư mục của repo (đã `pip install -r requirements.txt`). Chọn đúng kiểu cửa sổ: *Windows (cmd)* dùng `python` và đặt JSON trong dấu nháy kép, *macOS, Linux, Git Bash* dùng `python3` và dấu nháy đơn. PowerShell chưa có dạng riêng (cách truyền JSON khác nhau giữa các bản); dùng cmd hoặc chỉ chọn bộ đã lưu, khi đó lệnh không có JSON. Lệnh theo ô *Quét thử*: quét thử là `scan` (chỉ xếp hạng, không gọi model, không ghi file; `scan` không nhận `--repo`), quét một repo là `run --repo ... --dry-run`, quét thật là `run` (gọi model, cần khóa model trong biến môi trường, ghi vào `digests/`, `export/` và `state/` của bản clone, không mở PR). Lệnh chỉ chứa phần bạn đã đổi so với bộ đã chọn, giống những gì trang gửi lên workflow. Nên đặt biến `GITHUB_TOKEN` (một token không cần quyền nào) trước khi quét trên máy; nếu không, GitHub giới hạn tìm kiếm rất thấp. Token ở mục 1 không bao giờ được đưa vào lệnh.

Trang chỉ gửi **từng ô bạn đã đổi** so với bộ đã chọn (hoặc `radar.yaml` nếu không chọn bộ nào): đổi sàn sao thì gửi `{"min_stars": 5000}` và không gì khác; riêng `rising` gửi từng thiết lập, còn `langs` và `buckets` gửi nguyên (workflow cũng thay nguyên hai mục này). Nhờ vậy một trang mở từ lâu không ghim các giá trị cũ của `radar.yaml` hay của bộ đã chọn lên lượt quét: những gì bạn không đổi do workflow lấy từ bản hiện tại. Con số *Ước tính* thì vẫn tính theo bản chép trong trang, nên chạy lại `scripts/ui_sync.py` và tải lại trang sau khi sửa cấu hình. **Người quyết định cuối cùng vẫn là workflow**: nó kiểm lại mọi thứ trước khi gọi GitHub hay model (`radar/conditions.py`), nên trang không thể gửi điều kiện mà `radar.yaml` và `CLAUDE.md` cấm.

Các lần quét không chạy chồng (`concurrency: radar`): gửi thêm khi đang có một lượt chờ thì GitHub **thay** lượt chờ cũ, lượt cũ hiện là "Đã hủy (có thể bị thay bằng một yêu cầu mới hơn)". Nếu danh sách (đọc ngay trước khi gửi, gồm cả lượt theo lịch vì cùng nhóm đồng thời) có sẵn một lượt chờ chưa chạy, trang **hỏi một lần** ("gửi lúc này có thể thay nó") và chỉ gửi ở lần bấm thứ hai; lượt đang chạy thì không cần hỏi. Trang không chặn hẳn vì chưa kiểm được GitHub gọi lượt bị nhóm đồng thời giữ lại là `pending` hay `queued`, nên mọi lượt chưa chạy đều được coi là có thể bị thay. Trang không cho gửi tiếp khi lượt bạn vừa gửi còn đang chạy hay chờ, và cả trong lúc GitHub chưa liệt kê lượt đó (thường vài giây). Hết 2 phút mà một lần đọc danh sách **thành công** vẫn không thấy lượt đó thì trang mở khóa; nếu các lần đọc đều lỗi, hoặc bạn rời repo ấy suốt thời gian đó, nút vẫn khóa cho tới khi một lần đọc thành công (khi bạn quay lại, trang tự đọc).

Trang nhận ra "lượt bạn vừa gửi" không bằng đồng hồ mà bằng số thứ tự: ngay trước khi gửi nó đọc danh sách lượt chạy, rồi coi lượt có số lớn hơn mọi lượt đã thấy là lượt của mình (số của GitHub chỉ tăng). Vì vậy đồng hồ máy lệch bao nhiêu cũng không ảnh hưởng. Hệ quả: không đọc được danh sách đó thì trang **không gửi** (báo "Chưa gửi") thay vì gửi mà không theo dõi được. Khi trang không chắc, nó chọn bên an toàn (không gửi thêm): nếu không đọc được danh sách lượt chạy thì giữ nguyên khóa của lượt đã thấy đang chạy (không biết thì chưa coi là xong) và hỏi lại mỗi 10 giây; muốn mở khóa ngay thì bấm *Quên token* hoặc tải lại trang. Nếu mất kết nối đúng lúc gửi, hoặc GitHub trả lỗi 5xx, lệnh có thể đã tới nơi: trang báo "chưa biết lệnh đã tới GitHub chưa", đợi xem có lượt mới hiện ra (cùng quy tắc 2 phút ở trên) và không cho gửi lại ngay.

Trang nhớ lượt đã gửi **theo từng repo** (tên repo không phân biệt hoa thường, như GitHub; kể cả khi bạn gửi sang repo khác rồi quay lại): gõ sang repo khác thì nút mở cho repo đó, gõ lại repo cũ thì khóa trở lại (và trang tự hỏi lại xem lượt ấy đang ở đâu). Nếu hai lần đọc danh sách chồng nhau, chỉ câu trả lời của lần đọc mới nhất được dùng; câu trả lời cũ về muộn bị bỏ.

Bấm *Quên token* lúc lệnh đang gửi là kết thúc phiên: trang không tạo ra khóa nào sau đó (nó báo lệnh có thể đã tới GitHub, hãy xem tab Actions). Khi nút đang khóa vì một lượt đã gửi, trang ghi lý do ngay dưới nút; dán token lại rồi rời ô (hoặc bấm *Kiểm tra token* hay *Làm mới*) thì trang đọc lại danh sách để biết lượt đó đang ở đâu.

Một lệnh gửi bị treo không giữ nút khóa sau khi bạn bấm *Quên token* (phiên mới không phải chờ yêu cầu cũ), và kết thúc muộn của yêu cầu cũ không mở khóa cho lần gửi mới hơn. Bảng lượt chạy cũng tiếp tục được làm mới sau một lần đọc lỗi nếu lần đọc tốt gần nhất còn thấy lượt đang chạy (kể cả lượt do người khác bấm).

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
- Giới hạn còn lại, không tránh được: ai chạy được JavaScript trên máy bạn, hay trình duyệt đã cài tiện ích độc, đọc được ô mật khẩu. Vì vậy token chỉ có quyền Actions (xem mục tạo token về những gì quyền đó cho phép), chỉ một repo, và hết hạn sớm.

## Kiểm bằng máy và những gì chưa kiểm trên GitHub thật

Đã kiểm bằng máy (`tests/test_ui.py` luôn chạy, cần Node; `tests/test_ui_browser.py` chạy khi có Playwright và Chromium, nếu không thì bỏ qua):

- Khối dữ liệu và mã băm CSP đúng với mã hiện tại; không có API nguy hiểm, địa chỉ lạ, hay chỗ nào ngoài ô mật khẩu giữ token.
- Phần tính của trang (gộp bộ với điều kiện nhập thêm, ước tính có làm tròn kiểu Python, luật "tối đa một nửa số bài cho repo trẻ", điều kiện hợp lệ) chạy dưới Node và so với `radar/conditions.py` trên hàng trăm tổ hợp. Một điều kiện mà trang chấp nhận thì Python cũng chấp nhận, và ngược lại.
- Lệnh ở mục 5: dưới Node, lệnh cho cả hai kiểu cửa sổ được tách thành danh sách đối số (kiểu Windows theo luật của C runtime, kiểu sh bằng `shlex`), hai danh sách phải giống nhau, rồi được đưa vào bộ phân tích tham số thật của `radar.py`; giá trị mà lượt quét đó nhận phải đúng bằng giá trị trên form, với mọi bộ đã lưu, có và không có chỉnh sửa, quét thử và quét thật, có và không có một repo. Dấu nháy kiểu sh phải trùng `shlex.quote`; kiểu cmd từ chối mọi ký tự mà cmd có thể đọc là cú pháp (`& | < > ^ % ! ( )`, `\`). Chưa chạy trên một cửa sổ Windows thật: luật tách đối số của Windows được kiểm bằng một bản cài đặt lại trong test (và bản đó được kiểm ngược với `subprocess.list2cmdline`), không phải bằng cmd.exe.
- Trong Chromium, với `api.github.com` do test trả lời: nội dung lệnh gửi đi, yêu cầu gõ `QUET`, token không được lưu ở đâu, chữ lạ từ GitHub chỉ hiện thành chữ, tên repo/nhánh sai không tạo yêu cầu nào, trang không chạy trong khung nhúng, CSP chặn script chèn thêm.

Môi trường dựng trang không nối được GitHub thật, nên **chưa kiểm trên GitHub thật**. Bạn thử một lần (5 phút):

1. Mở trang, dán token, *Kiểm tra token*: phải hiện "Token đọc được repo và workflow radar.yml…". Nếu báo "Không kết nối được api.github.com" khi mở từ file, thử cách `http://localhost` ở trên (CORS từ `file://` chưa được thử).
2. Chọn `quet-nhanh`, giữ *Quét thử*, bấm *Quét thử*: phải hiện một dòng mới trong bảng ("lượt bạn vừa gửi"), rồi "Xong". Mở link, vào *Summary* xem `conditions.label` là `quet-nhanh`.
3. Gửi hai lượt liền nhau: lượt đầu có thể hiện "Đã hủy (có thể bị thay…)" (cách GitHub xử lý nhóm đồng thời, chưa thử ở repo này).
4. Chỉ khi hai bước trên ổn: quét thật với `quet-nhanh` (1 bài).
