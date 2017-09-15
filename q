[1mdiff --git a/assessment/settings.py b/assessment/settings.py[m
[1mindex d4cb2a6..0faf33b 100644[m
[1m--- a/assessment/settings.py[m
[1m+++ b/assessment/settings.py[m
[36m@@ -44,9 +44,11 @@[m [mINSTALLED_APPS = [[m
 	#third party[m
 	"django_spaghetti",[m
 	"bootstrap3",[m
[32m+[m	[32m'corsheaders',[m
 ][m
 [m
 MIDDLEWARE = [[m
[32m+[m	[32m'corsheaders.middleware.CorsMiddleware',[m
     'django.middleware.security.SecurityMiddleware',[m
     'django.contrib.sessions.middleware.SessionMiddleware',[m
     'django.middleware.common.CommonMiddleware',[m
[36m@@ -139,4 +141,11 @@[m [mBOOTSTRAP3 = {[m
 	}[m
 [m
 STATIC_PATH=os.path.join(BASE_DIR,'static')[m
[31m-STATICFILES_DIRS=[STATIC_PATH,][m
\ No newline at end of file[m
[32m+[m[32mSTATICFILES_DIRS=[STATIC_PATH,][m
[32m+[m
[32m+[m[32m# CORS_ORIGIN_WHITELIST = ([m
[32m+[m[32m    # 'localhost:8000',[m
[32m+[m[32m    # '127.0.0.1:8000',[m
[32m+[m	[32m# '10.115.70.93:8000',[m
[32m+[m[32m# )[m
[32m+[m[32mCORS_ORIGIN_ALLOW_ALL=True[m
\ No newline at end of file[m
