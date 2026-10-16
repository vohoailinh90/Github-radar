# Bảo vệ nhánh `main` mà vẫn giữ lượt quét tự chạy

Lượt quét theo lịch (và lượt quét bạn chạy tay) lưu kết quả bằng cách `git push` thẳng vào `main`. Khi `main` bật bảo vệ (bắt buộc PR, bắt buộc check `test`), cú push đó bị chặn, lượt quét báo đỏ và kết quả mất. Cách xử lý: kết quả đi qua **một nhánh và một pull request**. Việc này cần một token riêng, vì token mặc định của Actions không đẩy được vào nhánh bảo vệ và PR do nó mở **không kích hoạt CI** (nên check `test` không bao giờ chạy và PR không merge được).

**Thứ tự quan trọng: tạo token và thử một lượt quét TRƯỚC, bật bảo vệ SAU.** Chưa có token thì bước commit vẫn push thẳng như cũ, nên chưa có gì hỏng.

## 1. Tạo token (một lần)

GitHub → Settings (của tài khoản) → Developer settings → Personal access tokens → **Fine-grained tokens** → Generate new token.

| Mục | Giá trị |
|---|---|
| Repository access | **Only select repositories** → chỉ `Github-radar` |
| Repository permissions | **Contents: Read and write**, **Pull requests: Read and write** (Metadata: Read-only tự có). Không cần quyền nào khác |
| Expiration | Ngắn (ví dụ 90 ngày) và ghi lại ngày hết hạn: token hết hạn thì lượt quét báo đỏ ở bước commit |

**Đặt token vào Environment `radar`, không đặt vào Repository secrets.** Lý do: một lệnh chạy workflow thủ công chạy **file workflow của nhánh được chọn**, nên một nhánh (của ai có quyền ghi) có thể xóa mọi điều kiện `if:` trong file và đọc secret, rồi giữ token dài hạn có quyền ghi nội dung. Chỉ Environment mới từ chối được job ở nhánh khác. Job của workflow đã khai báo `environment: radar`; việc còn lại là của bạn:

1. Repo → Settings → **Environments** → New environment, tên đúng `radar` (sau lần chạy đầu GitHub cũng tự tạo, nhưng chưa có hạn chế).
2. Trong environment đó: **Deployment branches and tags** → **Selected branches and tags** → Add → `main`.
3. **Environment secrets** → Add secret, tên `RADAR_PR_TOKEN`, dán token. Đừng tạo thêm một bản cùng tên trong *Repository secrets*: bản đó mọi nhánh đều đọc được.

Từ đó workflow chỉ chạy được trên `main`: bấm *Run workflow* ở nhánh khác sẽ bị chặn ngay khi job bắt đầu. (Muốn thử workflow đang sửa trên nhánh khác, tạm thêm nhánh đó vào danh sách rồi gỡ ra.) Làm tương tự cho các khóa model và `STUDIO_REPO_TOKEN` thì chúng cũng được bảo vệ như vậy: chuyển vào Environment secrets rồi xóa bản ở Repository secrets. Chưa chuyển cũng không sao, lượt quét vẫn chạy như cũ.

(Tùy chọn, tự động hợp nhất) Settings → General → tick **Allow auto-merge**; Settings → Secrets and variables → Actions → tab **Variables** → thêm `RADAR_AUTOMERGE` = `true`. Khi đó mỗi PR của lượt quét tự merge khi check `test` đạt. Không đặt biến này thì bạn (hoặc tôi, khi bạn nhờ) bấm Merge.

## 2. Thử trước khi bật bảo vệ

Actions → *Radar scan* → *Run workflow*, bỏ chọn `dry_run`, `picks` = `1`. Kỳ vọng: bước *Commit digests, export and state* in một dòng JSON `{"status": "opened", ...}`, trong tab Pull requests có PR `radar: scan <ngày>`, và check **`test` tự chạy** trên PR đó (đó là bằng chứng token kích hoạt được CI). Nếu `test` không chạy, đừng bật bảo vệ.

## 3. Bật bảo vệ

Settings → Branches → Add branch ruleset / rule cho `main`:

- **Require a pull request before merging**; để trống *Require approvals* (nếu tick, bạn không tự duyệt được PR của chính mình).
- **Require status checks to pass before merging** → gõ `test` vào ô tìm và chọn nó; tick **Require branches to be up to date before merging**.
- **Do not allow bypassing the above settings** (tùy bạn).

## Sau khi bật: điều cần biết

- Mỗi lượt quét thành một PR. `state/seen.json` và `state/stars.json` cho lượt sau được đọc từ `main`, nên **PR của lượt trước phải được merge trước lượt kế**, nếu không bài bị viết lại và ảnh chụp số sao bị thiếu (có `RADAR_AUTOMERGE` thì việc này tự xảy ra).
- GitHub báo "branch is out of date" thì bấm **Update branch**; ở chế độ bắt buộc cập nhật, auto-merge sẽ **đứng chờ im lặng** cho tới lúc đó (không có gì tự cập nhật nhánh).
- Hai PR quét chưa merge sẽ **xung đột** ở `state/*.json` (mỗi lượt đều sửa `seen.json` và `stars.json`) và *Update branch* không gỡ được xung đột nội dung. PR mới tự ghi tên các PR quét cũ còn mở. Cách xử lý: merge PR cũ nhất trước; nếu PR mới vẫn xung đột thì đóng nó và chạy lại lượt quét (các repo của lượt bị đóng sẽ được xét lại).
- Nếu bước commit báo `pull request not opened` hoặc `branch-pushed`, kết quả vẫn nằm trên nhánh `radar/scan-...`: mở PR từ nhánh đó bằng tay.

## Rủi ro và những gì chưa kiểm được

- Token có quyền ghi nội dung của repo mạnh hơn token mặc định: giới hạn một repo, hạn ngắn, và **đặt trong Environment `radar` chỉ cho nhánh `main`** như ở bước 1. Nếu để ở Repository secrets, ai có quyền ghi vào repo đều có thể lấy nó bằng một nhánh chạy workflow thủ công.
- Đã kiểm bằng máy với git thật và GitHub giả: nhánh mới được đẩy, `main` không bị chạm, token không nằm trong argv hay URL, chạy lại không mở PR thứ hai, lỗi mở PR không làm mất kết quả, đường không-token giữ nguyên.
- **Chưa kiểm với GitHub thật**, nên đừng coi là chắc chắn:
  - tên và đủ của các quyền (**Contents**, **Pull requests**) theo giao diện GitHub lúc viết: hãy đối chiếu khi tạo token;
  - việc PR do token này mở có **kích hoạt CI** hay không (bước 2 ở trên chính là phép thử);
  - việc token fine-grained có gọi được thao tác GraphQL bật auto-merge hay không, và cài đặt *Allow auto-merge* của repo;
  - việc Environment `radar` với nhánh được phép là `main` có thật sự từ chối lần chạy ở nhánh khác (nên thử một lần sau khi cấu hình: bấm *Run workflow* ở một nhánh khác và thấy job bị chặn);
  - hành vi bên trong bản checkout thật của Actions (đã kiểm riêng rằng token được thêm vào chỉ gửi **một** tiêu đề xác thực, bằng một máy chủ cục bộ, nhưng chưa thử với `actions/checkout` thật).
- Lỗi của git có thể lặp lại một đoạn trả lời của máy chủ; token và dạng base64 của nó bị thay bằng `***` trước khi in.
