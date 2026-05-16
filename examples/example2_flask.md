# Example 2 — pallets/flask

Use this example to test all 4 stages of ContribFlow.

## Repository URL
```
https://github.com/pallets/flask
```
Paste this into the sidebar before running any stage.

---

## Stage 1 — Gap Finder
No extra input needed. Click **"Analyze Repository"**.

---

## Stage 2 — Idea Deduplication
```
Add rate limiting middleware to protect Flask routes from abuse
```
Expected result: **CLEAR** — this is a novel idea with no direct conflicts.

---

## Stage 3 — Change Impact Analysis
```
Modify the request context to add support for async middleware
```
Expected result: list of affected files related to request context and routing.

---

## Stage 4 — Pre-PR Quality Check

Paste the diff below:
```diff
diff --git a/src/flask/app.py b/src/flask/app.py
index 1234567..abcdefg 100644
--- a/src/flask/app.py
+++ b/src/flask/app.py
@@ -50,6 +50,12 @@ class Flask:
     def run(self, host=None, port=None, debug=None, **options):
+        import sys
+        print("Starting Flask app...")
+        try:
+            self._run_internal(host, port)
+        except:
+            pass
```
Expected result: **FAILED** — catches bare `except`, `print()` statement, and inline `import`.
