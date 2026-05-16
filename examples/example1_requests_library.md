# Example 1 — psf/requests

Use this example to test all 4 stages of ContribFlow.

## Repository URL
```
https://github.com/psf/requests
```
Paste this into the sidebar before running any stage.

---

## Stage 1 — Gap Finder
No extra input needed. Click **"Analyze Repository"**.

---

## Stage 2 — Idea Deduplication
```
Add retry logic with exponential backoff for failed HTTP requests
```
Expected result: **CONFLICT** or **COMPLEMENTARY** — retry logic already exists in discussions/issues.

---

## Stage 3 — Change Impact Analysis
```
Refactor the authentication module to support OAuth2 token refresh
```
Expected result: list of affected files related to auth and session handling.

---

## Stage 4 — Pre-PR Quality Check

Paste the diff below:
```diff
diff --git a/requests/adapters.py b/requests/adapters.py
index 1234567..abcdefg 100644
--- a/requests/adapters.py
+++ b/requests/adapters.py
@@ -100,6 +100,10 @@ class HTTPAdapter(BaseAdapter):
     def send(self, request, **kwargs):
+        import os
+        print("sending request")
         try:
             conn = self.get_connection(request.url, proxies)
+        except:
+            pass
```
Expected result: **FAILED** — catches bare `except`, `print()` statement, and inline `import`.
