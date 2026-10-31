# Build Your Own X — bản đồ tự xây công nghệ

Report tổng quan tiếng Việt, 20 trang. Nội dung dựa trên README được ghim commit và một ví dụ gốc về database. Các lộ trình và đầu ra thực hành là gợi ý của người viết, không phải giáo trình chính thức.

- [PDF có mục lục nhảy trang](build-your-own-x.pdf). Moda báo một trang được xuất dạng ảnh; nội dung và liên kết vẫn đầy đủ.
- [PowerPoint có hyperlink](build-your-own-x.pptx).
- [Bản đọc HTML](report.html).
- [Phiếu chọn dự án](project-brief.md).
- [Canvas Moda](https://moda.app/canvas/4074b77f-9d96-457d-abde-1be20ada8693?source=agent).

## Mục lục

- [Repo này thực sự cung cấp gì?](#muc-03) — trang 3.
- [31 nhóm công nghệ / 01](#muc-04) — trang 4.
- [31 nhóm công nghệ / 02](#muc-05) — trang 5.
- [Chọn bài đầu tiên theo câu hỏi](#muc-06) — trang 6.
- [Một vòng học tạo ra hiểu biết](#muc-07) — trang 7.
- [Dữ liệu & quản lý phiên bản](#muc-08) — trang 8.
- [Web: server & browser](#muc-09) — trang 9.
- [Ngôn ngữ & công cụ lập trình](#muc-10) — trang 10.
- [Hệ thống & hạ tầng](#muc-11) — trang 11.
- [AI, neural network & nhận dạng](#muc-12) — trang 12.
- [Đồ họa, game & mô phỏng](#muc-13) — trang 13.
- [Giao diện & công cụ cá nhân](#muc-14) — trang 14.
- [Ví dụ thật: bước đầu làm database](#muc-15) — trang 15.
- [Lộ trình gợi ý theo nền tảng](#muc-16) — trang 16.
- [Tự kiểm tra: hiểu hay mới làm theo?](#muc-17) — trang 17.
- [Những điều dễ hiểu nhầm](#muc-18) — trang 18.
- [Phiếu bắt đầu dự án của bạn](#muc-19) — trang 19.
- [Nguồn & phạm vi kiểm chứng](#muc-20) — trang 20.

<a name="muc-03"></a>
## Repo này thực sự cung cấp gì?

[Đọc phần này trên GitHub Radar](https://github.com/vohoailinh90/Github-radar/blob/main/docs/reports/build-your-own-x/report.md#muc-03) · [Mở tài liệu gốc](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md)

build-your-own-x tập hợp hướng dẫn từng bước để tái tạo các công nghệ quen thuộc. Bạn dùng README như một mục lục: chọn thứ muốn xây, chọn ngôn ngữ, rồi đi tới tài liệu bên ngoài. Repo không phải một ứng dụng duy nhất để clone về và chạy. [S1]


### Triết lý học tập

Bạn hiểu sâu hơn khi phải tự biến khái niệm thành một phiên bản có thể quan sát và thay đổi. Việc học nằm ở tài liệu đích và những quyết định khi bạn triển khai.

### Cấu trúc đã kiểm tra

Tại commit nguồn được ghim, phần Tutorials có 31 nhóm, gồm cả Distributed Systems và Uncategorized. Bản đồ hai trang sau phản ánh các tiêu đề thực tế trong phần này.

### Một mục hướng dẫn cho biết gì?

Tên thường đi kèm ngôn ngữ và liên kết tới bài viết, sách, video hoặc dự án. Các tài liệu có phạm vi, yêu cầu đầu vào và độ mới khác nhau.

### Giới hạn của bản tổng quan

Report giải thích cách chọn và học, chưa chạy thử toàn bộ hướng dẫn. Các gợi ý đầu ra và lộ trình là đề xuất của người viết, không phải chương trình chính thức của repo.

<a name="muc-04"></a>
## 31 nhóm công nghệ / 01

Tên nhóm dẫn tới mục README, ví dụ dẫn tới hướng dẫn được liệt kê. Không phải bảng xếp hạng chất lượng hoặc độ khó. [S1]

| Nhóm | Chủ đề | Ví dụ trong README |
| --- | --- | --- |
| [Distributed Systems](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-distributed-systems) | Hệ thống phân tán và luồng sự kiện. | [Java: Building Your Own Kafka-like System From Scratch: A Step-by-Step Guide](https://github.com/buildthingsuseful/build-your-own-kafka) |
| [3D Renderer](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-3d-renderer) | Biến mô hình thành hình ảnh. | [C++: Introduction to Ray Tracing: a Simple Method for Creating 3D Images](https://www.scratchapixel.com/lessons/3d-basic-rendering/introduction-to-ray-tracing/how-does-it-work) |
| [AI Model](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-ai-model) | Các hướng xây mô hình AI. | [Python: A Large Language Model (LLM)](https://github.com/rasbt/LLMs-from-scratch) |
| [Augmented Reality](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-augmented-reality) | Kết hợp nội dung ảo với hình ảnh thực. | [C#: How To: Augmented Reality App Tutorial for Beginners with Vuforia and Unity 3D](https://www.youtube.com/watch?v=uXNjNcqW4kY) |
| [BitTorrent Client](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-bittorrent-client) | Giao tiếp tải dữ liệu theo giao thức BitTorrent. | [C#: Building a BitTorrent client from scratch in C#](https://www.seanjoflynn.com/research/bittorrent.html) |
| [Blockchain / Cryptocurrency](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-blockchain--cryptocurrency) | Khám phá cơ chế blockchain/tiền mã hóa. | [ATS: Functional Blockchain](https://beta.observablehq.com/@galletti94/functional-blockchain) |
| [Bot](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-bot) | Tự động hóa tương tác hoặc tác vụ. | [Haskell: Roll your own IRC bot](https://wiki.haskell.org/Roll_your_own_IRC_bot) |
| [Command-Line Tool](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-command-line-tool) | Công cụ chạy từ dòng lệnh. | [Go: Visualize your local git contributions with Go](https://flaviocopes.com/go-git-contributions/) |
| [Database](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-database) | Tổ chức, lưu và truy xuất dữ liệu. | [C: Let's Build a Simple Database](https://cstack.github.io/db_tutorial/) |
| [Docker](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-docker) | Tìm hiểu một phần cơ chế container. | [C: Linux containers in 500 lines of code](https://blog.lizzie.io/linux-containers-in-500-loc.html) |
| [Emulator / Virtual Machine](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-emulator--virtual-machine) | Mô phỏng máy hoặc môi trường thực thi. | [C: Home-grown bytecode interpreters](https://medium.com/bumble-tech/home-grown-bytecode-interpreters-51e12d59b25c) |
| [Front-end Framework / Library](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-front-end-framework--library) | Khám phá cơ chế framework giao diện. | [JavaScript: WTF is JSX (Let's Build a JSX Renderer)](https://jasonformat.com/wtf-is-jsx/) |
| [Game](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-game) | Xây trò chơi và tương tác. | [C: Handmade Hero](https://handmadehero.org/) |
| [Git](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-git) | Hiểu cơ chế quản lý phiên bản. | [Haskell: Reimplementing “git clone” in Haskell from the bottom up](http://stefan.saasen.me/articles/git-clone-in-haskell-from-the-bottom-up/) |
| [Memory Allocator](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-memory-allocator) | Tìm hiểu cách cấp phát bộ nhớ. | [C: Malloc is not magic -- Implementing your own memory allocator](https://medium.com/p/e0354e914402) |
| [Network Stack](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-network-stack) | Khám phá các lớp giao tiếp mạng. | [C: Beej's Guide to Network Programming](http://beej.us/guide/bgnet/) |

<a name="muc-05"></a>
## 31 nhóm công nghệ / 02

Tên nhóm dẫn tới mục README, ví dụ dẫn tới hướng dẫn được liệt kê. Không phải bảng xếp hạng chất lượng hoặc độ khó. [S1]

| Nhóm | Chủ đề | Ví dụ trong README |
| --- | --- | --- |
| [Neural Network](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-neural-network) | Xây và quan sát mạng neural. | [C#: Neural Network OCR](https://www.codeproject.com/Articles/11285/Neural-Network-OCR) |
| [Operating System](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-operating-system) | Tìm hiểu thành phần hệ điều hành. | [Assembly: Writing a Tiny x86 Bootloader](http://joebergeron.io/posts/post_two.html) |
| [Physics Engine](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-physics-engine) | Mô phỏng trạng thái và tương tác vật lý. | [C: Video Game Physics Tutorial](https://www.toptal.com/game/video-game-physics-part-i-an-introduction-to-rigid-body-dynamics) |
| [Processor](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-processor) | Khám phá một bộ xử lý. | [Verilog: From Blinker to RISC-V](https://github.com/BrunoLevy/learn-fpga/tree/master/FemtoRV/TUTORIALS/FROM_BLINKER_TO_RISCV) |
| [Programming Language](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-programming-language) | Đọc và thực thi ngôn ngữ lập trình. | [(any): mal - Make a Lisp](https://github.com/kanaka/mal#mal---make-a-lisp) |
| [Regex Engine](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-regex-engine) | So khớp mẫu văn bản. | [C: A Regular Expression Matcher](https://www.cs.princeton.edu/courses/archive/spr09/cos333/beautiful.html) |
| [Search Engine](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-search-engine) | Tổ chức và tìm kiếm thông tin. | [CSS: A search engine in CSS](https://stories.algolia.com/a-search-engine-in-css-b5ec4e902e97) |
| [Shell](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-shell) | Nhận và xử lý dòng lệnh. | [C: Tutorial - Write a Shell in C](https://brennan.io/2015/01/16/write-a-shell-in-c/) |
| [Template Engine](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-template-engine) | Sinh nội dung từ mẫu. | [JavaScript: JavaScript template engine in just 20 lines](http://krasimirtsonev.com/blog/article/Javascript-template-engine-in-just-20-line) |
| [Text Editor](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-text-editor) | Xây công cụ soạn thảo văn bản. | [C: Build Your Own Text Editor](https://viewsourcecode.org/snaptoken/kilo/) |
| [Visual Recognition System](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-visual-recognition-system) | Xử lý bài toán nhận dạng hình ảnh. | [Python: Developing a License Plate Recognition System with Machine Learning in Python](https://medium.com/devcenter/developing-a-license-plate-recognition-system-with-machine-learning-in-python-787833569ccd) |
| [Voxel Engine](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-voxel-engine) | Xây môi trường dựng hình theo voxel. | [C++: Let's Make a Voxel Engine](https://sites.google.com/site/letsmakeavoxelengine/home) |
| [Web Browser](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-web-browser) | Khám phá thành phần trình duyệt. | [Rust: Let's build a browser engine](https://limpet.net/mbrubeck/2014/08/08/toy-layout-engine-1.html) |
| [Web Server](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-web-server) | Nhận yêu cầu và phục vụ nội dung web. | [C#: Writing a Web Server from Scratch](https://www.codeproject.com/Articles/859108/Writing-a-Web-Server-from-Scratch) |
| [Uncategorized](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#uncategorized) | Các dự án khác, đọc theo mục tiêu riêng. | [(any): From NAND to Tetris: Building a Modern Computer From First Principles](http://nand2tetris.org/) |

<a name="muc-06"></a>
## Chọn bài đầu tiên theo câu hỏi

[Đọc phần này trên GitHub Radar](https://github.com/vohoailinh90/Github-radar/blob/main/docs/reports/build-your-own-x/report.md#muc-06) · [Mở tài liệu gốc](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md)

Đừng bắt đầu bằng công nghệ có tên lớn nhất. Hãy chọn một câu hỏi bạn đang thật sự muốn hiểu, rồi giới hạn thành một sản phẩm nhỏ. Bảng lựa chọn dưới đây là gợi ý của người viết, dựa trên các nhóm có trong README. [S1]


### Tôi muốn thấy kết quả sớm

Cân nhắc Command-Line Tool, Template Engine hoặc một Web Server nhỏ bằng ngôn ngữ đã quen. Đọc yêu cầu của chính tutorial trước khi chọn.

### Tôi thường dùng công cụ nhưng chưa hiểu nó

Chọn Database, Git, Shell hoặc Front-end Framework / Library tương ứng với thứ bạn đã dùng. Kinh nghiệm sử dụng giúp bạn đặt câu hỏi cụ thể hơn.

### Tôi thích nền tảng hệ thống

Khám phá Docker, Network Stack, Operating System, Memory Allocator hoặc Emulator. Xác minh kiến thức hệ điều hành, công cụ và nền tảng mà tài liệu yêu cầu.

### Tôi muốn học AI hoặc đồ họa

Chọn bài có phạm vi nhỏ trong Neural Network, AI Model hoặc 3D Renderer. Kiểm tra yêu cầu toán, dữ liệu, thư viện và tài nguyên tính toán ở tài liệu đích.

<a name="muc-07"></a>
## Một vòng học tạo ra hiểu biết

[Đọc phần này trên GitHub Radar](https://github.com/vohoailinh90/Github-radar/blob/main/docs/reports/build-your-own-x/report.md#muc-07) · [Mở tài liệu gốc](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md)

Vòng học đề xuất: đặt câu hỏi → chọn nguồn → xây phiên bản nhỏ → thay đổi → giải thích lại. Đích đến là vừa chạy được vừa nói rõ vì sao chương trình hoạt động, không chỉ gõ lại mã mẫu. [S1]


### 01 / Chốt điều muốn hiểu

Ví dụ của người viết: “Một web server đọc yêu cầu và gửi phản hồi bằng cách nào?”. Chọn một câu hỏi thay vì học mọi phần cùng lúc.

### 02 / Kiểm tra tutorial

Đọc mục tiêu, ngôn ngữ, công cụ, phiên bản và điểm kết thúc. Ghi điều bạn đã biết và chỗ cần bổ sung trước.

### 03 / Xây và kiểm tra từng phần

Làm một mốc nhỏ có đầu vào và đầu ra rõ. Lưu kết quả đúng cùng một trường hợp lỗi để hiểu giới hạn.

### 04 / Tự sửa rồi kể lại

Thay một hành vi nhỏ và dự đoán kết quả trước khi chạy. Sau đó vẽ đầu vào → xử lý → đầu ra và ghi phần chưa hỗ trợ.

<a name="muc-08"></a>
## Dữ liệu & quản lý phiên bản

[Đọc phần này trên GitHub Radar](https://github.com/vohoailinh90/Github-radar/blob/main/docs/reports/build-your-own-x/report.md#muc-08) · [Mở tài liệu gốc](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-database)

Hai nhóm Database và Git phù hợp khi bạn muốn hiểu cách phần mềm lưu thông tin hoặc biểu diễn lịch sử thay đổi. README có nhiều cách tiếp cận và ngôn ngữ; hãy chọn phạm vi theo điều bạn muốn giải thích được. [S1]


### Database: câu hỏi nên mang theo

Dữ liệu được tổ chức ở đâu? Chương trình tìm lại bản ghi như thế nào? Khi tắt và mở lại, những gì còn tồn tại? Đây là câu hỏi học tập, không phải tính năng được mọi tutorial cam kết.

### Git: câu hỏi nên mang theo

Một phiên bản được biểu diễn ra sao? Các lần thay đổi liên hệ thế nào? Chọn tài liệu theo thao tác mà nó thật sự triển khai, thay vì coi bản nhỏ là Git đầy đủ.

### Đầu ra gợi ý

Tự vẽ mô hình lưu trữ của phần đã làm; tạo một dữ liệu hoặc thay đổi mới và dự đoán kết quả. Ghi rõ tính năng đang thiếu.

### Chuẩn bị

Ngôn ngữ lập trình quen thuộc, khả năng đọc/ghi tệp theo yêu cầu bài và cách quan sát lỗi. Nhu cầu cụ thể phụ thuộc tutorial được chọn.

- [Hướng dẫn trực tiếp: C: Let's Build a Simple Database](https://cstack.github.io/db_tutorial/)

- [Hướng dẫn trực tiếp: Python: ugit: Learn Git Internals by Building Git Yourself](https://www.leshenko.net/p/ugit/)

<a name="muc-09"></a>
## Web: server & browser

[Đọc phần này trên GitHub Radar](https://github.com/vohoailinh90/Github-radar/blob/main/docs/reports/build-your-own-x/report.md#muc-09) · [Mở tài liệu gốc](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-web-server)

Web Server và Web Browser là hai góc nhìn khác nhau: một bên phục vụ nội dung, một bên tiếp nhận và trình bày nội dung. Dùng chúng để đặt câu hỏi về đường đi của một tương tác web. [S1]


### Server: đi theo yêu cầu–phản hồi

Gợi ý học: xác định dữ liệu đầu vào, đoạn xử lý và phản hồi đầu ra. Bắt đầu bằng một yêu cầu đơn giản và một đường dẫn.

### Browser: đi theo nội dung–hiển thị

Gợi ý học: quan sát cách một thành phần của trình duyệt biến nội dung thành kết quả nhìn thấy được. Kiểm tra tutorial xây phần nào, không suy ra nó hỗ trợ toàn bộ chuẩn web.

### Đầu ra gợi ý

Một phản hồi hoặc ví dụ hiển thị nhỏ có thể thay đổi; kèm sơ đồ các bước và một tình huống chưa xử lý.

### Điểm cần phân biệt

Tự viết server, dùng một framework để dựng API và tự xây browser engine là các bài học khác phạm vi. Đọc mục tiêu nguồn trước khi so sánh.

- [Hướng dẫn trực tiếp: Python: Let’s Build A Web Server.](https://ruslanspivak.com/lsbaws-part1/)

- [Hướng dẫn trực tiếp: Python: Browser Engineering](https://browser.engineering)

<a name="muc-10"></a>
## Ngôn ngữ & công cụ lập trình

[Đọc phần này trên GitHub Radar](https://github.com/vohoailinh90/Github-radar/blob/main/docs/reports/build-your-own-x/report.md#muc-10) · [Mở tài liệu gốc](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-programming-language)

Programming Language, Regex Engine, Shell và Template Engine cho bạn các hướng khám phá cách phần mềm đọc và xử lý ký hiệu hoặc lệnh. Chúng là những dự án khác nhau, không phải một bài tập chung. [S1]


### Compiler và interpreter

Trình biên dịch và trình thông dịch là hai thuật ngữ thường gặp khi tìm hiểu ngôn ngữ. Hãy theo dõi đầu vào mã nguồn và cách tutorial tạo ra hành vi thực thi.

### Regex, template và shell

Bạn có thể chọn một cơ chế hẹp để học: so khớp mẫu, thay chỗ trống trong nội dung, hoặc xử lý một dòng lệnh. Xác định đúng quy tắc mà phiên bản nhỏ hỗ trợ.

### Đầu ra gợi ý

Một biểu thức, một mẫu hoặc một lệnh chạy được; một trường hợp không hợp lệ; và lời giải thích cách chương trình phân biệt chúng.

### Cách tránh quá tải

Không thêm nhiều cú pháp hoặc tính năng trước khi tự giải thích được ví dụ đầu tiên. Khi mắc kẹt, tách phần đọc đầu vào khỏi phần thực thi.

- [Hướng dẫn trực tiếp: JavaScript: The Super Tiny Compiler](https://github.com/jamiebuilds/the-super-tiny-compiler)

- [Hướng dẫn trực tiếp: C: Tutorial - Write a Shell in C](https://brennan.io/2015/01/16/write-a-shell-in-c/)

<a name="muc-11"></a>
## Hệ thống & hạ tầng

[Đọc phần này trên GitHub Radar](https://github.com/vohoailinh90/Github-radar/blob/main/docs/reports/build-your-own-x/report.md#muc-11) · [Mở tài liệu gốc](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-docker)

Docker, Operating System, Network Stack, Memory Allocator, Emulator và Distributed Systems mở ra các dự án về nền tảng vận hành. Tên nhóm rộng, nhưng từng hướng dẫn có phạm vi và điều kiện rất cụ thể. [S1]


### Chọn một tầng để hiểu

Gợi ý: cơ chế cô lập, một bước giao tiếp mạng, cách cấp phát bộ nhớ hoặc một tập lệnh giả lập. Đừng gom mọi chủ đề hệ thống thành một dự án đầu tiên.

### Đọc điều kiện môi trường

Kiểm tra hệ điều hành, kiến trúc máy, quyền chạy và công cụ mà tutorial yêu cầu. Một bài dành cho nền tảng này không tự áp dụng nguyên xi cho nền tảng khác.

### Đầu ra gợi ý

Một cơ chế được minh họa bằng đầu vào nhỏ, kèm kết quả quan sát và sơ đồ tầng liên quan. Chỉ mở rộng sau khi hiểu phần đầu.

### Giới hạn cần ghi

Bản học tập không tự có độ tin cậy, tính tương thích hoặc phạm vi như sản phẩm thật. Đánh giá việc sử dụng thực tế tách khỏi thành công của bài học.

- [Hướng dẫn trực tiếp: Go: Building a container from scratch in Go](https://www.youtube.com/watch?v=8fi7uSYlOdc)

- [Hướng dẫn trực tiếp: Java: Building Your Own Kafka-like System From Scratch: A Step-by-Step Guide](https://github.com/buildthingsuseful/build-your-own-kafka)

<a name="muc-12"></a>
## AI, neural network & nhận dạng

[Đọc phần này trên GitHub Radar](https://github.com/vohoailinh90/Github-radar/blob/main/docs/reports/build-your-own-x/report.md#muc-12) · [Mở tài liệu gốc](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-ai-model)

README có nhóm AI Model, Neural Network và Visual Recognition System. Có các liên kết về LLM, diffusion, tìm kiếm tài liệu và mạng neural; lựa chọn phụ thuộc vào điều bạn muốn hiểu và nền tảng đang có. [S1]


### Đừng chọn chỉ vì nhãn AI

Viết rõ câu hỏi: muốn hiểu phép tính trong mạng nhỏ, quy trình xử lý văn bản hay một hệ thống tìm kiếm tài liệu? Những mục tiêu đó có đầu ra khác nhau.

### Điều cần kiểm tra ở nguồn

Ngôn ngữ, toán nền, dữ liệu, thư viện và phần cứng được yêu cầu. Không suy ra rằng mọi bài “from scratch” đều không dùng thư viện.

### Đầu ra gợi ý

Một ví dụ nhỏ có thể giải thích đầu vào, bước xử lý và đầu ra; ghi lại dữ liệu và điều kiện chạy để kết quả có thể được xem lại.

### Chọn theo phạm vi

Nếu mới bắt đầu, ưu tiên bài có giả định và ví dụ cụ thể phù hợp kiến thức hiện tại. Report không xếp hạng độ khó chính thức của các tài liệu.

- [Hướng dẫn trực tiếp: Python: A Large Language Model (LLM)](https://github.com/rasbt/LLMs-from-scratch)

- [Hướng dẫn trực tiếp: Python: Implement a Neural Network from Scratch](https://victorzhou.com/blog/intro-to-neural-networks/)

<a name="muc-13"></a>
## Đồ họa, game & mô phỏng

[Đọc phần này trên GitHub Radar](https://github.com/vohoailinh90/Github-radar/blob/main/docs/reports/build-your-own-x/report.md#muc-13) · [Mở tài liệu gốc](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-3d-renderer)

3D Renderer, Game, Physics Engine và Voxel Engine cho phép nhìn thấy kết quả của thuật toán. Kết quả trực quan là lợi thế, nhưng vẫn cần phân biệt phần cơ chế mà bạn đang thực sự tự xây. [S1]


### Đặt câu hỏi theo hình ảnh

Ví dụ của người viết: một điểm trong mô hình trở thành điểm ảnh như thế nào, hoặc một thay đổi trong trạng thái làm vật thể chuyển động ra sao?

### Chọn một sản phẩm nhỏ

Có thể là một cảnh đơn giản, một hình được dựng hoặc một luật tương tác. Hãy dùng mục tiêu mà tutorial thật sự hỗ trợ để chốt bài.

### Đầu ra gợi ý

Lưu ảnh hoặc đoạn mô tả kết quả trước/sau một thay đổi. Dự đoán thay đổi trước khi chạy, rồi so sánh điều quan sát được.

### Đừng chỉ nhìn hình đẹp

Thử giải thích dữ liệu và các bước biến đổi. Nếu chỉ chạy lại ví dụ mà không hiểu được một thay đổi nhỏ, quay lại phần cơ chế.

- [Hướng dẫn trực tiếp: C++: Ray Tracing in One Weekend](https://raytracing.github.io/books/RayTracingInOneWeekend.html)

- [Hướng dẫn trực tiếp: C++: How OpenGL works: software rendering in 500 lines of code](https://github.com/ssloy/tinyrenderer/wiki)

<a name="muc-14"></a>
## Giao diện & công cụ cá nhân

[Đọc phần này trên GitHub Radar](https://github.com/vohoailinh90/Github-radar/blob/main/docs/reports/build-your-own-x/report.md#muc-14) · [Mở tài liệu gốc](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md#build-your-own-front-end-framework--library)

Những nhóm như Front-end Framework / Library, Text Editor, Command-Line Tool, Bot và Template Engine gắn việc học với công cụ dễ hình dung. Bạn có thể chọn bài gần công việc hằng ngày để có câu hỏi cụ thể hơn. [S1]


### Dùng trải nghiệm sẵn có

Nếu thường dùng framework giao diện, hãy hỏi nó biến trạng thái thành kết quả hiển thị thế nào. Nếu dùng công cụ dòng lệnh, hãy hỏi cách nó nhận và xử lý tham số.

### Giới hạn một hành vi

Ví dụ của người viết: chỉ xử lý một loại đầu vào, một màn hình hoặc một thao tác sửa văn bản. Đừng đặt mục tiêu thay thế toàn bộ công cụ đang dùng.

### Đầu ra gợi ý

Một tác vụ nhỏ có thể làm lại và một thay đổi do chính bạn bổ sung. Ghi điều kiện hoạt động cùng những trường hợp chưa hỗ trợ.

### Đọc tiếp khi cần

Các nhóm còn lại, như BitTorrent, AR hoặc blockchain, vẫn có trong bản đồ. Hãy dùng cùng phương pháp chọn phạm vi và kiểm tra điều kiện đầu vào.

- [Hướng dẫn trực tiếp: JavaScript: A DIY guide to build your own React](https://github.com/hexacta/didact)

- [Hướng dẫn trực tiếp: C: Build Your Own Text Editor](https://viewsourcecode.org/snaptoken/kilo/)

<a name="muc-15"></a>
## Ví dụ thật: bước đầu làm database

[Đọc phần này trên GitHub Radar](https://github.com/vohoailinh90/Github-radar/blob/main/docs/reports/build-your-own-x/report.md#muc-15) · [Mở tài liệu gốc](https://github.com/cstack/db_tutorial/blob/60b50c5b7be787a4aaa1e50ab8a90c6cabb75159/_parts/part1.md)

Phần 1 của cstack/db_tutorial chưa xây một cơ sở dữ liệu hoàn chỉnh. Nó bắt đầu bằng REPL: lặp việc đọc đầu vào, xử lý và in kết quả. Đây là ví dụ rõ về cách một dự án lớn có thể bắt đầu từ hành vi rất nhỏ. [S2]


### Nguồn thực sự làm gì?

Chương trình in “db > ”, đọc một dòng; nhận .exit thì giải phóng bộ nhớ và thoát. Lệnh chưa nhận diện được sẽ được báo lại rồi tiếp tục vòng lặp.

### Một kiểm tra được nguồn minh họa

Mở chương trình bằng ./db, nhập .tables: chương trình báo Unrecognized command '.tables'. Nhập .exit: chương trình kết thúc. Đây là hành vi được minh họa trong tài liệu, không phải SQL đã chạy được.

### Điều kiện cần xem trước

Bài dùng C, cấu trúc InputBuffer và getline(). Kiểm tra môi trường của bạn theo nguồn; phần này chưa nhằm hỗ trợ nhiều nền tảng.

### Tự kiểm tra điều đã hiểu

Bạn có giải thích được vì sao cần vòng lặp, ký tự xuống dòng được xử lý ở đâu và bộ nhớ được giải phóng khi nào? Chỉ học phần tiếp theo sau khi nắm những điểm này.

- [Hướng dẫn trực tiếp: Cstack — Part 1: Introduction and Setting up the REPL](https://github.com/cstack/db_tutorial/blob/60b50c5b7be787a4aaa1e50ab8a90c6cabb75159/_parts/part1.md)

- [Hướng dẫn trực tiếp: Trang tutorial được BYOX giới thiệu](https://cstack.github.io/db_tutorial/)

<a name="muc-16"></a>
## Lộ trình gợi ý theo nền tảng

[Đọc phần này trên GitHub Radar](https://github.com/vohoailinh90/Github-radar/blob/main/docs/reports/build-your-own-x/report.md#muc-16) · [Mở tài liệu gốc](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md)

Các lộ trình dưới đây do người viết đề xuất để giảm việc phải học nhiều thứ mới cùng lúc. Chúng không phải thứ tự bắt buộc hoặc xếp hạng độ khó do repo công bố. [S1]


### Bạn đã quen Python

Xem các lựa chọn Python ở Web Server, Git hoặc Database. Chọn một tutorial có yêu cầu khớp với điều bạn đã biết, rồi hoàn thành một mốc nhỏ.

### Bạn đã quen JavaScript

Khám phá Template Engine, Front-end Framework / Library hoặc một compiler nhỏ bằng JavaScript. Đặt mục tiêu giải thích được một cơ chế.

### Bạn đã học C/C++ hoặc hệ thống

Cân nhắc Text Editor, Shell, Memory Allocator hoặc bài Database bằng C. Xác minh yêu cầu môi trường của từng nguồn trước.

### Bạn chưa tự viết chương trình nhỏ

Bổ sung nền tảng ngôn ngữ, hàm, vòng lặp và cách chạy chương trình trước. Sau đó chọn bài hẹp, có đầu vào/đầu ra rõ, thay vì bắt đầu bằng OS hay AI model lớn.

<a name="muc-17"></a>
## Tự kiểm tra: hiểu hay mới làm theo?

[Đọc phần này trên GitHub Radar](https://github.com/vohoailinh90/Github-radar/blob/main/docs/reports/build-your-own-x/report.md#muc-17) · [Mở tài liệu gốc](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md)

Một chương trình chạy được là tín hiệu tốt, nhưng chưa đủ để biết bạn đã hiểu cơ chế. Dùng các câu hỏi dưới đây để tự đánh giá bài thực hành. Đây là rubric học tập của người viết. [S1]


### 1 / Giải thích

Mô tả đầu vào → các bước xử lý → đầu ra bằng lời của bạn. Nêu rõ phần mã hoặc dữ liệu tương ứng trong phiên bản đã xây.

### 2 / Dự đoán

Trước khi thay một đầu vào, hãy viết điều bạn mong đợi. So sánh dự đoán với kết quả và giải thích khi chúng khác nhau.

### 3 / Thay đổi

Bổ sung một hành vi nhỏ mà không chép nguyên lời giải. Nếu mắc kẹt, xác định chính xác điều chưa hiểu và đọc lại phần liên quan.

### 4 / Biết giới hạn

Nêu ít nhất một tình huống phiên bản chưa xử lý. Tách rõ tính năng đã làm, tính năng mới đọc và tính năng chưa thử.

<a name="muc-18"></a>
## Những điều dễ hiểu nhầm

[Đọc phần này trên GitHub Radar](https://github.com/vohoailinh90/Github-radar/blob/main/docs/reports/build-your-own-x/report.md#muc-18) · [Mở tài liệu gốc](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md)

Tuyển tập hướng dẫn mở ra nhiều cách học, nhưng các tài liệu đích có tuổi đời, phạm vi và điều kiện riêng. Đọc đúng vai trò của repo sẽ giúp bạn đặt kỳ vọng phù hợp. [S1]


### Clone repo ≠ tải mọi khóa học

Clone lấy nội dung của repo tổng. Bài viết, sách và mã được liên kết có thể nằm ở những nơi khác.

### From scratch ≠ không dùng gì có sẵn

Mỗi nguồn chọn một mức nền tảng khác nhau. Đọc giả định, thư viện và thành phần mà bài yêu cầu thay vì suy ra từ tiêu đề.

### Tất cả liên kết ≠ cùng điều kiện truy cập

Hãy kiểm tra nguồn còn truy cập được không, có yêu cầu tài khoản hoặc phần nội dung trả phí không. Report không xác nhận toàn bộ liên kết đều miễn phí hoặc còn hoạt động.

### Bản học tập ≠ sản phẩm sẵn sàng triển khai

Giấy phép, tính tương thích, xử lý lỗi và độ đầy đủ tính năng cần được đánh giá riêng nếu muốn dùng trong dự án thật.

<a name="muc-19"></a>
## Phiếu bắt đầu dự án của bạn

[Đọc phần này trên GitHub Radar](https://github.com/vohoailinh90/Github-radar/blob/main/docs/reports/build-your-own-x/report.md#muc-19) · [Mở tài liệu gốc](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md)

Dùng phiếu này để chuyển từ đọc tổng quan sang một lần thực hành có mục tiêu. Có bản Markdown đi kèm trong repo để bạn tự điền. Các lựa chọn dưới đây là gợi ý của người viết.


### Câu hỏi tôi muốn trả lời

Viết một câu: “Tôi muốn hiểu … bằng cách tự xây …”. Chọn đúng một nhóm và một hướng dẫn chính để bắt đầu.

### Nguồn và điều kiện đầu vào

Ghi URL gốc, ngôn ngữ, môi trường, kiến thức đang có và điều cần bổ sung. Chưa xác minh được mục nào thì ghi rõ.

### Phiên bản nhỏ nhất

Chốt một hành vi có đầu vào/đầu ra quan sát được. Ghi một mốc kiểm tra và một tình huống lỗi cần xem.

### Điều kiện hoàn thành

Tôi chạy được mốc nhỏ, tự thay đổi được một phần, giải thích được cơ chế và biết giới hạn. Sau đó mới quyết định mở rộng hay chuyển chủ đề.

<a name="muc-20"></a>
## Nguồn & phạm vi kiểm chứng

[Đọc phần này trên GitHub Radar](https://github.com/vohoailinh90/Github-radar/blob/main/docs/reports/build-your-own-x/report.md#muc-20) · [Mở tài liệu gốc](https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md)

Nguồn đọc ngày 24/10/2026. Chưa chạy thử toàn bộ tutorial hoặc xác minh mọi tài nguyên đích còn hoạt động. Các mục tiêu học và lộ trình là đề xuất của người viết.

- [S1] CodeCrafters — build-your-own-x / README, https://github.com/codecrafters-io/build-your-own-x/blob/aa17439b62f384511a5561ce308e9598b94d8989/README.md
- [S2] Cstack — db_tutorial / Part 1, https://github.com/cstack/db_tutorial/blob/60b50c5b7be787a4aaa1e50ab8a90c6cabb75159/_parts/part1.md
