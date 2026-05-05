# 信用卡自動記帳 — 國泰世華 × Notion

自動將國泰世華信用卡消費通知郵件記錄到 Notion 資料庫。每天凌晨兩點透過 GitHub Actions 自動執行。

---

## 運作原理

```
Gmail (IMAP) → 解析郵件 → 分類商店 → 寫入 Notion
```

1. 讀取 Gmail 收件匣中未讀的國泰世華消費通知信
2. 從郵件中抽取：消費日期、商店名稱、金額
3. 根據 `categories.yml` 的關鍵字規則自動分類
4. 寫入 Notion 資料庫（自動防止重複寫入）
5. 將信件標記為已讀，下次不再重複處理

---

## 設定步驟

### 1. 啟用 Gmail IMAP 並建立 App Password

**啟用 IMAP：**
1. 前往 [Gmail 設定](https://mail.google.com) → 右上角齒輪 → 「查看所有設定」
2. 切換到「轉寄和 POP/IMAP」分頁
3. 在「IMAP 存取」區段選擇「啟用 IMAP」→ 儲存變更

**建立 App Password：**
1. 前往 [Google 帳戶安全性設定](https://myaccount.google.com/security)
2. 確認已啟用「兩步驟驗證」
3. 搜尋「應用程式密碼」(App passwords) 並進入
4. 建立新的應用程式密碼，名稱填寫「信用卡記帳」
5. 複製產生的 16 字元密碼（稍後使用）

> ⚠️ App Password 只顯示一次，請立刻複製保存。

---

### 2. 建立 Notion Integration

1. 前往 [Notion Integrations](https://www.notion.so/profile/integrations)
2. 點擊「New integration」
3. 名稱填寫「信用卡記帳」，類型選「Internal」
4. 點擊「Save」後，複製「Internal Integration Secret」（`secret_...` 開頭）

---

### 3. 分享 Notion 頁面給 Integration

1. 在 Notion 中開啟你想放記帳資料庫的頁面
2. 點擊右上角「`•••`」→「Connections」
3. 搜尋「信用卡記帳」並點擊連結

---

### 4. 建立 Notion 資料庫（一次性）

在本機安裝依賴並執行設定腳本：

```bash
pip install -r requirements.txt

NOTION_API_KEY=secret_你的金鑰 \
NOTION_PARENT_PAGE_ID=你的頁面ID \
python setup.py
```

**如何取得頁面 ID：**
開啟 Notion 頁面，網址格式如下：
```
https://www.notion.so/你的工作區/頁面標題-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
最後 32 個英數字元就是頁面 ID。

執行成功後，終端機會印出：
```
Notion database created successfully!
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

Add this as a GitHub Secret named NOTION_DATABASE_ID
```

複製這個 ID。

---

### 5. 建立 GitHub Repository 並設定 Secrets

**建立 repository：**
1. 前往 [github.com/new](https://github.com/new) 建立新的 repository（可設為 Private）
2. 在本機初始化並推送：

```bash
git remote add origin https://github.com/你的帳號/你的repo名稱.git
git push -u origin main
```

**設定 Secrets：**
1. 前往 GitHub repository → Settings → Secrets and variables → Actions
2. 點擊「New repository secret」，依序新增以下四個：

| Secret 名稱 | 說明 | 範例值 |
|---|---|---|
| `GMAIL_ADDRESS` | 你的 Gmail 帳號 | `yourname@gmail.com` |
| `GMAIL_APP_PASSWORD` | 步驟 1 產生的 App Password | `abcd efgh ijkl mnop` |
| `NOTION_API_KEY` | 步驟 2 取得的 Integration Secret | `secret_abc123...` |
| `NOTION_DATABASE_ID` | 步驟 4 取得的資料庫 ID | `xxxxxxxx...` |

---

### 6. 驗證郵件解析（強烈建議）

國泰世華的郵件格式可能因卡種而略有不同，建議在首次啟用前驗證：

1. 將一封實際的國泰世華消費通知信內文複製到 `sample.txt`
2. 執行：

```bash
python -c "from email_parser import parse_transaction; print(parse_transaction(open('sample.txt', encoding='utf-8').read()))"
```

如果輸出類似 `{'date': '2024/01/15', 'merchant': '全聯福利中心', 'amount': 350}` 則代表成功。

若出現 `ValueError`，請編輯 `email_parser.py` 最上方的三個 Pattern 常數，調整正則表達式以符合你實際收到的郵件格式。

---

### 7. 手動觸發測試

1. 前往 GitHub repository → Actions 分頁
2. 點擊左側的「Sync credit card transactions to Notion」
3. 點擊「Run workflow」→「Run workflow」
4. 等待執行完成（綠色勾勾代表成功）
5. 前往 Notion 確認資料庫中是否出現消費紀錄

---

## 自動執行時程

每天台灣時間凌晨 **02:00** 自動執行（UTC 18:00）。

如需修改時程，編輯 `.github/workflows/sync.yml` 中的 `cron` 值：

```yaml
- cron: '0 18 * * *'   # 每天 02:00 台灣時間
```

---

## 自訂消費分類

編輯 `categories.yml`，在對應分類下新增商店關鍵字：

```yaml
餐飲:
  - 麥當勞
  - 你想新增的店名

購物:
  - 蝦皮
  - 另一家店
```

**規則：**
- 比對方式為關鍵字包含於商店名稱中（不區分大小寫）
- 第一個符合的分類優先
- 沒有符合任何關鍵字時，歸類為「其他」

修改後 commit 並 push 即生效，無需重新設定。

---

## Notion 資料庫欄位

| 欄位 | 類型 | 說明 |
|---|---|---|
| 名稱 | 標題 | 商店名稱 |
| 日期 | 日期 | 消費日期 |
| 金額 | 數字 | 消費金額（新台幣）|
| 分類 | 選取 | 自動分類結果 |
| 建立時間 | 建立時間 | 寫入 Notion 的時間 |

---

## 常見問題

**Q: 執行後沒有新增任何記錄？**
→ 確認 Gmail 收件匣中有未讀的國泰世華通知信。腳本只處理「未讀」信件，已讀的會跳過。

**Q: GitHub Actions 顯示失敗？**
→ 點擊失敗的 workflow run 查看 log。常見原因：Secrets 設定錯誤、Gmail IMAP 未啟用、Notion Integration 未分享給目標頁面。

**Q: 解析失敗 (ValueError)？**
→ 國泰世華的郵件格式可能與預設 regex 不符，請依照步驟 6 驗證並調整 `email_parser.py`。

**Q: 想重新掃描舊信件？**
→ 在 Gmail 中將舊的消費通知信標記為「未讀」，下次執行時會重新處理（Notion 端有重複偵測，不會寫入重複資料）。
