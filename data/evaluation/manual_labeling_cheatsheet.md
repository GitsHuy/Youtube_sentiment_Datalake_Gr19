# Cheat Sheet Gan Nhan Sentiment Thu Cong

Tai lieu nay dung de ho tro gan nhan tay cho file:

- `data/evaluation/manual_labels_100.csv`

Muc tieu:

- gan nhan nhanh
- gan nhan nhat quan
- giam viec phai suy nghi lai tu dau cho tung comment

## 1. Nguyen tac cot loi

Gan nhan theo **cam xuc be mat cua chinh comment**, khong gan theo:

- muc do lien quan den video
- muc do dung/sai cua noi dung
- du doan model se tra ve gi

Noi ngan gon:

- co khen, ung ho, hao hung -> `positive`
- co che, buc, that vong, tan cong -> `negative`
- khong ro cam xuc, chi hoi/quan sat/goi ten -> `neutral`

## 2. Quy tac nhanh

### Positive

Thuong la:

- khen
- yeu thich
- ung ho
- phan khich
- vui, hao hung

Vi du:

- `phenomenal`
- `awesome`
- `I love this`
- `W`
- `GOAT`
- `fire`
- `MrBeast ❤️`

### Negative

Thuong la:

- che bai
- buc tuc
- that vong
- buon
- ghet
- cong kich

Vi du:

- `I hate speed`
- `boring`
- `L`
- `trash`
- `Cancel Raikai`
- `Today is my birthday but 0 like 😢`

### Neutral

Thuong la:

- goi ten
- hoi thong tin
- nhan xet khong lo cam xuc ro
- spam/ngoai le/mo ho

Vi du:

- `MrBeast`
- `xqc`
- `Who is your favorite streamer?`
- `5:00 how much is that lambo?`
- `Early`

### Ghi chu bo sung cho greeting

Voi bo nhan tay hien tai cua du an:

- loi chao ngan nhu `Hi`, `HI MRBeast`, `HI BRO`
- duoc xem la `positive` neu mang sac thai than thien, huong ve creator

Chi gan `neutral` khi:

- chi la goi ten tron
- hoac noi dung qua mo ho, khong the hien thien cam ro

## 3. Cach xu ly slang / Gen Z

Mac dinh de nghi:

- `W` -> `positive`
- `L` -> `negative`
- `GOAT` -> `positive`
- `mid` -> `negative`
- `trash` -> `negative`
- `fire` -> `positive`

Nhung tu can can nhac theo ngu canh:

- `OMG`
- `no way`
- `crazy`
- `bro`
- `nah`

Goi y:

- neu chi the hien ngac nhien, chua ro thich hay ghe -> `neutral`
- neu la ngac nhien theo huong hao hung -> `positive`
- neu la than van/soc xau/khong chiu -> `negative`

## 4. Cach xu ly emoji

Thuong nghieng `positive`:

- ❤️
- 🔥
- 🎉
- 😍
- 😂
- 🙂

Thuong nghieng `negative`:

- 😭
- 😢
- 💔
- 😡
- 😤

Thuong nghieng `neutral`:

- 😮
- 😳
- 🤔
- 😐

Neu comment chi co emoji:

- nhin theo cam xuc chi phoi
- neu van qua mo ho thi gan `neutral`

## 5. Comment khong lien quan video thi sao?

Khong lien quan video **khong co nghia la neutral**.

Vi du:

- `I love u` -> `positive`
- `I hate speed` -> `negative`
- `MrBeast` -> `neutral`

Nho quy tac:

- relevance voi video != sentiment

## 6. Comment la cau hoi thi sao?

Mac dinh:

- cau hoi thong tin -> `neutral`

Chi doi nhan neu cau hoi co cam xuc ro:

- that vong -> `negative`
- hao hung, thien cam -> `positive`

Vi du:

- `Who is your favorite streamer?` -> `neutral`
- `Is he in the video 😢` -> thuong `negative`

## 7. Comment xin qua, xin tham gia, ke hoan canh

Goi y:

- chi xin thong thuong, khong co cam xuc ro -> `neutral`
- xin xo kem khoc loc, tuyet vong, than tho -> `negative`
- xin xo kem nguong mo, hao hung ro -> co the `positive`, nhung can than trong

Vi du:

- `I want to come your video` -> `neutral`
- `Please give me a gaming PC 😭` -> thuong `negative`

## 8. Comment qua ngan

Van gan nhan binh thuong:

- `W` -> `positive`
- `L` -> `negative`
- `Hi` -> `neutral`
- `Awesome` -> `positive`
- `Trash` -> `negative`
- `Early` -> `neutral`

Khong vi comment ngan ma mac dinh la neutral.

## 9. Nhieu ngon ngu hoac khong hieu ro

Neu van nhin ra cam xuc ro:

- cu gan theo cam xuc do

Neu that su khong chac:

- gan `neutral`
- ghi ly do vao `reviewer_notes`, vi du:
  - `unclear foreign language`
  - `possible sarcasm`
  - `emoji only`

## 10. Khi phan van

Neu dung giua `neutral` va `positive/negative` ma khong chac:

- uu tien `neutral`

Ly do:

- bo nhan se it noise hon
- de nhat quan hon

## 11. Mau reviewer_notes nen dung

Anh co the ghi ngan gon theo cac mau sau:

- `gen z praise`
- `gen z disapproval`
- `question`
- `greeting`
- `emoji only`
- `unclear foreign language`
- `request with sadness`
- `possible sarcasm`
- `name only`
- `supportive`

## 12. Ba quy tac chot de nho

1. Goi ten / hoi thong tin -> `neutral`; greeting than thien huong ve creator -> `positive`
2. Khen / yeu thich / hao hung ro -> `positive`
3. Che / ghe / buon / buc / tan cong ro -> `negative`
