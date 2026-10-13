# USaD Workspace

USaD hiện có frontend tĩnh gọn theo theme Pixel Dark và backend FastAPI với
auth/project metadata cùng sandbox vertical slice fail-closed. UI không hiển
thị số liệu hoặc hoạt động mẫu như dữ liệu thật.

## Mở frontend

Trong VS Code chọn **Tasks: Run Task → Web-Linux static preview** rồi mở
`http://localhost:4173/` (forward port 4173 nếu VS Code chưa tự động forward).
Task phục vụ ba asset frontend từ `/workspace` và proxy `/api/v1/*` đến
`host.docker.internal:8000`; không expose các file khác trong workspace.

Dashboard đọc health/capabilities trực tiếp. Workspace gọi login và
project/workspace metadata API; token chỉ được giữ trong memory của tab. AI
Chat, terminal/logs, memory và tasks hiển thị trạng thái chưa tích hợp, không
gửi yêu cầu hoặc giả lập kết quả. Sandbox vẫn fail-closed.

## Backend API

FastAPI backend ở `backend/app` hiện có health check, đăng nhập/tài khoản,
endpoint capabilities chỉ đọc cho sandbox, cùng API projects/workspaces có
xác thực và truy vấn MariaDB. Frontend hiện chưa gọi các API này. Cấu hình
Compose yêu cầu `.env`; không commit file này hoặc bí mật thật. Preview có thể
đọc được API backend qua host gateway; điều đó không đồng nghĩa API health kiểm
tra database readiness.

### Môi trường Compose riêng cho mỗi thành viên

Mỗi thành viên clone repository vào thư mục riêng, sao chép `.env.example`
thành `.env`, thay placeholder bằng giá trị local riêng rồi dùng một Compose
project name duy nhất, viết thường, cho môi trường đó:

```powershell
Copy-Item .env.example .env
# Sửa .env cục bộ: đặt mật khẩu MariaDB/JWT/admin riêng và đồng bộ DATABASE_URL.
docker compose -p usad-dev-alice --env-file .env config --quiet
docker compose -p usad-dev-alice --env-file .env up -d --build
docker compose -p usad-dev-alice --env-file .env ps
```

Thay `alice` bằng một mã thành viên riêng. Compose sẽ dùng tên project này
để phân tách network và named volume; không dùng cùng tên project ở hai môi
trường nếu cần database độc lập. Port host hiện được cố định ở `8000` và
`8081`, nên không thể chạy đồng thời nhiều checkout của cấu hình này trên
cùng một máy nếu chưa chọn port khác. `mariadb` không publish port ra host.

Compose tạo database theo `MARIADB_DATABASE`, nhưng hiện không tự áp dụng
`database/usad_schema.sql` và không tự chạy `backend.app.init_admin`. API
projects/auth vì vậy cần schema và tài khoản được thiết lập riêng trước khi
dùng; chỉ áp dụng DDL cho database development mới, đã xác minh là rỗng.
Không trỏ cấu hình local tới database dùng chung/production. Lệnh `up` ở trên
tạo/cập nhật container và volume cho project name đã chọn; không chạy nó với
project name đang có dữ liệu nếu chưa xác minh trạng thái.

### Chạy backend trực tiếp trên host (không dùng Compose)

Cách dưới đây chỉ chạy backend trên host; cần tự cung cấp các biến môi trường
phù hợp, gồm `JWT_SECRET` và `DATABASE_URL` tới database có thể truy cập từ
host. MariaDB trong Compose hiện không publish port ra host. Cần Python 3.11
trở lên:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Kiểm tra API trong cửa sổ PowerShell khác:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/sandboxes/capabilities
```

Chạy unit tests từ thư mục gốc:

```powershell
$env:JWT_SECRET = [guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")
.\.venv\Scripts\python.exe -m unittest backend.tests.test_api local_agent.tests.test_sandbox_policy
```

Secret ngẫu nhiên trong lệnh trên chỉ dành cho process test hiện tại; nó không
được ghi vào file hay dùng làm cấu hình deployment.

`/api/v1/health` chỉ xác nhận API process còn phục vụ, không xác nhận DB sẵn
sàng. Sandbox provider mặc định fail-closed; không có lệnh nào được thực thi.
Không bind `0.0.0.0` hoặc đưa API ra Internet nếu chưa có triển khai bảo mật
được xem xét. Chưa có E2E runner. Xem [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md),
[docs/SECURITY.md](docs/SECURITY.md), [docs/API.md](docs/API.md) và
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) trước khi nối runtime.

### Dev Container

`.devcontainer/devcontainer.json` ưu tiên image local
`usad-dev-container-test:latest`. Nếu image đó chưa có trên máy thành viên mới,
hãy build image với tag cần thiết từ Dockerfile trong repository trước khi
chọn **Dev Containers: Reopen in Container**:

```powershell
docker build -t usad-dev-container-test:latest -f .devcontainer/Dockerfile .
```

Build dựa trên Node 24 (Debian Trixie), cài Git, Python 3/venv và OpenJDK 21,
đồng thời dùng UID mặc định của user `node` trong base image dưới tên
`developer`. Build có thể tải base image/package nếu chưa có cache. Container
phát triển hiện không nằm trong network Compose
`usad_internal`; không thể phân giải service `mariadb`/`backend` qua DNS Compose
hoặc truy cập MariaDB (không publish port) từ network riêng này. Chưa có cấu
hình nối hai mạng; không tự chạy `docker network connect` trên môi trường
đang hoạt động.

## Database schema

DDL chuẩn được lưu tại [database/usad_schema.sql](database/usad_schema.sql).
File này chưa được Compose/backend áp dụng tự động; API dùng SQLAlchemy và
MariaDB khi được cấu hình. Xem
[docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md) để tra bảng/cột và
[docs/POWERDESIGNER_GUIDE.md](docs/POWERDESIGNER_GUIDE.md) để dựng PDM. Chỉ chạy
thử thủ công trên MySQL local dev riêng sau khi xác nhận đúng database đích;
không dùng VPS hoặc production.

## Kiểm thử policy helper

```powershell
$env:JWT_SECRET = [guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")
.\.venv\Scripts\python.exe -m unittest backend.tests.test_api local_agent.tests.test_sandbox_policy
```

Các test này kiểm tra API contract và validator/interface, **không** chứng minh
runtime isolation. Không thực thi code không tin cậy trên host và không kết
nối/triển khai lên VPS từ bản hiện tại. Xem [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md)
để biết khảo sát kiến trúc, phân công module và checklist thành viên mới.
