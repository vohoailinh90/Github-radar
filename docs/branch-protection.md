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

Rồi: repo → Settings → Secrets and variables → Actions → **New repository secret**, tên `RADAR_PR_TOKEN`, dán token. Token chỉ nằm trong secret; workflow chỉ đưa nó cho bước commit, qua biến môi trường.

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
- GitHub báo "branch is out of date" thì bấm **Update branch**; ở chế độ bắt buộc cập nhật, auto-merge sẽ đợi.
- Nếu bước commit báo `pull request not opened` hoặc `branch-pushed`, kết quả vẫn nằm trên nhánh `radar/scan-...`: mở PR từ nhánh đó bằng tay.

## Rủi ro và những gì chưa kiểm được

- Token có quyền ghi nội dung của repo mạnh hơn token mặc định. Giữ nó ở dạng secret của repo, giới hạn một repo, hạn ngắn. Muốn chặt hơn: đặt nó thành secret của một *Environment* chỉ cho nhánh `main` và thêm `environment:` vào job (chưa làm vì cần bạn tạo lại secret ở đó).
- Đã kiểm bằng máy với git thật và GitHub giả: nhánh mới được đẩy, `main` không bị chạm, token không nằm trong argv hay URL, chạy lại không mở PR thứ hai, lỗi mở PR không làm mất kết quả, đường không-token giữ nguyên.
- **Chưa kiểm với GitHub thật**: quyền của token, việc PR do token mở có kích hoạt CI, auto-merge. Bước 2 ở trên chính là phép thử đó.
