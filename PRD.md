# Product Requirements Document (PRD): `gmail-calendar` MCP Server

## 1. סקירת הפרויקט (Project Overview)

פרויקט `gmail-calendar` הוא שרת **Model Context Protocol (MCP)** מקומי הכתוב ב-Python ומורץ באמצעות `uv` מעל **stdio transport**. השרת מבוסס על ה-SDK הרשמי של MCP (`FastMCP` מתוך `mcp>=1.2,<2`) ומחבר סוכן AI לשירותי **Gmail API v1** ו-**Google Calendar API v3** של המשתמש.

השרת תוכנן מתוך עקרון **least privilege** ושליטת משתמש: הוא מאפשר חיפוש וקריאת מיילים, יצירת טיוטות מייל בלבד (`draft`), צפייה באירועי יומן, איתור חלונות זמן פנויים וקביעת אירועים באזור הזמן `Asia/Jerusalem` — **ללא כל יכולת לשלוח מיילים או למחוק פריטים**.

---

## 2. מטרות הפרויקט (Project Objectives)

- לאפשר לסוכן AI לתקשר עם חשבון Gmail ו-Google Calendar של המשתמש דרך ממשק כלים אחיד וסטנדרטי (`MCP`).
- להפריד בין שלב האימות האינטראקטיבי מול Google (`auth.py`) לבין הרצת השרת השוטפת (`server.py` / `gmail-calendar`), כך שהשרת לעולם אינו פותח דפדפן.
- לשמור על בטיחות תפעולית מלאה באמצעות חשיפת פעולות קריאה, יצירת טיוטות ויצירת אירועים בלבד, ללא פעולות שליחה או מחיקה.
- להבטיח בידוד מלא של סודות ומפתחות (`client_secret*.json`, `token.json`) מחוץ לתיקיית הקוד ומהיסטוריית ה-Git.
- לשמור על קוד מודולרי וקריא (כל קובץ Python מתחת ל-150 שורות) עם ניהול תלויות מבוסס `uv`.

---

## 3. הגדרת הבעיה (Problem Statement)

ביישומי אוטומציה מסורתיים (כגון סקריפטים ייעודיים בשיעור L05), כל זרימת עבודה דורשת כתיבה ותחזוקה של קוד ייעודי וקשיח מראש. לעומת זאת, סוכן AI המסוגל לבחור כלים באופן דינמי זקוק לשכבת תיווך אמינה ובטוחה מול שירותי Google האישיים של המשתמש.

חיבור ישיר וללא מגבלות של סוכן לחשבון מייל ויומן עלול לגרום לפעולות בלתי הפיכות (כגון שליחת מייל שגוי או מחיקת פגישה) או לדליפת הרשאות (`credentials` / `tokens`) לתוך קוד המקור. הפרויקט פותר זאת באמצעות שרת `MCP` ממוקד, מוגבל בהרשאות כלים, המשתמש במשתנה סביבה ייעודי (`GOOGLE_PRIVATE_DIR`) לאחסון פרטי של ה-tokens.

---

## 4. דרישות פונקציונליות (Functional Requirements)

1. **אימות מוקדם (`auth.py`):**
   - איתור קובץ `client_secret*.json` יחיד בתוך `~/my-private` (יצירת התיקייה בהרשאות `0700` במידת הצורך).
   - הרצת `InstalledAppFlow.run_local_server(port=0)` בדפדפן עבור ה-scopes הנדרשים ושמירת `token.json` ב-`~/my-private` בהרשאות `0600`.
   - רענון אוטומטי של token שפג תוקפו כאשר קיים `refresh_token`.
2. **הרצת שרת MCP (`src/l06/server.py`, `server.py`):**
   - יצירת שרת בשם `"gmail-calendar"` עם `FastMCP("gmail-calendar")`.
   - הרצה באמצעות `mcp.run(transport="stdio")` דרך `uv run gmail-calendar` או `uv run server.py`.
3. **חשיפת ששת כלי ה-MCP בלבד:**
   - חיפוש הודעות Gmail וקריאת הודעה לפי מזהה.
   - יצירת טיוטת מייל (`draft`) בלבד, ללא שליחה.
   - הצגת אירועים קרובים ביומן הראשי, איתור חלונות זמן פנויים בתאריך נתון וקביעת אירוע חדש באזור הזמן `Asia/Jerusalem`.
4. **מגבלת אי-מחיקה ואי-שליחה:**
   - לא ייחשף אף כלי השולח אימייל או מוחק אימייל/טיוטה/אירוע.

---

## 5. דרישות לא-פונקציונליות (Non-Functional Requirements)

- **סביבת ריצה וניהול חבילות:** Python `>=3.15` מנוהל באמצעות `uv` (`pyproject.toml` ו-`uv.lock`).
- **תחזוקתיות ומודולריות:** כל קובץ Python בפרויקט חייב להישמר מתחת ל-150 שורות קוד (`auth.py`, `server.py`, `test_server.py`, וקבצי החבילה תחת `src/l06/`).
- **אזור זמן אחיד:** כל חישובי התאריכים והשעות בכלי היומן יתבצעו באזור הזמן `Asia/Jerusalem` באמצעות `zoneinfo.ZoneInfo("Asia/Jerusalem")`.
- **הגנת עומס וקלטים (Input Bounds):**
  - `search_emails`: הגבלת `max_results` לטווח `1–50` (ברירת מחדל `10`).
  - `list_events`: הגבלת `days_ahead` לטווח `1–90` (ברירת מחדל `7`).
  - `find_free_slots`: דרישת `duration_minutes > 0` (ברירת מחדל `30`) ופורמט תאריך `YYYY-MM-DD`.
  - `create_event`: וידוא ש-`end` מאוחר מ-`start` (`end_dt > start_dt`).
- **אין אינטראקציית דפדפן מהשרת:** השרת לעולם אינו פותח חלון דפדפן; אם `token.json` חסר או לא תקין ללא `refresh_token`, השרת מחזיר שגיאה ברורה המפנה להרצת `auth.py`.

---

## 6. ששת כלי ה-MCP (The Six MCP Tools)

| # | שם הכלי (`Tool`) | פרמטרים וברירות מחדל | תיאור והתנהגות בפועל |
| - | ----------------- | --------------------- | --------------------- |
| 1 | `search_emails` | `query: str`, `max_results: int = 10` | מחפש הודעות ב-Gmail לפי שאילתת חיפוש (`q=query`), מגביל ל-`1..50` תוצאות, ומחזיר רשימה של `{id, thread_id, subject, from, date, snippet}`. |
| 2 | `read_email` | `message_id: str` | שולף הודעה מלאה לפי `message_id`, מפענח כותרות (`subject`, `from`, `to`, `date`) ומחלץ את גוף ההודעה מעץ ה-MIME (העדפה ל-`text/plain` עם fallback ל-`text/html` בקידוד `base64url`). |
| 3 | `create_draft` | `to: str`, `subject: str`, `body: str` | בונה `EmailMessage`, מקודד ל-`base64url` ויוצר טיוטה ב-Gmail בלבד. מחזיר `{draft_id, message_id, to, subject, status: "draft_created"}`. **אינו שולח את ההודעה.** |
| 4 | `list_events` | `days_ahead: int = 7` | מציג אירועים מן היומן הראשי (`primary`) מהרגע הנוכחי ועד `days_ahead` ימים קדימה (בטווח `1..90`), ממוינים לפי זמן התחלה באזור הזמן `Asia/Jerusalem`. מחזיר `{id, summary, start, end, location, description, status}`. |
| 5 | `find_free_slots` | `date: str`, `duration_minutes: int = 30` | מחפש חלונות זמן פנויים בתאריך `YYYY-MM-DD` בין השעות `08:00` ל-`20:00` (`Asia/Jerusalem`), מאחד חפיפות בין מרווחי `busy` ומחזיר מרווחים פנויים שאורכם לפחות `duration_minutes` בפורמט `{start, end, duration_minutes}`. |
| 6 | `create_event` | `title: str`, `start: str`, `end: str`, `description: str = ""` | מפרסר `start` ו-`end` בפורמט ISO-8601, מנרמל ל-`Asia/Jerusalem`, יוצר אירוע ביומן הראשי ומחזיר `{id, title, start, end, html_link, status}`. |

---

## 7. ארכיטקטורה טכנית (Technical Architecture)

### מבנה הקבצים בפרויקט

```text
L06/
├── pyproject.toml            # הגדרת הפרויקט, תלויות ו-entry points (gmail-calendar, l06)
├── uv.lock                   # נעילת גרסאות דטרמיניסטית עבור uv
├── .python-version           # גרסת Python של הפרויקט
├── .gitignore                # החרגת סודות, .venv וקובץ קונפיגורציה מקומי
├── auth.py                   # סקריפט אימות אינטראקטיבי חד-פעמי ליצירת token.json
├── server.py                 # קובץ הרצה בשורש הפרויקט (uv run server.py)
├── test_server.py            # בדיקת עשן (smoke test) מקצה לקצה מול stdio
├── README.md                 # תיעוד הרצה, תצורה וכלים
├── reflection.md             # רפלקציה על התהליך והפער מול L05
└── src/l06/
    ├── __init__.py           # חשיפת נקודת הכניסה main
    ├── google_client.py      # קריאת GOOGLE_PRIVATE_DIR, טעינת/רענון token ובניית שירותי API
    ├── gmail_tools.py        # לוגיקת חיפוש, קריאה ויצירת טיוטה ב-Gmail
    ├── calendar_tools.py     # לוגיקת רשימת אירועים, חישוב חלונות פנויים ויצירת אירוע
    └── server.py             # הגדרת FastMCP("gmail-calendar") ורישום 6 הכלים על stdio
```

### זרימת הבקשות (Request Flow)

1. לקוח MCP (כגון Antigravity דרך `.agents/mcp_config.json` או `test_server.py`) מפעיל תהליך משנה (`subprocess`) עם הפקודה `uv run server.py` או `uv run gmail-calendar` ומזריק את `GOOGLE_PRIVATE_DIR`.
2. `src/l06/server.py` מאתחל את `FastMCP("gmail-calendar")` ומאזין לבקשות JSON-RPC על גבי `stdin`/`stdout` (`stdio`).
3. בכל קריאת כלי, השרת מעביר את הבקשה למודול המתאים (`gmail_tools.py` או `calendar_tools.py`).
4. המודול פונה ל-`google_client.py`, הטוען את `token.json` מ-`GOOGLE_PRIVATE_DIR`, מרענן את ה-access token במקרה הצורך ושומר מחדש בהרשאות `0600`, ובונה לקוח Google API (`cache_discovery=False`).
5. התוצאה מוחזרת ללקוח ה-MCP במבנה JSON מובנה.

---

## 8. אינטגרציה עם Google API (Google API Integration)

- **ספריות:** `google-api-python-client>=2.202.0`, `google-auth-oauthlib>=1.5.0`.
- **OAuth 2.0 Scopes:**
  - `https://www.googleapis.com/auth/gmail.modify`
  - `https://www.googleapis.com/auth/calendar`
- **קריאות API בשימוש בפועל:**
  - **Gmail API (`v1`):**
    - `users().messages().list(userId="me", q=query, maxResults=limit)`
    - `users().messages().get(userId="me", id=..., format="metadata", metadataHeaders=["Subject", "From", "Date"])`
    - `users().messages().get(userId="me", id=message_id, format="full")`
    - `users().drafts().create(userId="me", body={"message": {"raw": raw}})`
  - **Google Calendar API (`v3`):**
    - `events().list(calendarId="primary", timeMin=..., timeMax=..., singleEvents=True, orderBy="startTime", timeZone="Asia/Jerusalem")`
    - `freebusy().query(body={"timeMin": ..., "timeMax": ..., "timeZone": "Asia/Jerusalem", "items": [{"id": "primary"}]})`
    - `events().insert(calendarId="primary", body=...)`
- **תלות חיצונית מאוחסנת מחוץ לריפו:** קובץ ה-OAuth Client (`client_secret*.json`) ו-`token.json` נשמרים בתיקייה הפרטית המוגדרת ב-`GOOGLE_PRIVATE_DIR`.

---

## 9. דרישות אבטחה ופרטיות (Security and Privacy Requirements)

- **בידוד סודות מלא:** התיקייה והקבצים הרגישים (`client_secret*.json`, `token.json`) לעולם אינם מועתקים לתוך תיקיית הפרויקט; הנתיב אליהם נקרא ממשתנה הסביבה `GOOGLE_PRIVATE_DIR` (עם ברירת מחדל `~/my-private`).
- **הרשאות מערכת קבצים:** התיקייה הפרטית נשמרת בהרשאות `0700` וקובץ `token.json` נשמר ונכתב מחדש בהרשאות `0600` בלבד.
- **מניעת הדלפת סודות בלוגים וב-stdout:** הקוד אינו מדפיס `client_secret`, `access_token`, `refresh_token` או תוכן של קובצי סוד.
- **החרגה מבקרת גרסאות (`.gitignore`):** קובצי `token.json`, `client_secret*.json`, `credentials.json`, `.env`, `.env.*` ו-`.agents/mcp_config.json` מוחרגים מ-Git.
- **ללא מידע אישי בקוד הציבורי:** נתיבים מוחלטים וכתובות דוא"ל אישיות אינם מופיעים בקבצי הקוד, ב-`README.md` או בהיסטוריית ה-commit הציבורית (שימוש ב-GitHub noreply email).
- **מניעת פעולות הרסניות או חיצוניות:** אין מימוש או חשיפה של `messages().send`, `drafts().send`, `messages().delete`, `messages().trash` או `events().delete`.

---

## 10. קריטריוני קבלה (Acceptance Criteria)

- [x] השרת עולה בהצלחה מעל `stdio` באמצעות `uv run gmail-calendar` ו-`uv run server.py` ומזדהה בשם `"gmail-calendar"`.
- [x] `list_tools()` מחזיר בדיוק 6 כלים: `search_emails`, `read_email`, `create_draft`, `list_events`, `find_free_slots`, `create_event`.
- [x] לא קיים אף כלי לשליחת מייל או למחיקת מייל/אירוע, ובקשות לבצע שליחה או מחיקה נדחות על ידי הסוכן.
- [x] `GOOGLE_PRIVATE_DIR` מכוון לתיקייה חיצונית המכילה את `token.json`, והשרת מרענן token בלי לפתוח דפדפן.
- [x] כל כלי היומן פועלים באזור הזמן `Asia/Jerusalem` (כולל קיזוז `busy` בחלון `08:00–20:00` ב-`find_free_slots`).
- [x] כל קובץ Python בפרויקט מכיל פחות מ-150 שורות קוד.
- [x] `.gitignore` חוסם סודות וקובצי קונפיגורציה מקומיים, ובהיסטוריית Git אין סודות, tokens או נתיבים/מיילים אישיים.

---

## 11. בדיקות ומדדי הצלחה (Testing and Success Metrics)

### אופן הבדיקה שבוצע בפועל
1. **בדיקת עשן אוטומטית (`test_server.py`):**
   - הרצה באמצעות `uv run test_server.py` עם `GOOGLE_PRIVATE_DIR` המצביע לתיקייה הפרטית.
   - אימות אתחול חיבור `ClientSession` מול `stdio_client`, בדיקת שם השרת (`gmail-calendar`), אימות רשימת 6 הכלים וקריאה חיה ל-`list_events(days_ahead=1)`.
2. **בדיקות אינטגרציה מול סוכן Antigravity דרך `.agents/mcp_config.json`:**
   - אימות קריאת לוח שנה (`list_events`), איתור חלון פנוי (`find_free_slots`), יצירת טיוטה (`create_draft`), ויצירת אירועים (`create_event`).
   - בדיקת עמידות גבולות בטיחות (Negative testing): ניסיון לשלוח טיוטה ולמחוק אירוע הסתיים בסירוב מפורש של הסוכן בשל היעדר הכלים.
3. **בדיקת תאימות ואבטחה של המאגר:**
   - ספירת שורות (`wc -l`) בכל קובצי ה-Python לוודא שכל אחד מתחת ל-150 שורות.
   - סריקת כל קובצי המאגר ואובייקטי ה-Git לוודא אפס ממצאים של סודות, מפתחות, נתיבים אישיים או אימיילים אישיים.

### מדדי הצלחה (Success Metrics)
- **זמינות כלים (Tool Discovery):** 6 מתוך 6 כלים מתגלים ותקינים ב-`ListToolsRequest`.
- **הצלחת קריאות תקינות:** קריאות תקינות (`search_emails`, `list_events`, `find_free_slots`, `create_draft`, `create_event`) מחזירות `isError: False`.
- **עמידה בגבולות בטיחות:** 0 פעולות שליחה (`send`) או מחיקה (`delete`) אפשריות דרך השרת.
- **עמידה במגבלת אורך קבצים:** 100% מקבצי ה-Python בפרויקט מתחת ל-150 שורות.
- **ניקיון היסטוריית Git:** 0 סודות, 0 tokens, ו-0 נתיבים אישיים בכל אובייקטי ה-Git.
