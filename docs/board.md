# Bảng theo dõi repo (`docs/ui/board.html`)

Một trang HTML duy nhất, **chỉ đọc**, để thấy trên một màn hình: những repo bạn liên kết, task nào đang chạy và gồm những bước nào, quy trình (workflow) của từng repo, lịch chạy theo cron trong 7 ngày tới, và agent. Trang không gửi lệnh, không ghi gì, không chạy hay hủy được workflow: việc đó vẫn ở [`ui.md`](ui.md) (trang quét) hoặc trên GitHub.

```text
api.github.com (GET) ─► board.html ◄─ snapshot.json (tùy chọn, nạp bằng tay)
  runs, jobs, steps,                    ▲
  workflow files, PR,                   └─ python3 scripts/office/snapshot.py   (Văn phòng agent, repo claude-agent-routing-template)
  .claude/agents
```

## Mở trang

- Tải `docs/ui/board.html` về máy và mở bằng trình duyệt. Không cài gì, không máy chủ, không build.
- **Không dùng GitHub Pages `github.io`**: mọi trang của cùng một chủ dùng chung một origin ở đó, nên script của trang khác có thể mở trang này và đọc ô token. Trang tự từ chối nhận token trên `*.github.io` (cùng lý do như [`ui.md`](ui.md)). Cần một địa chỉ riêng: `python3 -m http.server 8123 --directory docs/ui` rồi mở `http://localhost:8123/board.html`.
- Trang chỉ nói chuyện với `api.github.com` (ép bằng Content-Security-Policy, không chỉ lời hứa), không tải thư viện, font, ảnh hay script nào từ nơi khác, và từ chối chạy trong khung nhúng.

## Token

Repo công khai đọc được **không cần token**, nhưng hạn mức khi đó chỉ 60 yêu cầu/giờ cho mỗi IP, và trang tắt tự làm mới (bấm *Làm mới* khi cần). Có token chỉ-đọc: 5.000 yêu cầu/giờ và đọc được repo private.

GitHub → Settings → Developer settings → *Fine-grained tokens*, chọn **đúng các repo** bạn muốn theo dõi, quyền **Metadata, Actions, Pull requests, Contents: Read**, hạn ngắn. **Không** dùng chung với token của trang quét (cái đó có quyền Actions: Write): trang này không cần ghi, và mã của nó chỉ có đúng một chỗ gọi `fetch` với `method: "GET"` (test kiểm).

Token nằm trong ô mật khẩu, mất khi đóng hoặc tải lại trang, không vào `localStorage`/cookie/URL, chỉ đi vào header `Authorization` tới `api.github.com`. *Quên token* xóa luôn mọi thứ đã tải bằng token đó (repo private biến mất khỏi trang). Trang **có** lưu một thứ trong `localStorage`: danh sách tên repo (và chu kỳ làm mới), dưới một khóa `radar-board.v1`; tên repo không phải bí mật.

## Mỗi thứ trên trang lấy từ đâu

| Trên trang | Lấy từ | Ghi chú |
|---|---|---|
| Task đang chạy | `GET /repos/{r}/actions/runs?per_page=40` | Lượt chạy có trạng thái `in_progress`, `queued`, `waiting`, `pending` trong **40 lượt mới nhất** của repo. Mỗi repo hiện tối đa 4 task kèm chi tiết, phần còn lại được đếm |
| Job và từng bước của task | `GET /repos/{r}/actions/runs/{id}/jobs` | Tiến độ = số bước đã xong ÷ số bước. Job chưa bắt đầu chưa liệt kê bước nào nên con số có thể nhảy: khi đó trang ghi "ước lượng" |
| Quy trình từng repo | `GET /repos/{r}/actions/workflows` + các lượt chạy ở trên | 12 lượt gần nhất mỗi workflow (cột cao là lỗi). Workflow có ít hơn 3 lượt trong danh sách chung (bị workflow bận hơn chen mất, ví dụ quét chạy 2 lần/tuần cạnh CI) được đọc riêng qua `GET /actions/workflows/{id}/runs` |
| "Có lỗi" của một repo | lượt **đã xong** gần nhất của từng workflow | Một lượt đang chạy không xóa lỗi của lượt trước nó cho đến khi nó xong |
| Lịch chạy | mục `schedule` trong file workflow (`GET /contents/.github/workflows/*.yml`) | Cron tính theo **UTC**, hiển thị theo giờ máy bạn. Khi cả ngày và thứ đều bị giới hạn thì khớp một trong hai (như cron của GitHub). Cron chạy hơn 6 lần mỗi ngày (ví dụ `*/30 * * * *`) không liệt kê từng lần mà ghi một dòng "chạy lặp". GitHub có thể trễ lượt theo lịch vài phút, chỉ chạy lịch từ nhánh mặc định, và tự tắt lịch của repo công khai sau 60 ngày không hoạt động |
| Agent thấy được trên GitHub | tên workflow, nhánh (`claude/`, `codex/`, `copilot/`, `gemini/`, `cursor/`, `devin/`, `jules/`), tác giả PR, và `.claude/agents/*.md` | **Suy đoán theo tên**, không phải trạng thái thật của phiên agent: một nhánh `claude/…` có thể do người tạo, một agent đổi tên nhánh thì không thấy. PR của dependabot/renovate chỉ hiện nhãn `bot`, không tính là agent |
| Agent thật | file `snapshot.json` của **Văn phòng agent** | Xem dưới đây |

### Agent thật: nối với Văn phòng agent

Trạng thái thật của agent (đang làm, đang chờ, bị chặn, ngân sách, tiến độ) chỉ có ở máy chạy chúng. Repo `claude-agent-routing-template` đã có "Văn phòng agent" ghi lại điều đó bằng hook của Claude Code (`docs/office-dashboard.md` ở repo đó). Trang này **không viết lại** phần đó, chỉ đọc snapshot của nó:

```bash
# trong checkout của claude-agent-routing-template (hoặc repo tạo từ nó)
python3 scripts/office/snapshot.py > snapshot.json
```

rồi chọn file ở mục *Agent → Phiên agent trên máy bạn*. Trang nhận đúng `version: 1`, `mode: claude`, từ chối thứ khác với lý do, cắt mọi chuỗi và số lượng, và coi mọi chữ trong file là dữ liệu (chỉ `textContent`). File được đọc trong trình duyệt, không gửi đi đâu, không lưu. Muốn có số liệu "sống" thay vì nạp tay thì máy chủ Office (`serve.py`) phải cho phép trang này gọi nó (CORS), và đó là một thay đổi ở repo kia, chưa làm.

## Hạn mức và chi phí

Một lượt xem của một repo là khoảng 8 đến 12 yêu cầu: repo, các lượt chạy, workflow, PR, job của mỗi task đang chạy, mỗi file workflow, `.claude/agents`, và lịch sử của workflow bị chen mất. Giảm chi phí bằng:

- **ETag**: mọi yêu cầu gửi `If-None-Match`; nếu không đổi GitHub trả 304 và trang dùng lại bản cũ. Đã đo với GitHub thật (CORS cho phép header này). **Không có token thì 304 vẫn tính vào hạn mức** (đo được 43 xuống 42), nên đừng bật tự làm mới khi không có token. Theo tài liệu của GitHub, có token thì 304 không tính; điều đó chưa đo ở đây.
- File workflow và `.claude/agents` giữ 10 phút (bấm *Làm mới* để đọc lại, vẫn bằng yêu cầu có điều kiện).
- Tự làm mới (30 giây, 1 phút, 5 phút) chỉ chạy khi **có token**, khi tab đang hiện, và gộp lại nếu lượt trước chưa xong. Tối đa 30 repo, đọc 3 repo cùng lúc.

Hết hạn mức thì thẻ repo nói rõ và có nút *Thử lại*.

## Dữ liệu mẫu

*Xem dữ liệu mẫu* dựng ba repo giả (`demo/…`) và một snapshot Office giả bằng **đúng mã** dùng cho dữ liệu thật, không gọi mạng, để xem trang trước khi có token. Mọi tên và số trong đó đều giả; trang có biểu ngữ nói điều đó và danh sách repo của bạn không bị ghi đè.

## Cái gì được tận dụng, cái gì không (kiểm ngày 16/10/2026)

Số sao đọc từ trang github.com (làm tròn); API công khai trả 403 qua công cụ tìm kiếm nên không có ngày commit cuối. Chỉ những cái dùng được miễn phí (MIT/Apache-2.0) mới được tính.

| Nguồn | Gần yêu cầu ở | Dùng thế nào |
|---|---|---|
| **Văn phòng agent** (`claude-agent-routing-template`, của bạn) | agent đang chạy, ngân sách, tiến độ | **Dùng**: trang đọc snapshot của nó |
| **Automation-UI-Kit** (của bạn, MIT) | màu trạng thái, thanh lịch sử | **Dùng token và kiểu, không dùng code React**: trạng thái là chấm màu + chữ trung tính (màu chữ không bao giờ là chỗ duy nhất mang nghĩa), màu theo token đã kiểm tương phản, dải lịch sử kiểu tracker. Trang là HTML thuần để chạy từ một file, nên không nhập được component React |
| [DashGit](https://github.com/javiertuya/dashgit) (MIT, 17★) | trang trình duyệt, nhiều repo, issue/PR | Tham khảo. Khác ở chỗ lưu token trong `localStorage` (trang này không), và không có job/bước hay cron |
| cronstrue, cron-parser (MIT, ~1,5k★, số liệu từ trang tổng hợp) | mô tả và tính giờ cron | **Không nhúng**: cần phần rất nhỏ, và chính sách của trang cấm script từ nơi khác. Tự viết ~60 dòng, kiểm trên 54 tổ hợp với bộ so chuẩn tìm từng phút viết riêng bằng Python |
| claude-view (MIT, 114★), Claude-Code-Agent-Monitor (MIT, 1,1k★) | phiên Claude Code thật, nhiều dự án | Chưa dùng: cần server cục bộ và hook; Office đã làm việc đó cho team của bạn |
| Mission Control (MIT, 6,4k★), GitActionBoard (Apache-2.0, 163★) | agent + task + cron / trạng thái Actions | Chưa dùng: server riêng và mô hình dữ liệu riêng, không đọc workflow của repo bạn như trang này |
| flowdive (chưa thấy giấy phép), Dagu (GPL-3.0), Vibe Kanban (đang ngừng phát triển) | | Loại |

Gitdeck hiện trong một lượt tìm với ~390 sao nhưng chưa kiểm được repo thật, nên không đưa vào bảng.

## An toàn

- Chỉ `GET`. Test chỉ chấp nhận đúng một chỗ gọi `fetch`, đúng một header `Authorization`, và chỉ hai host trong mã (`api.github.com` để đọc, `github.com` cho đường link).
- Mọi chữ từ GitHub hoặc từ snapshot vào trang bằng `textContent`; không `innerHTML`, `eval`, `document.write`. Test trong Chromium cho một tên workflow chứa `<img onerror=…>`, một tiêu đề PR chứa `<b>` và một snapshot chứa thẻ: tất cả chỉ hiện thành chữ.
- Đường link chỉ ghép từ tên repo đã kiểm (`chủ/tên`) và số nguyên; không bao giờ dùng URL do GitHub trả về. `rel="noopener noreferrer"`. Yêu cầu gửi `credentials: omit`, `referrerPolicy: no-referrer`.
- Giới hạn còn lại, không tránh được: ai chạy được JavaScript trên máy bạn, hay trình duyệt đã cài tiện ích độc, đọc được ô mật khẩu. Vì vậy token chỉ đọc, chỉ các repo cần, hết hạn sớm.

## Đã kiểm và chưa kiểm

Đã kiểm bằng máy:

- `tests/test_board.py` (luôn chạy, cần Node): CSP băm đúng; không API cấm; chỉ đọc; phần tính thuần của trang (tên repo, trạng thái run/step, tiến độ, cron, kế hoạch tuần, đoán agent, đọc snapshot, dữ liệu mẫu) chạy dưới Node. Cron được so với bộ so chuẩn từng phút. Đã thử đột biến (đổi OR thành AND ở luật ngày/thứ, bỏ màu đỏ của lỗi, bỏ ranh giới từ khi đoán agent, ghi token vào kho, đổi GET thành POST): mỗi đột biến bị test bắt.
- `tests/test_board_browser.py` (cần Playwright và Chromium, nếu không thì bỏ qua) với `api.github.com` do test trả lời: nội dung hiển thị, token chỉ ở một header và không nằm ở đâu khác, chữ lạ chỉ là chữ, ETag, từng kiểu lỗi, thêm/bỏ/lưu repo, dữ liệu mẫu không gọi mạng, nạp snapshot, không tràn ngang ở 320/390/768 px, không chạy trong khung nhúng, bàn phím.
- Với **GitHub thật** (đọc repo công khai `vohoailinh90/Github-radar`, không token): CORS cho phép các header của trang, 304 trả đúng cho JS, lịch `0 1 * * 3,6` hiện "01:00 UTC, T4 T7, kế tiếp 08:00 Th 7", và phát hiện lỗi "workflow bị chen mất" đã sửa.

**Chưa kiểm:** token thật (fine-grained, repo private; tên các quyền ở trên là theo tài liệu GitHub, chưa thử), việc 304 miễn phí khi có token, nút *Chọn từ tài khoản* với `/user/repos` thật, một snapshot do hook thật sinh ra (đã thử với snapshot mẫu do chính mã của Office tạo: đặt `OFFICE_TEMPLATE` rồi chạy `tests/test_board.py`), và trình duyệt khác ngoài Chromium.

## Giữ trang đúng với mã

Trang này không phản chiếu giá trị Python nào, chỉ có hai mã băm CSP. Sửa script hay style trong trang rồi chạy:

```bash
python3 scripts/ui_sync.py          # ghi lại mã băm của cả hai trang
python3 scripts/ui_sync.py --check  # thoát 1 nếu lệch (test cũng kiểm)
```
