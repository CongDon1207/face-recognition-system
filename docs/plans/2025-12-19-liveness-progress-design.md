# Thiet ke thanh tien do liveness (2025-12-19)

## Muc tieu
- Them thanh tien do ngang ben duoi khung camera de nguoi dung biet tien trinh liveness va thoi diem thanh cong.
- Giu nguyen geometric ratio va luong xu ly hien tai.

## Pham vi
- UI Authentication: them progress bar va cap nhat theo so buoc liveness hoan thanh.
- LivenessDetector -> AuthWorker -> AuthView: truyen danh sach challenge da hoan thanh.

## Cach tinh tien do (4 buoc)
- Buoc 1-3: so challenge trong completed_challenges (toi da 3).
- Buoc 4: khi liveness_status == "REAL".
- Progress = round(steps_done / 4 * 100).

## UI/UX
- Thanh progress nam ngay duoi camera panel.
- Mau chunk theo Theme.PRIMARY; nen toi, vien cyan, co hien % nho.
- Reset ve 0 khi stop hoac khong co mat.

## Du lieu va luong xu ly
- LivenessDetector tra ve completed_challenges.
- AuthWorker day completed_challenges vao result.
- AuthViewLogic cap nhat progress bar tu result.

## RUI RO / Ghi chu
- Neu completed_challenges khong phai list -> coi nhu 0.
- Neu status REAL, progress luon 100%.
